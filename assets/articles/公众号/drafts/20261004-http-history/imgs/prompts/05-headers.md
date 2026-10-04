---
size: "2730x1536"
quality: standard
---

一张左右对照的信息图，展示 HTTP 请求头与响应头的高频成员。

布局：左右两栏，中间一条竖直分隔线。

左栏标题：请求头（客户端 → 服务端）
左栏逐行列出，每行只写英文 Header 名，不加中文前缀，不要重复，不要拼错：
Host
User-Agent
Accept
Content-Type
Authorization
Cookie
Referer
Origin
Cache-Control
Range

右栏标题：响应头（服务端 → 客户端）
右栏逐行列出，每行只写英文 Header 名，不加中文前缀，不要重复，不要拼错：
Content-Type
Content-Length
Set-Cookie
ETag
Location
Cache-Control
Access-Control-Allow-Origin
WWW-Authenticate
Retry-After
Server

视觉：左栏条目用青蓝色，右栏条目用深墨蓝色；两栏之间有一个由左指向右的箭头。

要求：
- 纯白色背景，两栏留白充足。
- 每个 Header 名只出现一次，不得重复、不得增改拼写。
- 画面中除上述指定文字外，不得出现任何其他文字、颜色代码或色号、水印或 logo。
