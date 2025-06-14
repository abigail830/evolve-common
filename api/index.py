from fastapi import FastAPI
# from .endpoints import documents, agents
from api.endpoints import documents

app = FastAPI(
    title="Evolve Common Service",
    description="A common service for document processing, AI agents, and more.",
    version="0.1.0",
)

# Health check endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Evolve Common Service API"}

# Include routers from endpoints
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
# app.include_router(agents.router, prefix="/api/v1") 