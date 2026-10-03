## 大模型预训练全流程：数据清洗、Tokenizer、分布式策略（工程实战）

> 从原始语料到千亿参数模型，每一个环节都藏着工程决策的深坑。本文基于真实项目经验，拆解预训练三大核心阶段的工程细节。

---

### 0. 全局视角：预训练的工程全景

很多技术文章把预训练描述成"拿数据训模型"五个字。但当你真正从零搭建一套预训练流水线时，会发现90%的工程量不在模型本身，而在数据处理和训练基础设施上。

一个典型的预训练项目，工程投入大致是这样的比例：

- **数据采集与清洗**：40%
- **Tokenizer训练与数据Token化**：15%
- **分布式训练基础设施搭建与调优**：30%
- **模型架构实现与调试**：10%
- **评估与迭代**：5%

本文聚焦前三个环节，也就是数据清洗、Tokenizer、分布式策略的工程实战。不讲原理推导，只讲你真正动手做时会踩的坑。

---

### 1. 数据清洗：脏数据是模型的慢性毒药

#### 1.1 数据源规划

预训练数据通常来自多个渠道：

| 数据源 | 典型占比 | 特点 |
|--------|---------|------|
| Common Crawl | 40-60% | 量大、噪声多、需要深度清洗 |
| 书籍/学术论文 | 15-25% | 质量高、领域覆盖窄 |
| 代码（GitHub） | 10-20% | 对推理能力有帮助 |
| 百科/知识库 | 5-10% | 结构化程度高 |
| 对话/论坛 | 5-10% | 语言多样性好 |

关键决策：**配比不是拍脑袋定的**。你需要先确定下游任务方向，再反推数据配比。做通用大模型和做代码大模型，数据策略完全不同。

#### 1.2 清洗流水线的工程实现

一套生产级的数据清洗流水线，通常包含以下阶段：

**第一阶段：格式标准化**

```python
# 典型的文档解析pipeline
def normalize_document(raw_doc: dict) -> str:
    # 1. HTML去标签，保留正文结构
    text = html_to_text(raw_doc['html'])
    # 2. Unicode标准化（全角/半角、特殊空格等）
    text = unicodedata.normalize('NFKC', text)
    # 3. 去除零宽字符、控制字符
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    # 4. 连续空行合并
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()
```

这一步看着简单，但Unicode的坑比你想象的多。全角数字、特殊连字符、RTL标记符，每一个都可能导致下游处理异常。

**第二阶段：语言识别与过滤**

```python
from fasttext import load_model

lid_model = load_model('lid.176.bin')

def filter_by_language(text: str, target_lang='zh', threshold=0.65) -> bool:
    predictions = lid_model.predict(text.replace('\n', ' ')[:512])
    lang, score = predictions[0][0].replace('__label__', ''), predictions[1][0]
    return lang == target_lang and score >= threshold
```

注意：fasttext的语言识别模型对短文本（<50字符）准确率骤降。工程上通常的做法是，短文本直接按来源域名的语言标签归类，不做模型推理。

**第三阶段：质量过滤**

这是最关键也最tricky的阶段。常用策略：

- **基于规则**：过滤广告、导航栏、版权声明、Cookie声明等模板化内容
- **基于困惑度（Perplexity）**：用小型语言模型计算文本困惑度，过滤困惑度过高的文本（通常意味着乱码或低质量拼凑）
- **基于重复率**：n-gram重复率过高的文档直接丢弃
- **基于长度**：过短（<50字）或过长（>100万字）的文档需要特殊处理

```python
def compute_perplexity(text: str, kenlm_model) -> float:
    """用KenLM计算困惑度，作为质量信号"""
    log_prob = kenlm_model.score(text)
    num_words = len(text.split())
    return 10 ** (-log_prob / num_words) if num_words > 0 else float('inf')

def quality_filter(doc: dict) -> bool:
    pp = compute_perplexity(doc['text'], kenlm)
    dup_ratio = compute_ngram_dup_ratio(doc['text'], n=5)
    alpha_ratio = sum(c.isalpha() for c in doc['text']) / len(doc['text'])
    
    return (
        10 < pp < 1000 and           # 困惑度在合理范围
        dup_ratio < 0.3 and           # 重复率不超过30%
        alpha_ratio > 0.6 and         # 可读字符占比
        len(doc['text']) > 100        # 最小长度
    )
```

