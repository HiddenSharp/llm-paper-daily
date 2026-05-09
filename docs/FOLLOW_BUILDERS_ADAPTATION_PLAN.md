# Follow Builders 改造参考与 paper-daily 订阅方案

## 目标

本文档记录以下内容：

1. `follow-builders` 仓库是如何实现“每日订阅”的
2. 对当前 `paper-daily` / `new-project` 仓库的映射关系
3. PDF 预处理相关 skill 的调研结果
4. 当前实现状态、真实测试结果与问题定位
5. 后续推荐方案

本文档服务于后续继续实现“论文日报订阅”能力时的工程参考。

---

## 一、`follow-builders` 是如何实现每日订阅的

### 1. 整体架构

`follow-builders` 实际上分成两条链路：

1. **中央内容生产链**
2. **用户本地订阅 / 投递链**

这两条链路逻辑上是分开的，只是对用户看起来像一个 skill。

### 2. 中央内容生产链

这部分**不是 skill**，而是固定脚本 + GitHub Actions。

关键文件：

- `/tmp/follow-builders/scripts/generate-feed.js`
- `/tmp/follow-builders/.github/workflows/generate-feed.yml`

工作流说明：

- GitHub Actions 定时触发
- 默认每天 UTC `06:17`
- 运行 `generate-feed.js`
- 更新并提交：
  - `/tmp/follow-builders/feed-x.json`
  - `/tmp/follow-builders/feed-podcasts.json`
  - `/tmp/follow-builders/feed-blogs.json`
  - `/tmp/follow-builders/state-feed.json`

因此其内容生产链是：

```text
GitHub Actions
-> generate-feed.js
-> 更新公共 feed JSON
-> commit 回仓库
```

### 3. 用户订阅链

这部分才是用户真正接触到的 skill。

关键文件：

- `/tmp/follow-builders/SKILL.md`
- `/tmp/follow-builders/scripts/prepare-digest.js`
- `/tmp/follow-builders/scripts/deliver.js`

职责：

- onboarding
- 询问频率 / 时区 / 语言
- 询问 delivery method（stdout / Telegram）
- 写本地配置
- 创建 cron
- 每次运行时读取中央 feed
- remix 成 digest
- 发送出去

### 4. 用户通过什么方式订阅

用户订阅入口是 **skill 对话**，不是直接改配置文件。

用户通过 skill：

- 配置 daily / weekly
- 配置 timezone
- 配置 language
- 配置 delivery method

skill 把这些写入：

- `~/.follow-builders/config.json`
- `~/.follow-builders/.env`

后续由 cron 执行：

- `prepare-digest.js`
- 再交给 agent remix
- `deliver.js` 负责 Telegram / stdout

所以本质上：

```text
用户通过 skill 订阅
-> skill 写配置
-> skill 创建 cron
-> cron 每天执行 digest 脚本
-> deliver.js 投递
```

### 5. 关键设计点

`follow-builders` 的关键思想是：

- **抓内容中央化**
- **用户偏好本地化**
- **投递独立化**

因此用户不需要自己去抓 X / podcast / blog，只消费公共 feed。

---

## 二、这个架构如何映射到 `paper-daily`

### 1. 推荐映射

对当前项目，建议同样拆成两层：

#### A. 中央内容生产链

这部分不应该是订阅 skill 的主入口，而应该是仓库的固定生产链：

```text
arXiv discover
-> PDF preprocess
-> LLM summarize
-> update README.md / README_en.md
-> 输出 feed-papers.json
```

建议未来由固定脚本 + GitHub Actions 承担。

#### B. 用户订阅链

这部分可以做成单独的订阅 skill，逻辑类似 `follow-builders`：

```text
读取 feed-papers.json
-> 根据语言 / 长度偏好组织 digest
-> deliver 到 stdout / Telegram
```

### 2. 是否应该拆成两个 skill

建议：

- `paper-daily`：内容生产 skill / 工具链
- `paper-subscribe`：订阅与投递 skill

原因：

- 维护者关心 discover / summarize / README 更新
- 订阅者关心 daily/weekly、时区、语言、推送方式

这两类用户不是同一种。

### 3. 当前仓库最适合的未来结构

```text
new-project/
  README.md
  README_en.md
  summary/
  summary_en/
  feed-papers.json          # 未来新增
  skill/
    paper-daily/           # 内容生产
    paper-subscribe/       # 订阅投递（未来）
```

