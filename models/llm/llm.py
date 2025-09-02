import json
import logging
from collections.abc import Generator
from enum import Enum
from typing import Optional, Union
from urllib.parse import urljoin

import httpx
from dify_plugin import LargeLanguageModel
from dify_plugin.entities import I18nObject
from dify_plugin.entities.model import (
    AIModelEntity,
    FetchFrom,
    ModelType, ParameterRule, ParameterType, ModelPropertyKey,
)
from dify_plugin.entities.model.llm import (
    LLMResult, LLMResultChunk, LLMResultChunkDelta, LLMUsage,
)
from dify_plugin.entities.model.message import (
    PromptMessage,
    PromptMessageTool, AssistantPromptMessage, )
from dify_plugin.entities.provider_config import AppSelectorScope
from dify_plugin.errors.model import (
    CredentialsValidateFailedError, InvokeError, InvokeConnectionError, InvokeBadRequestError,
)
from httpx import HTTPStatusError
from pydantic import BaseModel
from requests import get

logger = logging.getLogger(__name__)


class CredentialParams(BaseModel):
    server_url: str
    token_secret: Optional[str] = None


class LightRAGModeType(Enum):
    LOCAL = 'local'
    GLOBAL = 'global'
    HYBRID = 'hybrid'
    NAIVE = 'naive'
    MIX = "mix"
    BYPASS = 'bypass'


class LightRAGResponseType(Enum):
    MULTI = "Multiple Paragraphs"
    SINGLE = "Single Paragraph"
    BULLET = "Bullet Points"


