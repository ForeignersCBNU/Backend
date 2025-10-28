from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from sqlalchemy import select
from app.db.session import SessionLocal
from app.db.models import Test, TestItem, Question

async def build_test_pdf(test_id: str, with_answers: bool = False) -> bytes:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    async with SessionLocal() as s:
        test = (await s.execute(select(Test).where(Test.id == test_id))).scalar_one_or_none()
        rows = (await s.execute(
            select(TestItem, Question)
            .join(Question, Question.id == TestItem.question_id)
            .where(TestItem.test_id == test_id)
        )).all()

    y = height - 2*cm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, y, f"Test ID: {test_id}")
    y -= 1.2*cm
    c.setFont("Helvetica", 11)

    qnum = 1
    for _, q in rows:
        text = f"{qnum}. {q.question_text}"
        c.drawString(2*cm, y, text[:1000])
        y -= 0.8*cm

        if q.options:
            # print options in A/B/C/D order when available
            for key in sorted(q.options.keys()):
                c.drawString(2.5*cm, y, f"{key}) {q.options[key]}")
                y -= 0.7*cm

        # answer line
        c.line(2*cm, y, width-2*cm, y)
        y -= 0.8*cm
        if with_answers and getattr(q, 'correct_answer', None):
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(2*cm, y, f"Answer: {q.correct_answer}")
            c.setFont("Helvetica", 11)
            y -= 0.6*cm

        if y < 3*cm:
            c.showPage()
            y = height - 2*cm
            c.setFont("Helvetica", 11)

        qnum += 1

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