---

## 三、PDF 处理 skill 调研结果

### 1. 目标

调研 PDF 处理相关 skill，判断哪一种更适合嵌入 `paper-daily` 的摘要前预处理链。

### 2. 候选 skill

#### 候选 A：`anthropics/skills@pdf`

来源：

- https://skills.sh/anthropics/skills/pdf

核心思路：

- `pdftotext`
- `pdfplumber`
- `pypdf`
- `qpdf`
- OCR 兜底

#### 候选 B：`letta-ai/skills@extracting-pdf-text`

来源：

- https://skills.sh/letta-ai/skills/extracting-pdf-text

核心思路：

- `PyMuPDF` 优先
- `pdfplumber` 处理表格 / 布局复杂的 PDF
- OCR 兜底
- 输出更偏向 LLM / RAG 友好的文本

### 3. 实测样本

实测论文：

- `2604.24668`
- `The Price of Agreement: Measuring LLM Sycophancy in Agentic Financial Applications`

### 4. 实测结果

#### `anthropics/pdf` 风格

使用本机已有 `pdftotext` 做真实测试：

- PDF 下载：约 **61.90 秒**
- 本地抽取首页：约 **0.22 秒**
- 本地抽取前 8 页：约 **0.03 秒**

抽取质量：

- 能直接抽到标题、作者、机构（`Writer, Inc.`）、abstract、introduction 开头

结论：

- **下载慢**
- **但下载完成后，本地文本提取非常快**
- 很适合作为日报主链的 PDF 预处理基线

#### `letta` 风格

尝试按其推荐方向安装 `PyMuPDF` 依赖，发现：

- 当前环境安装额外大轮子有明显阻力
- 在本机上，安装本身就成了流程障碍

结论：

- 思路更适合“未来增强版”
- 但对当前这条主链，环境成本明显更高

### 5. 调研结论

当前主链优先选：

- **`anthropics/pdf` 风格**

原因：

- 依赖轻
- 已在本机证明可跑
- 对 arXiv born-digital 论文 PDF 足够好
- 更适合先把日报生产链跑稳

未来增强再借鉴：

- **`letta-ai/skills@extracting-pdf-text`**

原因：

- 更适合复杂版式 PDF
- 更适合表格 / OCR / LLM-friendly extraction
- 适合后续做多路由 PDF 预处理层

---

## 四、当前 `paper-daily` 的实现状态

### 1. 已实现内容

当前 `new-project/skill/paper-daily/` 已有这些能力：

- arXiv 发现与排序
- 基于关键词优先级选择候选论文
- 生成 `summary/` 与 `summary_en/`
- patch `README.md` 与 `README_en.md`
- 更新时间戳

关键文件：

- `new-project/skill/paper-daily/scripts/discover.py`
- `new-project/skill/paper-daily/scripts/run_daily.py`
- `new-project/skill/paper-daily/scripts/paper_daily/arxiv_client.py`
- `new-project/skill/paper-daily/scripts/paper_daily/discovery.py`
- `new-project/skill/paper-daily/scripts/paper_daily/render.py`
- `new-project/skill/paper-daily/scripts/paper_daily/patch.py`
- `new-project/skill/paper-daily/scripts/paper_daily/summary.py`
- `new-project/skill/paper-daily/scripts/paper_daily/pdf_preprocess.py`

### 2. 已完成的整理

已经做过的精简：

- `README2.md` / `README_en2.md` 已从新 skill 依赖中移除
- `SKILL.md` 中不再提 `README2*`
- `run_daily.py` 默认不写中间 JSON 调试产物

### 3. 当前 README patch 目标

- `new-project/README.md`
- `new-project/README_en.md`

不会再操作：

- `README2.md`
- `README_en2.md`
- `CATEGORIES2.md`

---

## 五、真实测试结果与问题定位

### 1. discovery 测试

对 `2026-04-27`（UTC）进行 discovery：

- `Agent`: 54
- `Agents`: 54
- `LLM`: 81

说明：

- 发现阶段正常

### 2. DashScope summary 测试

当前接入的大模型配置：

- `base_url = https://dashscope.aliyuncs.com/compatible-mode/v1`
- `model = qwen3.6-plus`
- `DASHSCOPE_API_KEY` 从环境变量读取
- `enable_thinking = false`

