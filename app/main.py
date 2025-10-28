from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import router as auth_router
from app.files.router import router as files_router
from app.questions.router import router as questions_router
from app.tests.router import router as tests_router
from app.questions.router import router as questions_router
app = FastAPI(title="Lecture & Exam Manager API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
@app.get("/healthz")
async def healthz(): return {"ok": True}
app.include_router(auth_router)
app.include_router(files_router)
app.include_router(questions_router)
app.include_router(tests_router)


from fastapi import Depends
from app.deps import get_current_user
from app.db.models import User

@app.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="Lecture & Exam Manager API",
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    for path in openapi_schema.get("paths", {}).values():
        for method in path.values():
            method.setdefault("security", [{"bearerAuth": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
