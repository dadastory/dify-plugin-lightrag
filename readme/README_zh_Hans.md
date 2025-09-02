## lightrag

**作者:** dadastory  
**版本:** 0.0.1  
**类型:** 模型  

### 描述

- 这是一个 LightRAG 的 LLM 插件。  
- 它允许将 LightRAG 挂载为 Dify 的大模型（LLM），实现方便的集成和使用。  
- LightRAG 服务器的部署可以参考官方文档。  

### 功能

- 无缝将 LightRAG 集成为 Dify 的 LLM 插件。  
- 支持标准 LLM 请求和流式响应。  
- 可通过 Dify 插件系统进行简单配置。  

### 限制

- **当前不支持 Token 计算。**  
- 使用插件前，请确保 LightRAG 服务器已启动并可访问。  

### 安装

1. 将该插件克隆或下载到 Dify 的插件目录中。  
2. 根据 LightRAG 服务器地址和凭证配置插件。  
3. 重启 Dify 以加载插件。  

### 使用方法

- 安装完成后，可以在 Dify 的 LLM 设置中选择 `lightrag` 作为模型。  
- 正常发送提示，插件会将请求转发到 LightRAG 服务器。  

### 配置

- `server_url`：运行中的 LightRAG 服务器的 HTTP 端点（例如 `http://localhost:9621`）。  
- `api_key` 或其他 LightRAG 所需的凭证（**但是当前 lightrag 不支持这些参数，因此暂时无法使用**）。  
