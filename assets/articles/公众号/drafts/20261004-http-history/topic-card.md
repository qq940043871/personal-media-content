# 选题卡：HTTP 的前世今生

## 基本信息

- **拟定标题**：HTTP 的前世今生：状态码与请求头一次讲透
- **文章类别**：科技
- **目标读者**：36 岁技术老兵——有多年开发经验，写过接口、调过后端，但没系统梳理过 HTTP 协议的历史与细节
- **调性**：专业、干货、教程式；不说教、不堆术语，每个概念都要落到"它解决什么问题"
- **目标字数**：1800-2500 字（宁精勿长，用表格压缩信息密度）

## 核心问题（读者读完要能回答）

1. HTTP 从 1991 年到现在，经历了 0.9 / 1.0 / 1.1 / 2 / 3 五代，每一代到底解决了上一代的什么痛点？
2. 状态码那一串 2xx / 3xx / 4xx / 5xx，到底是谁定义的、怎么记、每类什么含义？
3. 请求头（Request Headers）和响应头（Response Headers）分别有哪些高频成员，各自在干什么？

## 内容要点

### 第一部分：前世今生（发展史，约占 1/3）

- HTTP/0.9（1991）：只有 GET，只能返回 HTML 文本，没有头部——一个"只能用一次"的极简协议
- HTTP/1.0（1996）：引入请求头/响应头、状态码、Content-Type，但每个请求都要新建一次 TCP 连接（三次握手），慢
- HTTP/1.1（1997）：长连接（keep-alive）、管道化、Host 头（虚拟主机）、分块传输、缓存协商（ETag/If-Modified-Since）——统治至今的版本
- HTTP/2（2015）：二进制分帧、多路复用（解决队头阻塞）、头部压缩（HPACK）、服务端推送
- HTTP/3（2022 标准化）：抛弃 TCP，改用 QUIC（基于 UDP），彻底解决 TCP 层的队头阻塞，0-RTT 握手
- 总结规律：每一代都在解决"更快的连接 + 更小的开销 + 更强的复用"

### 第二部分：状态码（约占 1/3）

- 状态码是服务端给客户端的"一句话回执"，三位数字按首位分类：
  - 1xx 信息：100 Continue、101 Switching Protocols
  - 2xx 成功：200 OK、201 Created、204 No Content（含 206 Partial Content 断点续传）
  - 3xx 重定向：301 永久、302/307 临时、304 Not Modified（缓存命中，不返回 body）、308 永久+保持方法
  - 4xx 客户端错误：400 参数错、401 未认证、403 无权限、404 不存在、405 方法不允许、408 请求超时、409 冲突、429 限流
  - 5xx 服务端错误：500 内部错误、502 网关错误、503 服务不可用、504 网关超时
- 重点讲清易混对：301 vs 302、401 vs 403、502 vs 504、304 为什么没有 body

### 第三部分：请求头与响应头（约占 1/3）

**请求头（客户端 → 服务端）**：
- Host：目标域名（虚拟主机的关键）
- User-Agent：客户端身份（浏览器/爬虫/App 版本）
- Accept / Accept-Encoding / Accept-Language：内容协商，我"能"接受什么
- Content-Type：请求体的格式（application/json 等）
- Content-Length：请求体字节数
- Authorization：认证凭据（Bearer token / Basic）
- Cookie：携带会话状态
- Referer / Origin：来源页与跨域来源
- Cache-Control / If-None-Match / If-Modified-Since：缓存协商
- Range：断点续传/分片下载

**响应头（服务端 → 客户端）**：
- Content-Type：告诉客户端怎么解析响应体
- Content-Length / Transfer-Encoding: chunked：怎么界定 body 边界
- Content-Encoding：gzip/br 压缩
- Set-Cookie：下发会话
- Cache-Control / ETag / Last-Modified / Expires：缓存策略
- Location：配合 3xx 告诉客户端跳去哪
- Access-Control-Allow-Origin：CORS 跨域许可
- Server / Date：服务端信息与响应时间
- WWW-Authenticate：配合 401 指明认证方式
- Retry-After：配合 429/503 告诉客户端多久后重试

### 第四部分：收尾

- 一句话总结：HTTP 的一切设计，都是在"无状态"这个前提下，想办法把状态、缓存、性能、安全这几件事拆开来解决
- 呼应"前世今生"：协议没变的是语义，变的是承载它的传输方式

## 配图要求

- 封面 1 张（放在标题之前）
- 正文按节配图：建议一个"版本演进时间线"信息图、一个"状态码分类"信息图、一个"请求头/响应头对照"信息图
- 配图标记格式：`![类型名：画面描述](placeholder)`，类型名只能用 封面/信息图/氛围/流程图/对比/实证
