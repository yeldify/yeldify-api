from fastapi import FastAPI
from src.infrastructure.web.api.v1.routes.despesas import router as despesas_router
from src.infrastructure.web.api.v1.routes.orcamentos import router as orcamentos_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Yeldify API",
        version="0.1.0",
        description="API for personal finance manager (budget + portfolio)",
    )
    app.include_router(despesas_router)
    app.include_router(orcamentos_router)
    return app

app = create_app()