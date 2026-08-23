from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/healthz")
async def healthz():
    """Liveness probe endpoint."""
    return {"status": "ok", "version": "6.2.2"}

