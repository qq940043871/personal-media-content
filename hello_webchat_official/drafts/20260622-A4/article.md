---
title: "KV Cache 原理与优化：PagedAttention、vLLM 的前世今生"
author: haswhere
category: 科技
date: 2026-06-22
tags: [LLM, KV Cache, PagedAttention, vLLM, 推理优化]
---

# KV Cache 原理与优化：PagedAttention、vLLM 的前世今生

## 为什么 KV Cache 是 LLM 推理的命门

当你用 ChatGPT 对话时，模型并不是每次都从头计算整个序列。它会复用之前已经算好的 Key 和 Value 向量，这就是 **KV Cache**。没有它，生成一个 1000 token 的回复，计算量会从 O(n) 暴涨到 O(n²)。

但 KV Cache 本身也是一把双刃剑——它用空间换时间，却在高并发场景下成为显存瓶颈。一个 70B 参数的模型，单条请求的 KV Cache 就可能吃掉数 GB 显存。当数百个请求同时涌入，显存立刻告急。

这篇文章，我们从原理出发，拆解 KV Cache 的本质问题，然后看 PagedAttention 和 vLLM 如何一步步解决它。

---

## 一、KV Cache 的工作原理

### 1.1 自回归生成的本质

Transformer 的自回归生成是逐 token 进行的。生成第 n 个 token 时，需要计算当前 token 的 Query 与**所有**前序 token 的 Key 做点积，再与对应的 Value 加权求和。

如果每次生成都重新计算所有 token 的 K 和 V，复杂度是灾难性的。于是我们缓存它们——每生成一个新 token，就把它的 K、V 向量存下来，下次直接读取。

```
生成 token_t 时：
  Q = W_q · x_t                    # 只算当前 token 的 Q
  K = concat(K_cache, W_k · x_t)   # 拼接缓存的 K
  V = concat(V_cache, W_v · x_t)   # 拼接缓存的 V
  output = softmax(Q · K^T) · V
```

### 1.2 显存消耗有多大

以 LLaMA-70B 为例：
- 每层 128 个头（GQA），每个头维度 128
- 80 层 Transformer
- FP16 精度，每个元素 2 字节
- 单个 token 的 KV Cache ≈ **2 × 80 × 128 × 128 × 2 bytes ≈ 5 MB**

一条 4096 token 的请求，KV Cache 就要吃掉 **20 GB**。而一张 A100 80GB 的显卡，模型权重本身就要占用 140 GB（70B × 2 bytes），只能靠多卡并行。留给 KV Cache 的空间极为有限。

这就是问题的核心：**KV Cache 的显存管理效率，直接决定了推理系统的吞吐量。**

---

## 二、朴素实现的困境

### 2.1 连续内存分配的浪费

最直觉的做法是为每条请求预分配一块连续显存，大小等于最大序列长度。但问题是：

- **内部碎片**：请求实际长度往往远小于最大长度，预分配的空间大量浪费。
- **外部碎片**：不同请求长度不同，释放后留下大小不一的空洞，难以利用。
- **无法动态扩展**：一旦预分配用完，请求就被截断或拒绝。

实测显示，这种朴素方式的显存利用率只有 **20%-40%**。也就是说，你花大价钱买的 A100，有一半以上的显存在空转。

### 2.2 请求调度的两难

推理系统面临一个经典矛盾：
- **先来先服务（FCFS）**：简单公平，但长请求会阻塞短请求（队头阻塞）。
- **短作业优先（SJF）**：需要预知请求长度，实际场景很难做到。

无论哪种策略，只要显存分配效率低，系统吞吐量就上不去。

---

## 三、PagedAttention：用操作系统思维解决显存管理

### 3.1 核心洞察

UC Berkeley 的研究团队提出了一个优雅的类比：**KV Cache 的显存管理，和操作系统的虚拟内存管理本质上是同一个问题。**

操作系统用**分页（Paging）** 解决进程内存的碎片问题：把物理内存切成固定大小的页（Page），进程看到的是连续的虚拟地址空间，实际物理页可以分散存放。

PagedAttention 把这个思路搬到了 GPU 上。

### 3.2 工作机制

1. **物理块（Physical Block）**：把 GPU 显存切成固定大小的块，每块存储固定数量 token 的 KV 向量。比如每块存 16 个 token。

2. **逻辑块（Logical Block）**：每条请求看到的是连续的逻辑块序列，通过**块表（Block Table）** 映射到物理块。

3. **按需分配**：请求到达时，不预分配最大长度，而是每生成 16 个 token 才申请一个新物理块。

4. **共享前缀**：多条请求如果共享相同的 system prompt 或 few-shot 示例，它们的 KV Cache 可以共享同一组物理块，用引用计数管理。

```
请求 A: [逻辑块0] → [物理块3]
        [逻辑块1] → [物理块7]
        [逻辑块2] → [物理块1]

请求 B: [逻辑块0] → [物理块3]   # 共享！引用计数 +1
        [逻辑块1] → [物理块9]
```

### 3.3 效果对比

| 指标 | 朴素连续分配 | PagedAttention |
|------|------------|----------------|
| 显存利用率 | 20%-40% | 接近 100% |
| 内部碎片 | 严重（预分配最大长度） | 极小（按需分配） |
| 外部碎片 | 严重（大小不一的空洞） | 不存在（固定块大小） |
| 前缀共享 | 不支持 | 原生支持 |

PagedAttention 把显存利用率从不到 40% 提升到了接近 **100%**，意味着同样的硬件可以同时服务 **2-4 倍**的请求。

---

## 四、vLLM：从论文到生产

### 4.1 诞生背景

