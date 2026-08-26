from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.seed import router as seed_router
from app.api.policies import router as policies_router
from app.api.clips import router as clips_router
from app.api.scenes import router as scenes_router
from app.api.analysis import router as analysis_router

app = FastAPI(
    title="SceneRights AI API",
    version="6.2.2",
    description="Agentic Cinema Hackathon — Production Supervisor API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Uniform error envelope handler conforming to Master Spec §39 & §45."""
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "ERROR",
                "message": str(exc.detail),
                "retryable": False,
                "details": {}
            }
        }
    )


app.include_router(seed_router)
app.include_router(policies_router)
app.include_router(clips_router)
app.include_router(scenes_router)
app.include_router(analysis_router)


@app.get("/healthz")
async def healthz():
    """Liveness probe endpoint."""
    return {"status": "ok", "version": "6.2.2"}