class LightragLargeLanguageModel(LargeLanguageModel):
    """
    Model class for lightrag large language model.
    """

    @property
    def _invoke_error_mapping(self) -> dict[type[InvokeError], list[type[Exception]]]:
        return {
            InvokeConnectionError: [HTTPStatusError]
        }

    def _invoke(
            self,
            model: str,
            credentials: dict,
            prompt_messages: list[PromptMessage],
            model_parameters: dict,
            tools: Optional[list[PromptMessageTool]] = None,
            stop: Optional[list[str]] = None,
            stream: bool = True,
            user: Optional[str] = None,
    ) -> Union[LLMResult, Generator]:
        """
        Invoke large language model

        :param model: model name
        :param credentials: model credentials
        :param prompt_messages: prompt messages
        :param model_parameters: model parameters
        :param tools: tools for tool calling
        :param stop: stop words
        :param stream: is stream response
        :param user: unique user id
        :return: full response or stream response chunk generator result
        """
        print(f"stream: {stream}")
        if stream:
            return self._handle_stream_response(model, credentials["server_url"], model_parameters, prompt_messages)
        return self._handle_sync_response(model, credentials["server_url"], model_parameters, prompt_messages)

    def _handle_stream_response(self, model: str, server_url: str, model_parameters: dict,
                                prompt_messages: list[PromptMessage]) -> Generator:
        query_path = urljoin(server_url, "/query/stream")
        system_prompt, user_prompt, history_message_conversation = self._resolve_query_messages(prompt_messages)
        if not user_prompt:
            raise InvokeBadRequestError('user query cannot be empty!')
        query_params = {
            "user_prompt": system_prompt,
            "query": user_prompt,
            "history_turns": len(history_message_conversation),
            "conversation_history": history_message_conversation,
            **model_parameters}
        with httpx.stream("POST", query_path, json=query_params) as response:
            response.raise_for_status()
            idx = 0
            for line in response.iter_lines():
                result = json.loads(line)['response']
                yield LLMResultChunk(
                    model=model,
                    prompt_messages=prompt_messages,
                    delta=LLMResultChunkDelta(
                        index=idx + 1,
                        message=AssistantPromptMessage(
                            content=result
                        )
                    )
                )
                idx += 1
            yield LLMResultChunk(
                model=model,
                prompt_messages=prompt_messages,
                delta=LLMResultChunkDelta(
                    index=idx + 1,
                    message=AssistantPromptMessage(
                        content='',
                    ),
                    finish_reason='stop'
                )
            )

    def _handle_sync_response(self, model: str, server_url: str, model_parameters: dict,
                              prompt_messages: list[PromptMessage]) -> LLMResult:
        query_path = urljoin(server_url, "/query")
        system_prompt, user_prompt, history_message_conversation = self._resolve_query_messages(prompt_messages)
        if not user_prompt:
            raise InvokeBadRequestError('user query cannot be empty!')
        query_params = {
            "user_prompt": system_prompt,
            "query": user_prompt,
            "history_turns": len(history_message_conversation),
            "conversation_history": history_message_conversation,
            **model_parameters}
        with httpx.post(query_path, json=query_params) as response:
            response.raise_for_status()
            result = response.json()['response']
            return LLMResult(
                model=model,
                prompt_messages=prompt_messages,
                message=AssistantPromptMessage(
                    content=result
                ),
                usage=LLMUsage.empty_usage()
            )

    def get_num_tokens(
            self,
            model: str,
            credentials: dict,
            prompt_messages: list[PromptMessage],
            tools: Optional[list[PromptMessageTool]] = None,
    ) -> int:
        """
        Get number of tokens for given prompt messages

        :param model: model name
        :param credentials: model credentials
        :param prompt_messages: prompt messages
        :param tools: tools for tool calling
        :return:
        """
        return 0

    def validate_credentials(self, model: str, credentials: dict) -> None:
        """
        Validate model credentials

        :param model: model name
        :param credentials: model credentials
        :return:
        """
        try:
            params = CredentialParams(**credentials)
            version_url = urljoin(params.server_url, "/api/version")
            response = get(url=version_url)
            response.raise_for_status()
            response = response.json()
            logger.info(f"load lightrag success, lightrag version: {response['version']}")
        except Exception as ex:
            raise CredentialsValidateFailedError(str(ex))

    def get_customizable_model_schema(
            self, model: str, credentials: dict
    ) -> AIModelEntity:
        """
        If your model supports fine-tuning, this method returns the schema of the base model
        but renamed to the fine-tuned model name.

        :param model: model name
        :param credentials: credentials

        :return: model schema
        """
        rules = [
            ParameterRule(
                name="mode", type=ParameterType.STRING,
                default=LightRAGModeType.MIX.value,
                required=True,
                options=[mode.value for mode in LightRAGModeType],
                label=I18nObject(
                    en_US="mode for lightrag", zh_Hans="LightRAG模式类型"
                ),
                help=I18nObject(
                    en_US="Local | Focuses on context-dependent information\nGlobal | Utilizes global knowledge\nHybrid | Combines local and global retrieval methods\nNaive | Performs a basic search without advanced techniques\nMix | Integrates knowledge graph and vector retrieval",
                    zh_Hans="Local | 侧重于上下文相关的信息\nGlobal | 利用全数据库知识\nHybrid | 结合了本地和全局检索方法\nNaive | 执行基本检索，不使用高级检索方式\nMix | 融合知识图谱与向量检索"
                )
            ),
            ParameterRule(
                name="only_need_context", type=ParameterType.BOOLEAN,
                default=False,
                required=True,
                label=I18nObject(
                    en_US="whether only returns the retrieved context",
                    zh_Hans="是否只返回召回的上下文",
                ),
                help=I18nObject(
                    en_US="If true, only returns the retrieved context without generating a response",
                    zh_Hans="如果为True，则只会返回召回的上下文，没有模型回复",
                )
            ),
            ParameterRule(
                name="only_need_prompt", type=ParameterType.BOOLEAN,
                default=False,
                required=True,
                label=I18nObject(
                    en_US="whether only returns the generated prompt",
                    zh_Hans="是否只返回生成的prompt",
                ),
                help=I18nObject(
                    en_US="If true, only returns the generated prompt without producing a response",
                    zh_Hans="如果为True，则只会返回生成的prompt，没有模型回复",
                )
            ),
            ParameterRule(
                name="response_type", type=ParameterType.STRING,
                default=LightRAGResponseType.MULTI,
                required=True,
                options=[rep_type.value for rep_type in LightRAGResponseType],
                label=I18nObject(
                    en_US="Response format", zh_Hans="响应格式"
                ),
                help=I18nObject(
                    en_US="Defines the response format",
                    zh_Hans="定义响应的格式"
                )
            ),
            ParameterRule(
                name="top_k", type=ParameterType.INT,
                default=60,
                required=True,
                label=I18nObject(
                    en_US="top_k", zh_Hans="top_k"
                ),
                help=I18nObject(
                    en_US="Number of top items to retrieve. Represents entities in 'local' mode and relationships in 'global' mode.",
                    zh_Hans="要检索的顶级项目数量。在“local”模式下表示实体，在“global”模式下表现为关系"
                )
            ),
            ParameterRule(
                name="chunk_top_k", type=ParameterType.INT,
                default=20,
                required=True,
                label=I18nObject(
                    en_US="chunk_top_k", zh_Hans="chunk_top_k"
                ),
                help=I18nObject(
                    en_US="Number of text chunks to retrieve initially from vector search and keep after reranking.",
                    zh_Hans="从向量搜索中初始检索并保留在重新排列后的文本块数量"
                )
            ),
            ParameterRule(
                name="max_entity_tokens", type=ParameterType.INT,
                default=6000,
                required=True,
                label=I18nObject(
                    en_US="Maximum number of tokens allocated for entity context", zh_Hans="最大实体token数量"
                ),
                help=I18nObject(
                    en_US="Maximum number of tokens allocated for entity context in unified token control system.",
                    zh_Hans="系统控制最大实体token数量"
                )
            ),
            ParameterRule(
                name="max_relation_tokens", type=ParameterType.INT,
                default=8000,
                required=True,
                label=I18nObject(
                    en_US="Maximum number of tokens allocated for relationship context",
                    zh_Hans="关系描述控制最大实体token"
                ),
                help=I18nObject(
                    en_US="Maximum number of tokens allocated for entity context in unified token control system.",
                    zh_Hans="系统控制为关系描述控制最大实体token数量"
                )
            ),
            ParameterRule(
                name="max_total_tokens", type=ParameterType.INT,
                default=30000,
                required=True,
                label=I18nObject(
                    en_US="Maximum number of tokens allocated for relationship context",
                    zh_Hans="最大总tokens"
                ),
                help=I18nObject(
                    en_US="Maximum total tokens budget for the entire query context (entities + relations + chunks + system prompt)",
                    zh_Hans="最大总tokens数量控制(entities + relations + chunks + system prompt)"
                )
            ),
            ParameterRule(
                name="enable_rerank", type=ParameterType.BOOLEAN,
                default=False,
                required=True,
                label=I18nObject(
                    en_US="Whether Enable reranking",
                    zh_Hans="是否启动重排",
                ),
                help=I18nObject(
                    en_US="Enable reranking for retrieved text chunks",
                    zh_Hans="是否启动对召回的context做rerank",
                )
            ),

        ]

        entity = AIModelEntity(
            model=model,
            label=I18nObject(zh_Hans=model, en_US=model),
            model_type=ModelType.LLM,
            features=[],
            fetch_from=FetchFrom.CUSTOMIZABLE_MODEL,
            model_properties={
                ModelPropertyKey.MODE: AppSelectorScope.CHAT
            },
            parameter_rules=rules,
        )

        return entity

    def _resolve_query_messages(self, prompt_messages: list[PromptMessage]):
        # 聊天窗口大于2,实际上是存在历史消息的
        system_prompt = prompt_messages[0].content
        user_prompt = prompt_messages[-1].content
        history_message_conversation = []
        if len(prompt_messages) > 2:
            history_message_conversation = [
                {
                    'role': prompt_message.role.value,
                    'content': prompt_message.content
                } for prompt_message in prompt_messages[1:-1]
            ]
        return system_prompt, user_prompt, history_message_conversation
