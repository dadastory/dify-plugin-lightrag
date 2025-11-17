# lightrag

**作者:** dadastory  
**类型:** 模型

> ⚠️ **提示:** 仅适配Lightrag版本为 **v1.4.9.4**.
> 其他版本可能无法正常工作，如果有问题，请及时联系更新

## 描述

- 这是一个用于 LightRAG 的 LLM 插件。
- 它允许将 LightRAG 挂载为 Dify 中的大语言模型（LLM），从而实现便捷的集成与使用。
- LightRAG 服务器的部署可参考官方文档。

## 功能特性

- 无缝集成 LightRAG 作为 Dify 的 LLM 插件。
- 支持标准 LLM 请求与流式响应。
- 可通过 Dify 插件系统进行简单配置。

## 限制

- **目前不支持 Token 计算。**
- 在使用插件前，请确保 LightRAG 服务器已启动并可访问。

## 安装

1. 将此插件克隆或下载到 Dify 的插件目录下。
2. 根据 LightRAG 的服务器地址与凭据配置插件。
3. 重启 Dify 以加载插件。
4. 安装并启动 lightrag，请参考官方文档 [https://github.com/HKUDS/LightRAG] 

## 配置

- `server_url`: 已运行的 LightRAG 服务器的 HTTP 接口地址（例如 `http://localhost:9621`）。
- `api_key` 或 LightRAG 所需的其他凭据。
- 你可以配置多个不同的 LightRAG 实例，它们彼此相互隔离。

## 使用方法

### 安装

<p align="center">
    <img src="_assets/install.png" alt="安装界面" width="400">
</p>

- 安装完成后，你可以在 Dify 的 LLM 设置中选择 `lightrag` 作为模型。
- 正常发送提示词，请求将会被转发至 LightRAG 服务器。
- 你可以修改请求 lightrag 的模式配置。

### 🔌 LightRAG 与 Dify 集成

<p align="center">
    <img src="_assets/config.png" alt="LLM 配置界面" width="400">
</p>

LightRAG 在接入 **Dify** 时支持三种输出模式：

1. **上下文输出模式（Context Output Mode）**  
   LightRAG 以 **上下文** 的形式返回结果，你可以将其直接替代 Dify 的知识库。  
   该模式适合在下游任务中使用 LightRAG 提供的背景知识。

2. **提示词输出模式（Prompt Output Mode）**  
   LightRAG 会自动生成一段 **system prompt** 并输出。  
   你可以将该提示词接入 Dify 内的其他 LLM 节点进行进一步处理。  
   如果你想自定义 Dify 的链路处理逻辑，该模式非常灵活。

3. **LLM 解析输出模式（LLM Parsing Output Mode）**  
   LightRAG 使用其 **内置的 LLM** 来解析结果，并直接提供 **流式输出**。  
   当你希望获得即时结果而无需额外的 LLM 处理时，该模式最为合适。

---

✨ 通过这三种模式，你可以根据实际需求，选择最合适的方式将 LightRAG 集成到 Dify 工作流中。

# 📝 版本历史

- **v0.0.6**
    - 正式支持api-key配置。

- **v0.0.5**
    - 适配最新的 LightRAG 版本。

- **v0.0.4**
    - 移除了 `print` 配置以避免某些错误。

- **v0.0.3**
    - 添加请求超时配置以防止部分错误。

- **v0.0.2**
    - 修复了默认参数设置错误的问题。

- **v0.0.1**
    - 初始稳定版本，包含核心功能。