**第四阶段：去重**

去重是数据清洗中最耗计算资源的环节。工程上通常用**MinHash + LSH**做近似去重：

```python
from datasketch import MinHashLSH, MinHash

def build_dedup_index(docs: list, threshold=0.8):
    lsh = MinHashLSH(threshold=threshold, num_perm=128)
    for i, doc in enumerate(docs):
        m = MinHash(num_perm=128)
        for word in doc['text'].split():
            m.update(word.encode('utf8'))
        lsh.insert(str(i), m)
    return lsh
```

真实项目中的一个血泪教训：**去重必须在Token化之前做**。很多团队先Token化再去重，结果发现相同内容的Token ID序列因为边界对齐问题略有不同，导致去重率大幅下降。

#### 1.3 数据清洗的工程陷阱

- **内存管理**：Common Crawl原始数据动辄几百TB，不能全量加载。必须用流式处理（generator），每个文件处理完立即释放
- **并行化**：清洗是CPU密集型任务，用多进程而非多线程。Python的GIL在这里是真实瓶颈
- **可复现性**：每次清洗都要记录完整的参数和版本，方便回溯。建议用配置文件驱动，不要硬编码阈值
- **中间存储格式**：用parquet而非jsonl，压缩比和读取速度都好得多

---

### 2. Tokenizer：模型的"五官"

#### 2.1 为什么Tokenizer这么重要

Tokenizer决定了模型"看到"什么。一个糟糕的Tokenizer会导致：

- 中文每个字都被拆成2-3个Token，浪费序列长度
- 稀有领域的专业术语被拆得支离破碎
- 数字、代码的编码效率极低

直接影响：**同样的模型参数和训练预算，Tokenizer差的模型实际"看到"的有效信息量少30-50%。**

#### 2.2 BPE训练的工程要点

主流大模型使用BPE（Byte Pair Encoding）或其变体。训练Tokenizer时的关键工程决策：

**词表大小选择**

| 词表大小 | 优点 | 缺点 |
|---------|------|------|
| 32K | 模型Embedding层参数少 | 编码效率低，序列长 |
| 64K | 平衡点 | 主流选择 |
| 128K | 编码效率高 | Embedding层参数多，稀有Token训练不充分 |
| 256K+ | 极高编码效率 | 训练数据必须足够大，否则大量Token几乎不出现 |

实践建议：**中文为主的模型建议64K-128K**。纯英文模型32K就够，但中文是象形文字，一字一Token的需求使得词表必须更大。

**训练语料的配比**

Tokenizer的训练语料配比不需要和预训练数据完全一致，但要覆盖目标语言的分布。一个常见错误是只用英文语料训练Tokenizer，然后用于中文模型——中文编码效率会极低。

```python
import sentencepiece as spm

spm.SentencePieceTrainer.train(
    input='tokenizer_train_data.txt',    # 混合语料
    model_prefix='tokenizer',
    vocab_size=64000,
    model_type='bpe',
    character_coverage=0.9995,           # 中文要高，英文0.9999够
    byte_fallback=True,                  # 未知字符用UTF-8字节回退
    split_digits=True,                   # 数字逐位拆分，提升算术能力
    num_threads=32,                      # 并行训练
)
```

**特殊Token设计**

```
[BOS] [EOS] [PAD] [UNK] [SEP] [CLS] [MASK]
<|system|> <|user|> <|assistant|>         # 对话角色
<|fim_prefix|> <|fim_middle|> <|fim_suffix|>      # Fill-in-middle
```

特殊Token的设计直接影响模型的微调能力。建议在预训练阶段就把SFT需要的特殊Token加进去，否则后期扩展词表会导致Embedding矩阵不兼容。

