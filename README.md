 Lecture-Exam Backend (FastAPI)
 Overview
This project is a FastAPI-based backend for managing lectures, exam materials, and auto-graded tests.
It provides RESTful APIs for authentication, file upload/parsing, and question management.
⚙️ Tech Stack
Backend Framework: FastAPI (Python 3.10+)
Database: PostgreSQL / MySQL (via SQLAlchemy & Alembic)
ORM: SQLAlchemy + Alembic migrations
Auth: JWT (JSON Web Token)
File Parser: PyMuPDF / python-docx
Deployment: Uvicorn + Docker (optional)
📁 Project Structure
app/
 ├── auth/           # login, register, JWT
 ├── core/           # settings & configuration
 ├── db/             # database session and models
 ├── files/          # PDF/DOCX file parsing
 ├── questions/      # question & exam logic
 ├── tests/          # grading, export, testing routes
 └── main.py         # FastAPI entry point
 How to Run Locally
# 1. Clone repo
git clone https://github.com/ForeignersCBNU/Backend.git
cd Backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate.bat  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run server
uvicorn app.main:app --reload
Then open 👉 http://127.0.0.1:8000/docs to test the API.
 Environment Variables (.env)
DATABASE_URL=postgresql://user:password@localhost:5432/lecture_exam
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
  Example Features
Upload lecture/exam PDFs → parse → store in DB
Auto-grading for simple questions
Export results in DOCX or JSON
User authentication and role-based access
  Future Plans
Add student dashboard (frontend)
Integrate AI question generation
Add admin analytics
