# ZhouYan_C4C_AI日志

> 本日志如实记录本次作业中 **AI（Claude Code / Commander 智能体）做了什么、人做了什么、遇到什么问题、怎么解决的**。
> 未做的事如实标注为"未做/未验证"，不美化。

## 一、协作方式

- **人**：确定挑战目标、选择非微积分题型（线性代数 + 概率论）、提供作业原件、审核交付物、决定提交。
- **AI**：阅读挑战要求与 rubric、搭建项目骨架、编写与调试求解器 / 核验层 / LaTeX 渲染、
  跑通端到端流水线、排查真实编译错误、撰写文档、组装仓库。

## 二、时间线（关键节点）

1. **读题**：解析 C4C 挑战正文、rubric（总分 100：solverQuality 25 / typesetting 20 /
   artifactCompleteness 15 / aiUsage 20 / reflectionQuality 20）与 4 项交付物要求。
2. **搭骨架**：从 starter kit 出发，重构为 `src/homework_solver/` 包结构（ingest / parse /
   classify / solvers / verify / llm / render / pipeline / cli）。
3. **实现求解器**：为线性方程组、特征值、行列式、矩阵运算、二项分布、正态分布各写一个
   SymPy 求解器。
4. **实现核验层**：为每类题型写一条**独立原理**的复算路径。
5. **调试真实 bug**（详见第三节）。
6. **跑通流水线**：6/6 题核验通过，PDF 编译成功（5 页）。
7. **产出文档与仓库**：README、CI、SKILL.md、方案设计、验证报告、教学说明、本日志。

## 三、AI 遇到并修复的真实问题（重点）

### 1. `verify.py` 里对 SymPy 符号排序报错

**现象**：`sorted(symbols)` 在涉及 `Relational`（如 `x < y`）时报
`cannot determine truth value of Relational`。
**修复**：`_unknowns()` 改为 `key=lambda s: str(s)`，按字符串排序，规避符号比较。

### 2. `solvers.py` 对解集字典直接 `sp.latex(sol[0])` 不安全

**现象**：解是 dict 时 `latex` 输出不稳定、语义错乱。
**修复**：显式拼接 `k=v` 的 `sol_tex`；矩阵转置展示改为 `sp.latex(B) + "^{T}=" + sp.latex(BT)`。

### 3. xelatex 连续三次 `! Missing $ inserted`（最耗时）

- 第 1 次：`l.33 \begin{cases}` —— 题面里裸写的 display 环境没有数学定界符。
  **修复**：新增 `latex_utils.normalize_math()`，把裸的 display 环境用 `\[...\]` 包裹、
  把裸行内 `^ _ \` 片段用 `$...$` 包裹，并用占位符保护已写好的 `$` / `\[` / `\(`。
- 第 2 次：`l.64 \begin{answerbox}\textbf{答案：}\; \lambda_1=...` —— 答案框里直接放了裸数学。
  **修复**：`answer_latex` 在 `answerbox` 内用 `\[ %s \]` 包裹。
- 第 3 次：`l.90 \textbf{转置 B^T}` —— 步骤标签里含 `^`。
  **修复**：步骤标签统一过 `lu.normalize_math(st["label"])`。
- 补充：`render.py` 补 `from . import latex_utils as lu`。

### 4. PowerShell 的 `> $null` 被拒

**现象**：`E_BASH_DYNAMIC_PATH_UNSUPPORTED`。
**修复**：改用 `| Out-Null`。

### 5. 环境无 LLM 密钥

**现象**：`DASHSCOPE / MOONSHOT / DEEPSEEK / OPENAI / ANTHROPIC` 密钥检测全为 False。
**处理**：流水线**自动降级**为纯确定性模式，`llm_backend` 记为 `qwen(disabled:no-key)`，
不抛异常。**因此本次未实际运行 Qwen/Kimi/Claude 的多模型对比**——这是已知缺口，如实记录。

## 四、AI 没有做的 / 未验证的

- ❌ **未运行** Qwen vs Kimi vs Claude 多模型对比实验（缺 API 密钥）。
- ❌ **未验证** PDF / DOCX / 图片 OCR 摄入路径（本机未装对应可选依赖）。
- ❌ **未做** 像素级版式回归（仅确认编译通过）。
- ⚠️ 只覆盖 6 类题型；ODE、物理公式等超纲题未实现。

## 五、人机分工小结

AI 承担了绝大部分编码与调试，但**关键判断由人做出**：选哪种题型、什么算"通过核验"、
是否接受"无密钥降级"的结论、以及最终是否提交。AI 的价值在于把重复、易错的调试
（尤其是三轮 LaTeX 报错）快速收敛；人的价值在于设定正确性标准与边界。
