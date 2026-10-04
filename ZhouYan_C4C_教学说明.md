# ZhouYan_C4C_教学说明

## 一、这份文档给谁看

给**想复现或理解本作业求解器**的同学 / 教师。它会讲清楚：
这个工具怎么用、它的正确性靠什么保证、它会在哪里出错、以及你应该怎么"教"别人用。

## 二、这个求解器在做什么

一句话：**给一份作业，自动生成带完整步骤、可核验、排版规范的中文解答 PDF。**

它不是"把题目丢给 AI 让它写答案"，而是：
1. 把题目**结构化**（切题、分类）；
2. 用**符号数学引擎**精确求解（不是概率性生成）；
3. 用**另一条独立路径**把答案复算一遍；
4. 只有核验通过，才排进 PDF。

## 三、怎么用（三步）

### 第 1 步：装依赖

```bash
pip install -r requirements.txt
# 如需 pdf/docx/图片摄入，再装：pip install pdfplumber python-docx pytesseract Pillow
```

### 第 2 步：跑一条命令

```bash
PYTHONPATH=src python -m homework_solver.cli \
    --input examples/homework_linalg_prob.md \
    --outdir out --title "作业解答" --author "你的名字"
```

Windows PowerShell 必须带 `$env:PYTHONPATH="src";`，否则会 `ModuleNotFoundError`。

### 第 3 步：看结果

- `out/homework.pdf` —— 排版好的解答。
- `out/report.json` —— **先看这个**：`verified/total` 告诉你几道题核验通过。

## 四、怎么判断它做对了（教学重点）

**不要因为 PDF 好看就认为答案对。** 判断正确性的唯一依据是 `report.json`：

```json
{ "total": 6, "verified": 6, "accuracy": 1.0 }
```

- `verified == total` → 每题都通过了独立核验。
- 某题 `verified:false` → 该题**未通过**，PDF 中会标注，请人工复核，**不要直接交**。

核验为什么可信？因为它是**原理不同**的第二条路径，例如：
- 方程组：把解**代回原方程**看残差是否为 0；
- 特征值：检查 `trace = Σλ` 与 `det = Πλ` 是否同时成立；
- 行列式：`Matrix.det` 与 LU 分解结果对比。

同一方法算两次不算核验；两条不同原理互相印证才算。

## 五、常见坑与排查

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| `ModuleNotFoundError: homework_solver` | 没设 PYTHONPATH | 加 `PYTHONPATH=src` / `$env:PYTHONPATH="src"` |
| `! Missing $ inserted` | 题面里有裸的数学片段 | 已在 `latex_utils.normalize_math()` 处理；如是新题型请补充规则 |
| PDF 没生成 | 没有 xelatex / ctex | 装 MiKTeX 或 TeX Live，确保 `xelatex` 在 PATH |
| 答案对但 `verified:false` | 核验路径未覆盖该题型 | 为新题型增加独立核验，勿直接放行 |
| `llm_backend: qwen(disabled:no-key)` | 没配密钥 | 配 `DASHSCOPE_API_KEY` 等；不配也能跑确定性题 |

## 六、边界：它做不到什么

- 只覆盖有限题型（线代 + 概率论 6 类）；ODE、物理公式等未实现。
- 未配 LLM 密钥时，超纲题无法兜底，会标为待人工复核。
- 符号引擎对超复杂表达式可能很慢或不化简。
- 图像 OCR / 扫描件依赖可选依赖，未在本机验证。

## 七、可以怎么扩展（给学生）

1. 新增一个题型：在 `solvers.py` 注册求解器 + 在 `verify.py` 加一条**独立**核验。
2. 接入国产大模型：配好密钥后跑一遍超纲题，对比"LLM 直出"与"符号 + 核验"的差异。
3. 做多模型对比实验：Qwen / Kimi / DeepSeek 各跑同一批题，统计准确率。
