"""题目分类器：基于关键词/结构的确定性题型判定。

对应 starter kit 中 classify.py 的迁移版本；用于把题面路由到合适的求解器。
若无法判定，返回 "unknown"，交由 LLM 兜底路径处理。
"""
from __future__ import annotations

import re

_RULES = [
    ("linear_system", r"线性方程组|方程组|求解\s*[xyz]|联立"),
    ("eigen", r"特征值|特征向量|eigen"),
    ("determinant", r"行列式|determinant|\bdet\b"),
    ("matrix_product", r"矩阵乘法|乘积|相乘|转置|B\^T|BC"),
    ("binomial", r"二项分布|恰好答对|恰好有|至少答对|binomial"),
    ("normal", r"正态分布|正态|N\s*\(\s*\d|标准差"),
]


def classify(text: str) -> str:
    for kind, pat in _RULES:
        if re.search(pat, text, re.I):
            return kind
    return "unknown"