#### 2.3 Tokenizer的工程验证

训练完Tokenizer后，必须做以下验证：

```python
def validate_tokenizer(sp, test_texts: list):
    results = []
    for text in test_texts:
        tokens = sp.encode(text, out_type=str)
        decoded = sp.decode(sp.encode(text))
        
        # 1. 无损验证
        assert decoded == text, f"编码-解码不一致: {text[:50]}"
        
        # 2. 压缩率（每个Token平均多少字节）
        compression = len(text.encode('utf-8')) / len(tokens)
        
        # 3. 中文压缩率单独统计
        if is_chinese(text):
            results.append(('zh', compression))
        else:
            results.append(('en', compression))
    
    return results
```

中文压缩率目标：**每个Token对应1.5-2.0个汉字**。低于1.2说明词表设计有问题。

---

### 3. 分布式策略：让千卡集群高效运转

#### 3.1 为什么分布式策略是工程核心

一个7B参数的模型，FP16训练时需要约14GB显存存储参数，加上梯度和优化器状态，总显存需求约56GB。单卡放不下，必须分布式。

但分布式不只是"把模型切开放到多张卡上"这么简单。通信开销、负载均衡、容错恢复，每一个都是工程深坑。

#### 3.2 三种并行策略

**数据并行（Data Parallelism）**

最简单的并行方式。每张卡持有完整模型副本，处理不同的数据批次。

```python
# PyTorch DDP
model = DistributedDataParallel(model, device_ids=[local_rank])
```

优点：实现简单，通信开销小（只需同步梯度）。
缺点：每张卡都要装下完整模型，受单卡显存限制。
适用：模型能放进单卡时（通常<3B参数）。

**张量并行（Tensor Parallelism，TP）**

把单个算子（矩阵乘法）拆到多张卡上执行。例如一个`[H, H]`的线性层，按列切成`[H, H/N]`放到N张卡上。

```python
# Megatron-LM 风格的列并行
class ColumnParallelLinear(nn.Module):
    def __init__(self, in_features, out_features, num_gpus):
        super().__init__()
        self.weight = nn.Parameter(
            torch.empty(out_features // num_gpus, in_features)
        )
```

优点：可以突破单卡显存限制。
缺点：每层计算都需要AllReduce通信，对网络带宽要求极高（必须用NVLink）。
适用：同一节点内的多卡并行（通常8卡）。

**流水线并行（Pipeline Parallelism，PP）**

把模型的不同层放到不同卡上，数据像流水线一样流过。

关键问题：**气泡率（Bubble Ratio）**。如果把模型均分为K个阶段，朴素流水线的气泡率为`(K-1)/K`，即K=4时有75%的时间在等待。

解决方案：**微批次（Micro-batching）**。把一个大batch分成多个小micro-batch，让不同micro-batch在不同阶段同时执行。

```python
# 流水线调度示意
# GPipe: 先全前向，再全反向
# 1F1B: 交替执行前向和反向，减少内存峰值

def schedule_1f1b(micro_batches, num_stages):
    """1F1B调度：减少峰值内存"""
    # warmup阶段：逐步填满流水线
    for i in range(num_stages - 1):
        forward(micro_batches[i])
    
    # 稳态阶段：1个forward + 1个backward
    for i in range(num_stages - 1, len(micro_batches)):
        forward(micro_batches[i])
        backward(micro_batches[i - num_stages + 1])
    
    # cooldown阶段：排空流水线
    for i in range(num_stages - 1):
        backward(micro_batches[len(micro_batches) - num_stages + 1 + i])
```

#### 3.3 3D并行：实战中的混合策略

真正的生产训练通常组合使用三种并行：

```
假设：64张GPU，模型70B
├── TP = 8   （同节点8卡NVLink互联）
├── PP = 4   （4个Pipeline阶段）
└── DP = 2   （2组数据并行）
    总计 = 8 × 4 × 2 = 64 GPU
```

