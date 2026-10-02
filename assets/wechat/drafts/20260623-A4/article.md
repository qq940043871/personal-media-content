# KV Cache 原理与优化：PagedAttention、vLLM 的前世今生

> 大模型推理的核心瓶颈不在计算，而在内存。KV Cache 是解码阶段的命脉，而 PagedAttention 彻底改变了我们管理它的范式。

---

## 一、为什么需要 KV Cache

Transformer 的自回归解码本质上是一个 token 一个 token 往外蹦的过程。每生成一个新 token，模型需要对所有之前的 token 做 Attention 计算。如果每次都从头算，时间复杂度会随着序列长度平方级增长——这显然不可接受。

KV Cache 的思路极其朴素：**之前算过的 Key 和 Value 不要丢，缓存起来，下一步直接复用。**

具体来说，在 Multi-Head Attention 中，每个 token 会生成对应的 Q（Query）、K（Key）、V（Value）三个向量。解码第 $n$ 个 token 时，只需要计算当前 token 的 Q，然后让它和缓存中所有 $n-1$ 个 token 的 K、V 做点积。这样每一步的计算量从 $O(n^2 d)$ 降到 $O(nd)$，其中 $d$ 是 head dimension。

这个优化看似简单，却是整个 LLM 推理加速的基石。没有 KV Cache，GPT-4 级别的模型根本无法在合理时间内完成推理。

---

## 二、KV Cache 的内存困境

KV Cache 省了计算，却把压力全甩给了内存。

以 LLaMA-70B 为例：模型有 80 层，每层 64 个 KV head，每个 head 维度 128，使用 FP16 存储。一个 token 的 KV Cache 大小为：

$$80 \times 2 \times 64 \times 128 \times 2\ \text{bytes} = 2.5\ \text{MB/token}$$

听起来不多？一条 4096 长度的序列就要吃掉 **10 GB** 显存。如果同时服务 32 个请求，就是 **320 GB**——直接超出单张 H100 的 80 GB 显存上限。

更糟糕的是，KV Cache 的生命周期是**动态且不可预测**的。用户随时可能发送新消息、结束对话、或者长尾请求突然到来。传统做法是按最大序列长度预分配显存，导致严重的碎片化和浪费——实际利用率往往不到 50%。

这就是 2023 年之前大模型推理的核心矛盾：**计算很闲，内存很忙。**

---

## 三、PagedAttention：操作系统思维的降维打击

2023 年，UC Berkeley 的 vLLM 团队发表了一篇改变游戏规则的论文：*Efficient Memory Management for Large Language Model Serving with PagedAttention*。

核心洞察只有一句话：**操作系统用虚拟内存管理进程内存的那套方法，可以直接搬过来管 KV Cache。**

### 3.1 从连续分配到分页

传统 KV Cache 管理遵循"连续分配"原则：一条序列的 KV Cache 必须占用一块连续的显存区域。这和早期操作系统给进程分配连续物理内存一模一样——问题也一模一样：外部碎片、内部碎片、利用率低下。

PagedAttention 引入了 **Block** 的概念，相当于操作系统的"页"。每个 Block 存储固定数量 token 的 KV Cache（比如 16 个 token）。一条序列的 KV Cache 被拆散到多个 Block 中，这些 Block 在物理显存上不需要连续。

同时维护一个 **Block Table**（页表），记录逻辑 Block 到物理 Block 的映射关系。解码时，Attention Kernel 根据 Block Table 把散布在各处的 KV 数据拼接起来计算。

### 3.2 Copy-on-Write：Beam Search 的救星

Beam Search 是文本生成中常用的策略，会维护多条候选序列。这些序列共享同一个 Prefix，理论上它们的 KV Cache 应该只存一份。

PagedAttention 引入了 **Copy-on-Write**（写时复制）机制：多条序列的 Block Table 可以指向同一个物理 Block，只有当某条序列需要修改某个 Block 的内容时，才真正复制一份。这和操作系统中 fork() 的实现如出一辙。

实测显示，Beam Search 场景下 KV Cache 的内存占用降低了 **55% 以上**。

### 3.3 内存效率的飞跃

PagedAttention 带来的收益是全方位的：

- **消除外部碎片**：Block 大小固定，分配和释放都是整块操作，碎片率接近零。
- **降低内部碎片**：Block 只需在最后一个位置有少量浪费（最后一个 Block 可能没填满）。
- **按需分配**：不需要预分配最大长度，序列生成到哪里，Block 就分配到哪里。
- **动态回收**：序列结束后，Block 立即归还到空闲池，供其他请求使用。

综合下来，KV Cache 的内存利用率从不到 50% 提升到 **>96%**，等效于把显存容量翻了一倍。

---

