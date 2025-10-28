
# --- grading helpers ---------------------------------------------------------
def _normalize_text(s: str) -> str:
    # trim, collapse whitespace, lowercase
    return " ".join((s or "").split()).strip().lower()

def grade_short_answer(answer: str, correct: str) -> bool:
    return _normalize_text(answer) == _normalize_text(correct)

def grade_mcq(answer: str, correct: str, options: dict | None) -> bool:
    # if user sent an option key like "B", map it to the option text
    if isinstance(options, dict) and answer in options:
        answer_text = str(options[answer])
    else:
        answer_text = str(answer)
    return _normalize_text(answer_text) == _normalize_text(correct)
# ----------------------------------------------------------------------------- 

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import select, func
from app.db.session import SessionLocal
from app.db.models import User, Test, TestItem, Answer, Question, Concept
from app.deps import get_current_user

router = APIRouter(prefix="/tests", tags=["tests"])

class CreateTestIn(BaseModel):
    file_id: str
    num_questions: int = 5
    difficulty: int | None = None

@router.post("/create")
async def create_test(body: CreateTestIn, user: User = Depends(get_current_user)):
    async with SessionLocal() as s:
        q = (select(Question)
             .join(Concept, Question.concept_id == Concept.id)
             .where(Concept.file_id == body.file_id))
        if body.difficulty:
            q = q.where(Question.difficulty == body.difficulty)
        q = q.order_by(func.random()).limit(body.num_questions)
        rows = (await s.execute(q)).scalars().all()
        if not rows:
            raise HTTPException(404, "No questions found for this file")

        test = Test(user_id=user.id, test_date=datetime.utcnow(),
                    total_questions=len(rows), correct_count=0, score=0.0)
        s.add(test); await s.flush()

        items = []
        for ques in rows:
            s.add(TestItem(test_id=test.id, question_id=ques.id))
            items.append({
                "question_id": ques.id,
                "type": ques.question_type.value,
                "question_text": ques.question_text,
                "options": ques.options,
                "difficulty": ques.difficulty
            })
        await s.commit()
        return {"test_id": test.id, "total_questions": test.total_questions, "items": items}

# IMPORTANT: define /mine BEFORE /{test_id}
@router.get("/mine")
async def list_my_tests(user: User = Depends(get_current_user)):
    async with SessionLocal() as s:
        tests = (await s.execute(
            select(Test).where(Test.user_id == user.id).order_by(Test.created_at.desc())
        )).scalars().all()
        return [{"id": t.id, "date": t.test_date.isoformat(),
                 "total": t.total_questions, "correct": t.correct_count, "score": t.score}
                for t in tests]

@router.get("/{test_id}")
async def get_test(test_id: str, user: User = Depends(get_current_user)):
    async with SessionLocal() as s:
        test = (await s.execute(
            select(Test).where(Test.id == test_id, Test.user_id == user.id)
        )).scalar_one_or_none()
        if not test:
            raise HTTPException(404, "Test not found")
        rows = (await s.execute(
            select(TestItem, Question)
            .join(Question, Question.id == TestItem.question_id)
            .where(TestItem.test_id == test_id)
        )).all()
        items = [{
            "question_id": q.id,
            "type": q.question_type.value,
            "question_text": q.question_text,
            "options": q.options,
            "difficulty": q.difficulty
        } for _, q in rows]
        return {
            "test_id": test.id,
            "test_date": test.test_date.isoformat(),
            "total_questions": test.total_questions,
            "correct_count": test.correct_count,
            "score": test.score,
            "items": items
        }

class SubmitIn(BaseModel):
    answers: List[Dict[str, Any]]

@router.post("/{test_id}/submit")
async def submit_test(test_id: str, body: SubmitIn, user: User = Depends(get_current_user)):
    async with SessionLocal() as s:
        test = (await s.execute(
            select(Test).where(Test.id == test_id, Test.user_id == user.id)
        )).scalar_one_or_none()
        if not test:
            raise HTTPException(404, "Test not found")

        rows = (await s.execute(
            select(TestItem, Question)
            .join(Question, Question.id == TestItem.question_id)
            .where(TestItem.test_id == test_id)
        )).all()
        qmap = {q.id: q for _, q in rows}

        correct = 0
        for a in body.answers:
            qid = a.get("question_id"); ans = str(a.get("answer", "")).strip()
            q = qmap.get(qid)
            if not q:
                continue
            ok = grade_mcq(ans, q.correct_answer or "", q.options) if q.question_type.name == "mcq" or str(q.question_type) in ("mcq","QType.mcq") else grade_short_answer(ans, q.correct_answer or "")
            if ok: correct += 1
            s.add(Answer(test_id=test.id, question_id=qid, user_answer=ans, is_correct=ok))

        total = test.total_questions or 0
        test.correct_count = correct
        test.score = float((correct / total) * 100.0) if total else 0.0
        await s.commit()
        return {"test_id": test.id, "correct": correct, "total": total, "score": test.score}


from fastapi.responses import StreamingResponse
from app.tests.export import build_test_pdf

@router.get("/{test_id}/export.pdf")
async def export_test_pdf(test_id: str, with_answers: bool = False, user: User = Depends(get_current_user)):
    # reuse the auth/ownership check in get_test:
    async with SessionLocal() as s:
        test = (await s.execute(
            select(Test).where(Test.id == test_id, Test.user_id == user.id)
        )).scalar_one_or_none()
        if not test:
            raise HTTPException(404, "Test not found")

    data = await build_test_pdf(test_id, with_answers=with_answers)
    return StreamingResponse(iter([data]),
                             media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename=test_{test_id}.pdf"})