vLLM 最初是 UC Berkeley Sky Computing Lab 的研究项目，论文《Efficient Memory Management for Large Language Model Serving with PagedAttention》发表于 2023 年。但它的野心远不止一篇论文——vLLM 要做一个**生产级的 LLM 推理引擎**。

### 4.2 架构设计

vLLM 的核心组件：

- **调度器（Scheduler）**：决定哪些请求进入 GPU 执行，支持抢占和优先级。
- **KV Cache 管理器**：基于 PagedAttention 的块分配器，管理所有请求的 KV Cache 生命周期。
- **执行引擎**：高效的 CUDA kernel 实现，支持连续批处理（Continuous Batching）。

**连续批处理**是另一个关键优化。传统批处理必须等一个 batch 的所有请求都完成才能开始下一个。连续批处理允许新请求随时加入正在执行的 batch，只要有空闲的 KV Cache 块可用。这大幅提升了 GPU 利用率。

### 4.3 演进历程

**2023 年：起步**
- vLLM 0.1 发布，实现 PagedAttention 核心。
- 支持 LLaMA、OPT 等模型。
- 吞吐量比 HuggingFace Transformers 提升 **24 倍**。

**2024 年：生态爆发**
- 支持 GQA（Grouped-Query Attention）、MoE 等新架构。
- 引入 Prefix Caching，进一步优化共享前缀场景。
- 支持 FP8 量化推理。
- 成为 LangChain、LlamaIndex 等框架的默认推理后端。

**2025 年：走向全能**
- 支持多模态模型（视觉、音频）。
- 引入 Disaggregated Prefill，把预填充和解码阶段分离到不同 GPU。
- 支持 Speculative Decoding，用小模型加速大模型生成。
- 与 NVIDIA TensorRT-LLM、AMD ROCm 深度集成。

**2026 年：现状**
- vLLM 已经成为事实标准的开源 LLM 推理引擎。
- 支持 100+ 种模型架构。
- 社区贡献者超过 1000 人。
- 被众多云厂商和企业采用。

### 4.4 与其他引擎的对比

| 特性 | vLLM | TensorRT-LLM | SGLang |
|------|------|---------------|--------|
| 开源协议 | Apache 2.0 | Apache 2.0 | Apache 2.0 |
| PagedAttention | ✅ | ✅ | ✅ (RadixAttention) |
| 连续批处理 | ✅ | ✅ | ✅ |
| 模型覆盖 | 最广 | NVIDIA 生态 | 中等 |
| 易用性 | 高 | 中（需要编译） | 高 |
| 极致性能 | 高 | 最高（NVIDIA 优化） | 高 |
| 生产成熟度 | 高 | 高 | 中 |

---

## 五、KV Cache 优化的前沿方向

### 5.1 压缩：减少 KV Cache 的体积

- **量化**：把 FP16 的 KV Cache 量化到 INT8 甚至 INT4，显存占用直接减半或更多。
- **稀疏化**：只保留重要的 token 的 KV Cache，丢弃不重要的。H2O（Heavy Hitter Oracle）就是这个思路。
- **低秩分解**：用 SVD 等方法把 KV 向量投影到低维空间。

### 5.2 共享：让多条请求复用 KV Cache

- **Prefix Caching**：共享相同的 system prompt。vLLM 和 SGLang 都已支持。
- **Prompt Caching**：更激进的缓存策略，把常见问题的完整 KV Cache 都缓存起来。
- **跨请求共享**：在多轮对话中，复用之前轮次的 KV Cache。

### 5.3 架构创新：从源头减少 KV Cache

- **GQA（Grouped-Query Attention）**：多个 Query 头共享一组 KV 头，LLaMA 2/3 都用了这个方案。
- **MQA（Multi-Query Attention）**：所有 Query 头共享同一组 KV 头，极致压缩。
- **MLA（Multi-head Latent Attention）**：DeepSeek-V2 提出的方案，把 KV Cache 压缩到极致。
- **线性注意力**：用线性核函数替代 softmax，从根本上避免存储完整 KV Cache。

### 5.4 系统层面的优化

- **Disaggregated Prefill**：预填充（计算密集）和解码（访存密集）有不同的硬件需求，分离到不同 GPU 可以各自优化。
- **Offloading**：把不常用的 KV Cache 卸载到 CPU 内存或 NVMe SSD，需要时再加载。
- **动态调度**：根据当前显存压力，动态调整 batch 大小和请求优先级。

---

## 六、实践建议

如果你正在搭建 LLM 推理服务，以下是一些实用建议：

1. **首选 vLLM**：除非你有非常特殊的性能需求，vLLM 是最成熟、最易用的选择。
2. **开启 Prefix Caching**：如果你的场景有大量共享 system prompt 的请求，这个优化效果立竿见影。
3. **合理设置 max_num_seqs**：控制并发请求数，避免 KV Cache 爆显存。
4. **监控显存使用**：用 `nvidia-smi` 或 vLLM 自带的 metrics 端点，持续监控 KV Cache 的显存占用。
5. **考虑量化**：FP8 量化几乎不损失精度，但能把 KV Cache 和模型权重都压缩一半。

---

## 结语

KV Cache 的优化史，本质上是一部**显存管理的进化史**。从朴素的连续分配，到 PagedAttention 的分页思想，再到 vLLM 的工程落地，每一步都在回答同一个问题：**如何用有限的显存，服务更多的请求。**

这个领域还在快速演进。DeepSeek 的 MLA 架构、Google 的 MQA 变体、各种稀疏化方案，都在试图从不同角度压缩 KV Cache 的体积。而 Disaggregated Prefill、Offloading 等系统优化，则在硬件层面寻找新的可能性。

对于技术老兵来说，理解 KV Cache 不仅仅是理解一个优化技巧——它是理解整个 LLM 推理系统的关键钥匙。掌握了它，你就掌握了大模型落地的最后一公里。