## 四、vLLM 的前世今生

### 4.1 从论文到工程

vLLM 最初只是 Berkeley RISE Lab 的一个研究项目，目标很简单：验证 PagedAttention 在真实场景下的效果。但当团队发现这个优化能把吞吐量提升 **2-4 倍**时，它迅速演变成一个生产级推理引擎。

vLLM 的架构可以分为三层：

- **调度层**（Scheduler）：负责请求的排队、抢占和调度。当显存不足时，可以将低优先级请求的 KV Cache 换出到 CPU 内存（Swap），等资源充裕时再换入。
- **执行层**（Executor）：管理 GPU Worker，协调模型的前向计算。支持张量并行（Tensor Parallelism）和流水线并行（Pipeline Parallelism）。
- **内核层**（Kernels）：PagedAttention 的 CUDA 实现，针对不同模型架构（LLaMA、Mistral、Qwen 等）做了专门优化。

### 4.2 关键演进

**vLLM v0.1（2023年6月）**：首个开源版本，实现了 PagedAttention 的核心功能。支持 LLaMA、ChatGLM 等少数模型，但已经展现出惊人的吞吐量优势。

**vLLM v0.2-v0.3（2023年下半年）**：引入 Continuous Batching（连续批处理），打破了传统 Static Batching 必须等整个 batch 完成才能处理下一个请求的限制。新请求可以在已有 batch 的任意位置插入，大幅降低了排队延迟。

**vLLM v0.4-v0.5（2024年）**：支持 Prefix Caching——相同系统提示的多个请求可以共享 Prefix 部分的 KV Cache，避免重复计算。同时开始支持多模态模型（如 LLaVA）和 Structured Output（结构化输出）。

**vLLM v0.6+（2024年末至今）**：引入 Chunked Prefill（分块预填充），将长 Prompt 的预填充阶段拆分成多个小块，避免单次计算占用过多显存和计算时间。同时支持 Speculative Decoding（投机解码），用小模型先猜多个 token，再用大模型一次性验证，减少解码步数。

### 4.3 vLLM 的生态位

今天 vLLM 已经成为大模型推理的事实标准之一。它被集成到 Hugging Face TGI、LangChain、OpenAI 兼容 API 等众多框架中。SGLang、TensorRT-LLM 等竞争者也纷纷借鉴了 PagedAttention 的思路。

但 vLLM 并非万能。在极端低延迟场景（如实时对话的第一 token 延迟），TensorRT-LLM 的编译优化往往更胜一筹；在边缘设备上，llama.cpp 的量化方案更加实用。vLLM 的优势在于**高吞吐量的服务场景**——这恰恰是大多数企业部署大模型时的核心需求。

---

## 五、KV Cache 优化的前沿方向

PagedAttention 解决了内存管理问题，但 KV Cache 的优化远未结束。当前的研究热点集中在以下几个方向：

**KV Cache 压缩**：通过量化（将 FP16 压缩到 INT4/INT8）、稀疏化（只保留重要 token 的 KV）、或者低秩分解来减小 KV Cache 的体积。GQA（Grouped Query Attention）和 MQA（Multi-Query Attention）从模型架构层面减少了 KV head 的数量，是更根本的压缩手段。

**KV Cache 驱逐**：当序列过长、显存不够时，需要决定丢弃哪些 token 的 KV Cache。H2O（Heavy-Hitter Oracle）等方法通过 Attention Score 识别"重要"token，优先保留它们。

**分布式 KV Cache**：在多机多卡场景下，KV Cache 可以分散存储在不同 GPU 上，通过高速互联（NVLink、InfiniBand）按需传输。这为超长上下文（100K+ token）的推理提供了可能。

**KV Cache 复用**：除了 Prefix Caching，更激进的方案是将 KV Cache 持久化到磁盘或分布式存储中，实现跨请求、跨会话的复用。这对 RAG（检索增强生成）场景尤其有价值。

---

## 六、写在最后

KV Cache 的故事，本质上是一个**资源管理**的故事。从最朴素的缓存复用，到操作系统级别的分页管理，再到分布式系统级别的调度和压缩——每一步优化都在回答同一个问题：如何在有限的硬件上榨取最大的推理性能。

PagedAttention 的启示不仅在于技术本身，更在于方法论：**跨领域的思维迁移往往能带来突破性创新**。谁会想到，操作系统的虚拟内存管理技术，能成为大模型推理的核心基础设施？

对于工程团队来说，理解 KV Cache 的底层机制，不是学术兴趣，而是生产必需。它决定了你的推理服务能扛多少并发、延迟能做到多低、成本能压到多省。在这个大模型落地的关键时期，这些数字就是竞争力。

---

*参考资料：Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention", SOSP 2023*