### 3. 问题定位过程

做过 3 组排查：

#### A. 最小 SDK 请求

请求：`你是谁`

结果：

- DashScope 返回约 **2.32 秒**

说明：

- 接口本身可用
- 不是纯粹“API 不通”

#### B. 轻量摘要请求

只喂：

- title
- abstract
- institution hint

结果：

- 返回约 **14.85 秒**
- 而且返回合法 JSON

说明：

- `qwen3.6-plus` 做论文摘要不是完全不可用

#### C. 完整流水线问题

旧版本问题：

- 主链会卡在 summary 阶段
- `summary/*.md` 不落盘
- `README.md` 不更新

真正的瓶颈被确认在：

- **PDF 预处理**
- 尤其是下载太慢、重复下载、输入过重

### 4. 当前已做的修复

已经把 PDF 处理改成：

```text
单次下载
-> 首页提取
-> 前 6 页提取
-> 传给 DashScope
```

而不是：

```text
下载一次提首页
再下载一次提正文
```

### 5. 当前问题是否完全解决

还没有完全解决。

虽然主链已经明显改善，但对于“当天 paper 实时日更”来说，`qwen3.6-plus` + 当前 prompt + 当前输入组合仍然有性能风险。

这意味着：

- 方向已经对
- 但需要继续优化摘要链

---

## 六、后续改造计划

### 1. 内容生产链（推荐）

采用 `follow-builders` 的模式：

#### 仓库中央生产

- 固定脚本：
  - `run_daily.py`
- 固定 workflow：
  - 未来新增 `.github/workflows/daily.yml`
- 输出：
  - `README.md`
  - `README_en.md`
  - `summary/`
  - `summary_en/`
  - `feed-papers.json`

### 2. 订阅链（推荐）

未来新增单独的 `paper-subscribe` skill：

职责：

- onboarding
- 订阅频率（daily / weekly）
- 时区
- 语言
- delivery method（stdout / Telegram）
- cron
- 读取 `feed-papers.json`
- 投递 digest

### 3. `feed-papers.json` 建议

建议作为中央公共 feed：

```json
{
  "generatedAt": "...",
  "date": "2026-05-09",
  "papers": [
    {
      "paper_id": "2604.24955",
      "title": "...",
      "links": {
        "abs": "...",
        "pdf": "..."
      },
      "institution": "...",
      "summary_cn": "...",
      "summary_en": "...",
      "summary_path": "summary/2026-04/2604.24955.md",
      "summary_en_path": "summary_en/2026-04/2604.24955.md"
    }
  ]
}
```

### 4. `paper-daily` 主链建议继续优化

#### 建议 1：把摘要改成三层降级

```text
fast path:
title + abstract + first page
-> DashScope summarize

fallback path:
title + abstract only
-> DashScope summarize

offline fallback:
template / heuristic summary
-> 至少落盘 summary 和 README
```

#### 建议 2：控制时延

- PDF 下载设置更明确超时
- summary 阶段设置更强超时与降级
- 不允许单篇论文长时间拖住整条日报主链

#### 建议 3：未来再吸收 `letta` 思路

把 `pdf_preprocess.py` 升级成多路由：

```text
simple text PDF -> pdftotext
complex layout PDF -> pdfplumber / PyMuPDF
scanned PDF -> OCR
```

---

## 七、最终建议

### 现在就该做的

1. 保持 `paper-daily` 作为**中央内容生产 skill**
2. 继续优化当前 PDF + DashScope 摘要主链
3. 产出 `feed-papers.json`
4. 再做单独的 `paper-subscribe`

### 不建议现在做的

1. 让订阅 skill 自己去抓 arXiv / PDF
2. 把 discover / summarize / subscribe 混成一个大 skill
3. 过早强依赖更重的 PDF 工具链

---

## 八、摘要版结论

`follow-builders` 的“每日订阅”能成立，不是因为它有一个万能 skill，而是因为它做了清晰分层：

- **中央 feed 生成**
- **本地订阅配置**
- **定时任务**
- **独立投递脚本**

对你的仓库，最适合的映射也是：

- `paper-daily`：负责每天生成内容
- `paper-subscribe`：负责用户订阅与接收

而在 PDF 预处理上，当前应优先采用 `anthropics/pdf` 风格做主链，未来再吸收 `letta` 的路由式增强思路。
