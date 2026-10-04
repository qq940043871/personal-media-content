---
size: "2730x1536"
quality: standard
---

一张从左到右的流程图，展示浏览器跨域请求的预检流程。纯白色背景。

四个圆角矩形节点，依次为（节点内文字必须准确）：
1. 浏览器：准备发送跨域请求
2. 预检 OPTIONS：先发一个 OPTIONS 请求询问服务端
3. 服务端校验：返回 Access-Control-Allow-Origin、Access-Control-Allow-Methods
4. 发出真实请求：预检通过后，浏览器才发送真正的 GET 或 POST

连接：节点之间用清晰箭头连接；第 2 个与第 3 个节点之间为双向箭头表示问答。
高亮：第 3 个节点用明亮的青蓝色边框突出。
额外标注：一条橙红色虚线从右侧节点上方绕回，标注文字「无许可则拦截」。

要求：
- 纯白色背景，不要深色背景、不要岩石或纹理背景。
- 画面中除上述指定中文文案以及 OPTIONS、GET、POST、Access-Control-Allow-Origin、Access-Control-Allow-Methods 外，不得出现任何其他文字、字母、数字、颜色代码或色号（例如以井号开头的十六进制颜色值）、图例、水印或 logo。
