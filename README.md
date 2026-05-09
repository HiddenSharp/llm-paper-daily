<h2 align='center'>llm-paper-daily 日常论文精选</h2>
<div align='center'>

[![Status](https://img.shields.io/badge/status-Update_05.09_17:06-success.svg)]() [![简体中文 badge](https://img.shields.io/badge/%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-Simplified%20Chinese-blue)](./README.md) [![English badge](https://img.shields.io/badge/%E8%8B%B1%E6%96%87-English-blue)](./README_en.md) 

</div>

欢迎来到 **llm-paper-daily**! 这是一个获取 LLM、Agent 相关研究论文的每日更新和分类平台。

📚 **每日更新:** 仓库每天会带来最新的 LLM、Agent 相关研究，并附有 arXiv 地址、相关 GitHub 仓库和文章的总结。

<!-- paper-daily:readme:updates:start -->
<details>
  <summary>查看更新文章 &nbsp;&nbsp;<sub>更新时间: 2026年05月09日 17:06</sub></summary>
<br>

- StraTA: Incentivizing Agentic Reinforcement Learning with Strategic Trajectory Abstraction 
</details>
<!-- paper-daily:readme:updates:end -->

## 最新论文

<!-- paper-daily:readme:months:start -->
### 05月

| &nbsp;Date&nbsp;&nbsp; | Paper | Links & Summary |
| --- | --- | --- |
| <span style='display: inline-block; width: 42px;'>05-07</span> | **StraTA: Incentivizing Agentic Reinforcement Learning with Strategic Trajectory Abstraction**<br><sub>机构: The Chinese University of Hong Kong, Shanghai Artificial Intelligence Laboratory, University of Oxford, University of Georgia, Shenzhen Loop Area Institute<br>StraTA 通过引入显式的轨迹级策略抽象，解决了现有反应式智能体在长视野决策中面临的探索短视和信用分配难题。该方法通过分层训练和多样化策略机制，显著提升了 LLM 智能体在复杂交互任务中的性能和样本效率，为构建更可靠的长视野智能体提供了新的范式。</sub>| <div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)](https://arxiv.org/pdf/2605.06642v1)</div><div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)](summary/2026-05/2605.06642.md) <div style='min-width:85px;'>[![GitHub](https://img.shields.io/badge/GitHub-View-brightgreen?logo=github)](https://github.com/xxyQwQ/StraTA)</div> |
| <span style='display: inline-block; width: 42px;'>05-06</span> | **FoodCHA: Multi-Modal LLM Agent for Fine-Grained Food Analysis**<br><sub>机构: University of California, San Diego<br>FoodCHA 通过引入分层代理机制，有效解决了食物识别中细粒度属性提取难和标签非规范化的问题。它不仅在精度上显著优于现有的大型视觉语言模型，还通过采用轻量化基座模型提升了实际部署的可行性，为实时、准确的个人营养监测提供了新的技术路径。</sub>| <div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)](https://arxiv.org/pdf/2605.05499v1)</div><div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)](summary/2026-05/2605.05499.md)  |
| <span style='display: inline-block; width: 42px;'>05-05</span> | **Agent Island: A Saturation- and Contamination-Resistant Benchmark from Multiagent Games**<br><sub>机构: Stanford University<br>本文提出了 Agent Island，一个旨在解决静态基准测试饱和与污染问题的动态多代理博弈环境。通过让LLM代理在类似《幸存者》的环境中进行说服与竞争，该方法能够持续评估模型的战略交互能力。实验结果显示 GPT-5.5 具有显著优势，并揭示了模型间存在的提供商偏好偏见。该工作为追踪LLM在复杂多代理场景下的能力演进提供了新的工具和视角。</sub>| <div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)](https://arxiv.org/pdf/2605.04312v1)</div><div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)](summary/2026-05/2605.04312.md)  |
| <span style='display: inline-block; width: 42px;'>05-04</span> | **When Agents Handle Secrets: A Survey of Confidential Computing for Agentic AI**<br><sub>机构: Imperial College London<br>本文系统地梳理了机密计算在Agentic AI领域的应用现状与挑战。作者指出，随着AI代理承担更多自主任务，传统的软件层防御已不足以应对来自特权对手和复杂交互流程的安全威胁。通过引入TEE和远程认证，机密计算提供了硬件级的隔离和信任验证能力。然而，目前仍缺乏一个成熟的端到端框架来整合这些硬件原语，特别是在处理多代理协作认证和大规模GPU加速推理的性能优化方面仍存在六大开放挑战。该综述为未来构建生产级安全代理系统提供了重要的理论依据和技术路线图。</sub>| <div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)](https://arxiv.org/pdf/2605.03213v2)</div><div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)](summary/2026-05/2605.03213.md)  |
| <span style='display: inline-block; width: 42px;'>05-03</span> | **Coopetition-Gym v1: A Formally Grounded Platform for Mixed-Motive Multi-Agent Reinforcement Learning under Strategic Coopetition**<br><sub>机构: University of Toronto<br>Coopetition-Gym v1 为混合动机多智能体强化学习提供了一个形式化 grounded 的基准平台。通过解耦收益与奖励、校准历史案例以及提供全面的参考算法和数据集，该平台使得研究人员能够系统地研究战略竞合中的复杂动态，推动了 MARL 从理想化场景向更具现实意义的混合动机场景迈进。</sub>| <div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)](https://arxiv.org/pdf/2605.02063v1)</div><div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)](summary/2026-05/2605.02063.md) <div style='min-width:85px;'>[![GitHub](https://img.shields.io/badge/GitHub-View-brightgreen?logo=github)](https://github.com/vikpant/strategic-coopetition)</div> |
| <span style='display: inline-block; width: 42px;'>05-02</span> | **Feedback-Normalized Developer Memory for Reinforcement-Learning Coding Agents: A Safety-Gated MCP Architecture**<br><sub>机构: PythaLab, Yildiz Technical University<br>本文贡献了一个具有组件级证据和明确声明边界的可审计记忆控制架构，而非声称 universal 的编码智能体改进。它强调了在RL编码代理中，记忆管理需要结合严格的治理、离线评估和安全门控，以应对微小细节对训练稳定性和正确性的重大影响。</sub>| <div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)](https://arxiv.org/pdf/2605.01567v1)</div><div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)](summary/2026-05/2605.01567.md)  |
| <span style='display: inline-block; width: 42px;'>05-01</span> | **A Low-Latency Fraud Detection Layer for Detecting Adversarial Interaction Patterns in LLM-Powered Agents**<br><sub>机构: University of California, San Diego; UNC at Greensboro; Indiana University Bloomington<br>本文提出了一种互补的防御机制，即针对 LLM 智能体的低延迟欺诈检测层。通过从交互轨迹中提取结构化特征并使用轻量级机器学习模型，该方法解决了传统规则基方法在应对多轮渐进式攻击时的不足，以及 LLM 基检测方法延迟过高的问题。实验表明，交互级别的行为检测应成为 LLM 智能体部署时防御体系的核心组成部分。</sub>| <div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)](https://arxiv.org/pdf/2605.01143v1)</div><div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)](summary/2026-05/2605.01143.md)  |

---

### 04月

| &nbsp;Date&nbsp;&nbsp; | Paper | Links & Summary |
| --- | --- | --- |
| <span style='display: inline-block; width: 42px;'>04-30</span> | **Agentic AI for Trip Planning Optimization Application**<br><sub>本文针对智能车辆行程规划中从可行性向最优性转变的需求，解决了现有方法在优化能力和评估标准上的双重缺口。通过引入具备动态细化能力的编排式代理 AI 框架，以及提供确切最优解的 TOP 数据集，作者实现了比传统单代理及固定工作流多代理系统更优的性能，为行程规划优化提供了新的方法论和评估基准。</sub>| <div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)](https://arxiv.org/pdf/2605.00276v1)</div><div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)](summary/2026-04/2605.00276.md)  |
| <span style='display: inline-block; width: 42px;'>04-26</span> | **ClawTrace: Cost-Aware Tracing for LLM Agent Skill Distillation**<br><sub>机构: UC San Diego, Epsilla, Carnegie Mellon University<br>本文指出了当前 LLM Agent 技能蒸馏中忽视成本信号的缺陷，提出了 ClawTrace 追踪平台和 TraceCard 数据格式，解决了细粒度成本归因难题。基于此构建的 CostCraft 管道生成了保留、剪枝和修复三类技能补丁。研究揭示了剪枝规则在跨任务成本优化上的高效性与泛化能力（降低 32% 中位数成本），而保留规则可能存在过拟合风险。ClawTrace 作为开放基础设施发布，旨在推动成本敏感的 Agent 研究。</sub>| <div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)](https://arxiv.org/pdf/2604.23853v1)</div><div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)](summary/2026-04/2604.23853.md)  |
| <span style='display: inline-block; width: 42px;'>04-27</span> | **BenchGuard: Who Guards the Benchmarks? Automated Auditing of LLM Agent Benchmarks**<br><sub>机构: University of Washington, Phylo, Inc., Genentech, Inc.<br>本文提出了 BenchGuard，开创了将前沿 LLM 从被评估对象转变为评估基础设施主动验证者的新范式。通过自动化交叉验证基准测试的各个组成部分，BenchGuard 有效解决了基于执行的基准测试中普遍存在的隐性错误和噪声问题。实验结果表明，该方法不仅能高精度地复现专家发现的问题，还能以极低的成本揭示人工审查遗漏的重大缺陷，为 AI 辅助的基准测试开发提供了切实可行的解决方案。</sub>| <div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)](https://arxiv.org/pdf/2604.24955v1)</div><div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)](summary/2026-04/2604.24955.md)  |
| <span style='display: inline-block; width: 42px;'>04-24</span> | **FormalScience: Scalable Human-in-the-Loop Autoformalisation of Science with Agentic Code Generation in Lean**<br><sub>机构: University of Manchester, Idiap Research Institute, National Biomarker Centre<br>本文提出了 FormalScience，一个高效的人机协同自动形式化流水线，并构建了 FormalPhysics 数据集。研究不仅解决了物理学等科学领域因符号复杂性和语义漂移导致的自动形式化难题，还通过系统性分析揭示了 LLM 在科学推理形式化中的局限性。该工作为科学领域的可解释性验证和自动化事实核查提供了重要基础工具和基准。</sub>| <div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)](https://arxiv.org/pdf/2604.23002v1)</div><div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)](summary/2026-04/2604.23002.md) <div style='min-width:85px;'>[![GitHub](https://img.shields.io/badge/GitHub-View-brightgreen?logo=github)](https://github.com/jmeadows17/formal-science)</div> |
| <span style='display: inline-block; width: 42px;'>04-24</span> | **Superminds Test: Actively Evaluating Collective Intelligence of Agent Society via Probing Agents**<br><sub>机构: University of Maryland<br>Collective intelligence refers to the ability of a group to achieve outcomes beyond what any individual member can accomplish alone. As large language model agents scale to populations of millions, a key question arises: Does collective intelligence emerge spontaneously from scale? We present the first empirical evaluation of this question in a large-scale autonomous agent society.</sub>| <div style='min-width:85px;'>[![arXiv](https://img.shields.io/badge/arXiv-Paper-%23D2691E?logo=arxiv)](https://arxiv.org/pdf/2604.22452v1)</div><div style='min-width:85px;'>[![Summary](https://img.shields.io/badge/Sum.-Read-blue?logo=dependabot)](summary/2026-04/2604.22452.md)  |

---
<!-- paper-daily:readme:months:end -->

## Star History
<picture>
<source
    media="(prefers-color-scheme: dark)"
    srcset="
    https://api.star-history.com/svg?repos=xianshang33/llm-paper-daily&type=Date&theme=dark
    "
/>
<source
    media="(prefers-color-scheme: light)"
    srcset="
    https://api.star-history.com/svg?repos=xianshang33/llm-paper-daily&type=Date
    "
/>
<img
    alt="Star History Chart"
    src="https://api.star-history.com/svg?repos=xianshang33/llm-paper-daily&type=Date"
/>
</picture>
            