配置的经验法则：
- TP放在通信最快的层级（NVLink > IB > RoCE）
- PP放在通信较慢的层级（只需点对点传输激活值）
- DP放在最外层，通信量最小

#### 3.4 通信优化实战

分布式训练中，通信往往是性能瓶颈。几个关键优化：

**梯度压缩**

```python
# 梯度先在本地累积N步，再同步
optimizer = ZeroRedundancyOptimizer(
    model.parameters(),
    optimizer_class=torch.optim.AdamW,
    overlap_with_param=True,  # 通信与计算重叠
)
```

**通信与计算重叠**

```python
# 在反向传播过程中，某一层梯度计算完成后立即发起通信
# 而不是等所有层梯度都算完再统一通信
with model.no_sync():  # 禁止同步，累积梯度
    loss.backward()     # 前几层的梯度
# 这里触发同步
loss.backward()         # 最后一层的梯度
```

**激活值重计算（Activation Checkpointing）**

用时间换空间。前向传播时不保存中间激活值，反向传播时重新计算。

```python
from torch.utils.checkpoint import checkpoint

class TransformerBlock(nn.Module):
    def forward(self, x):
        # 不保存中间结果，反向时重算
        return checkpoint(self._forward, x, use_reentrant=False)
```

实测效果：**显存减少60%，训练速度下降约25%**。这是个划算的tradeoff。

#### 3.5 容错与恢复

千卡训练跑几周，不考虑容错就是自杀。必须做：

1. **定期Checkpoint**：每隔1000-2000步保存完整训练状态（模型参数 + 优化器状态 + 数据加载器位置 + 随机数种子）
2. **异步Checkpoint**：在后台线程写Checkpoint，不阻塞训练
3. **弹性训练**：检测到节点故障时，自动摘除故障节点，用剩余节点继续训练

```python
# 异步Checkpoint示例
import torch.distributed.checkpoint as dcp

def async_save_checkpoint(state, step):
    """异步保存，不阻塞训练"""
    path = f"checkpoints/step_{step}"
    # 用独立进程写磁盘
    dist_cp.save(
        state_dict=state,
        storage_writer=dcp.FileSystemWriter(path),
        planner=dcp.async_save  # 异步写入
    )
```

---

### 4. 端到端Pipeline：串联三大环节

最后把三个环节串起来，展示一个完整的预训练Pipeline：

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  原始语料     │───>│  数据清洗     │───>│  清洗后语料   │
│  (TB级)      │    │  (流式处理)   │    │  (压缩存储)   │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                    ┌──────────────┐            │
                    │  Tokenizer   │<───────────┘
                    │  训练+验证    │    (用子集训练Tokenizer)
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  数据Token化  │    (分布式Map处理)
                    │  + 打包      │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  分布式训练   │    (3D并行 + 容错)
                    │  数千GPU     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  评估+迭代   │    (困惑度 + 下游任务)
                    └──────────────┘
```

每个环节的输出都是下一个环节的输入，任何一步的质量问题都会被放大。这就是为什么预训练是系统工程，不是炼丹。

---

### 5. 总结：三个核心认知

**第一，数据质量 > 数据数量。** 1TB高质量数据的训练效果通常优于10TB低质量数据。在数据清洗上的投入，回报率远高于增加训练算力。

**第二，Tokenizer是被严重低估的环节。** 大多数团队花大量时间调模型架构，却对Tokenizer一笔带过。一个针对目标语言优化的Tokenizer，可以让模型效果提升一个档次。

**第三，分布式策略的核心不是算法，是工程。** 3D并行的原理不难理解，但如何调通、如何优化通信、如何处理故障，才是真正的挑战。做好分布式训练需要深厚的系统工程能力。

预训练是一场工程马拉松。理解这三个环节的工程细节，才能在真正动手时不被埋在技术债里。

---

*本文基于公开资料与工程实践经验整理，部分代码为简化示意，生产环境需根据具体框架（Megatron-LM、DeepSpeed、FSDP等）调整。*
