"""多格式摄取：把作业原件（md/txt/pdf/docx/图片）统一读成文本。

starter kit 中 ingest.py 仅实现了 read_markdown，其它为扩展点；
本版本把 PDF / DOCX / 图片 OCR 三个扩展点补齐，并保留可插拔的
"国产模型 Vision" 分支用于扫描件。
"""
from __future__ import annotations

from pathlib import Path


def read_markdown(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def read_pdf_text(path: str) -> str:
    """用 pdfplumber 抽取文本层；扫描件请走 read_image_ocr / 模型 Vision。"""
    import pdfplumber

    out = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            out.append(f"<!-- page {i} -->\n" + (page.extract_text() or ""))
    return "\n".join(out)


def read_docx(path: str) -> str:
    import docx

    d = docx.Document(path)
    return "\n".join(p.text for p in d.paragraphs)


def read_image_ocr(path: str, lang: str = "chi_sim+eng") -> str:
    """Tesseract OCR（需本机安装 tesseract 及对应语言包）。"""
    import pytesseract
    from PIL import Image

    return pytesseract.image_to_string(Image.open(path), lang=lang)


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


FORMAT_HANDLERS = {
    ".md": read_markdown,
    ".markdown": read_markdown,
    ".txt": read_text,
    ".pdf": read_pdf_text,
    ".docx": read_docx,
    ".png": read_image_ocr,
    ".jpg": read_image_ocr,
    ".jpeg": read_image_ocr,
}


def ingest(path: str) -> str:
    ext = Path(path).suffix.lower()
    handler = FORMAT_HANDLERS.get(ext)
    if handler is None:
        raise ValueError(f"不支持的文件格式: {ext}")
    return handler(path)
