from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.config import settings
from app.database import create_db_and_tables
from app.llm.client import OllamaClient
from app.llm.pipeline import GradingPipeline
from app.routers import student, teacher

app_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.load_questionnaires()
    create_db_and_tables()

    client = OllamaClient(settings.ollama_base_url, settings.ollama_model)
    pipeline = GradingPipeline(client, settings.questionnaires)

    app_state["questionnaires"] = settings.questionnaires
    app_state["pipeline"] = pipeline
    app_state["ollama_client"] = client

    yield
    app_state.clear()


app = FastAPI(title="EQ改作業小幫手", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(student.router)
app.include_router(teacher.router)


@app.get("/health")
async def health():
    client: OllamaClient = app_state.get("ollama_client")
    ollama_ok = await client.health_check() if client else False
    return {
        "status": "ok" if ollama_ok else "degraded",
        "ollama": ollama_ok,
        "questionnaires_loaded": len(app_state.get("questionnaires", {})),
    }
