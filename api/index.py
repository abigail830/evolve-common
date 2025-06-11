from fastapi import FastAPI
# from .endpoints import documents, agents

app = FastAPI(
    title="Evolve Common Service",
    description="A common service for document processing, AI agents, and more.",
    version="0.1.0",
)

# Health check endpoint
@app.get("/health")
def read_root():
    return {"status": "ok"}

# Include routers from endpoints
# app.include_router(documents.router, prefix="/api/v1")
# app.include_router(agents.router, prefix="/api/v1") 