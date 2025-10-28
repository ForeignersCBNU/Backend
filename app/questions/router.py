from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Concept, Question, UploadedFile, QType
from datetime import datetime

router = APIRouter(prefix="/questions", tags=["questions"])

@router.post("/generate/{file_id}")
async def generate_questions(file_id: str):
    async with SessionLocal() as s:
        file = (await s.execute(select(UploadedFile).where(UploadedFile.id == file_id))).scalar_one_or_none()
        if not file:
            raise HTTPException(404, "file not found")
        concept = (await s.execute(select(Concept).where(Concept.file_id == file_id))).scalar_one_or_none()
        if not concept:
            concept = Concept(file_id=file_id, keyword="demo", description="demo concept", importance=3)
            s.add(concept)
            await s.flush()
        q = Question(
            concept_id=concept.id,
            question_type=QType.mcq,
            question_text="What is 2 + 2?",
            correct_answer="4",
            options={"A":"3","B":"4","C":"5","D":"22"},
            difficulty=1,
            created_at=datetime.utcnow(),
        )
        s.add(q)
        await s.commit()
        return {"status":"ok","file_id":file_id,"concept_id":concept.id,"question_id":q.id}

@router.get("/by-file/{file_id}")
async def list_by_file(file_id: str):
    async with SessionLocal() as s:
        result = await s.execute(
            select(Concept, Question)
            .join(Question, Question.concept_id == Concept.id, isouter=True)
            .where(Concept.file_id == file_id)
        )
        items = []
        for c, q in result.all():
            items.append({
                "concept_id": c.id,
                "keyword": c.keyword,
                "question_id": getattr(q, "id", None) if q else None,
                "question_text": getattr(q, "question_text", None) if q else None,
                "difficulty": getattr(q, "difficulty", None) if q else None,
            })
        return {"items": items}
