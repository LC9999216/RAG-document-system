import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

from app.api.routes import router
from app.core.errors import register_exception_handlers


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("RAG 服务启动中...")
    yield
    print("RAG 服务关闭中...")


app = FastAPI(
    title="RAG 文档问答系统",
    description="基于 LangGraph 和 DeepSeek 的 RAG 文档问答 API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(router, prefix="/api/v1")

static_path = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=True
    )
