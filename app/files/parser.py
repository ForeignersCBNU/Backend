from __future__ import annotations
from pathlib import Path
from collections import Counter
import re
from typing import Iterable
import fitz  # PyMuPDF
from docx import Document
from sqlalchemy import select, delete
from app.db.session import SessionLocal
from app.db.models import UploadedFile, Concept, Question, QType
from datetime import datetime

STOP = set("""
the of and to a in is it you that he was for on are with as I his they be at one
have this from or had by hot but some what there we can out other were all your
when up use word how said an each she which do their time if will way about many
then them write would like so these her long make thing see him two has look more
day could go come did number sound no most people my over know water than call
first who may down side been now find any new work part
""".split())

def _clean_tokens(text: str) -> Iterable[str]:
    for w in re.findall(r"[A-Za-z][A-Za-z\-]{2,}", text.lower()):
        if w not in STOP:
            yield w

def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".pdf":
        txt = []
        with fitz.open(path) as doc:
            for page in doc:
                txt.append(page.get_text())
        return "\n".join(txt)
    if ext == ".docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    try:
        return path.read_text(errors="ignore")
    except Exception:
        return ""

async def parse_and_store(file_id: str) -> None:
    async with SessionLocal() as s:
        uf = (await s.execute(select(UploadedFile).where(UploadedFile.id == file_id))).scalar_one_or_none()
        if not uf:
            return
        try:
            uf.ai_status = "parsing"
            await s.commit()

            text = extract_text(Path(uf.file_path)).strip()
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            summary = " ".join(lines)[:400] if lines else ""

            tokens = list(_clean_tokens(text))[:20000]
            common = [w for w, _ in Counter(tokens).most_common(8)]

            await s.execute(delete(Concept).where(Concept.file_id == uf.id))

            concepts = []
            for kw in common[:5]:
                c = Concept(file_id=uf.id, keyword=kw, description=f"Key term: {kw}", importance=3)
                s.add(c); concepts.append(c)
            await s.flush()

            if concepts:
                q = Question(
                    concept_id=concepts[0].id,
                    question_type=QType.mcq,
                    question_text="What is 2 + 2?",
                    correct_answer="4",
                    options={"A": "3", "B": "4", "C": "5", "D": "22"},
                    difficulty=1,
                    created_at=datetime.utcnow(),
                )
                s.add(q)

            uf.summary = summary or "No summary available."
            uf.ai_status = "parsed"
            await s.commit()
        except Exception:
            uf.ai_status = "error"
            await s.commit()
