from fastapi import FastAPI
from routers.relatorio_router import router as relatorio_router

app = FastAPI(title="Microservice Relatório de Confirmação")

app.include_router(relatorio_router)
