from fastapi import FastAPI

from app.api.books import router as books_router
from app.api.categories import router as categories_router
from app.api.scrape_runs import router as scrape_runs_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.include_router(books_router)
app.include_router(categories_router)
app.include_router(scrape_runs_router)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": settings.app_env,
    }
