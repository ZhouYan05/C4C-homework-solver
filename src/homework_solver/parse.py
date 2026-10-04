"""题面解析：把摄取到的整页文本切分为结构化题目列表。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from .classify import classify


@dataclass
class Problem:
    id: str
    title: str
    statement: str
    kind: str = field(default="")


_HEAD_PAT = re.compile(r"^#{2,3}\s*(?:第\s*)?(\d+)\s*题.*$", re.M)


def split_problems(text: str) -> List[Problem]:
    """按 `## 第N题` 标题切分；无标题时回退为按空行分段。"""
    matches = list(_HEAD_PAT.finditer(text))
    problems: List[Problem] = []
    if matches:
        for i, m in enumerate(matches):
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()
            pid = m.group(1)
            title = text[m.start():m.end()].lstrip("#").strip()
            problems.append(Problem(id=pid, title=title, statement=body, kind=classify(body)))
    else:
        chunks = [c.strip() for c in re.split(r"\n\s*\n", text) if c.strip()]
        for i, c in enumerate(chunks, 1):
            problems.append(Problem(id=str(i), title=f"第{i}题", statement=c, kind=classify(c)))
    return problems
