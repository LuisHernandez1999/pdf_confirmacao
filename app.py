from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers.relatorio_router import router as relatorio_router

app = FastAPI(title="Microservice Relatório de Confirmação")

# ----------------------------------------------------
# CORS CONFIGURADO PARA NEXT.JS
# ----------------------------------------------------
origins = [
    "http://localhost:3000",       # Next.js local
    "http://127.0.0.1:3000",
    # "*",  # só use em DEV se quiser liberar geral
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],      # <- PERMITE OPTIONS (pré-flight)
    allow_headers=["*"],      # <- permite JSON, Authorization etc.
)

# ----------------------------------------------------
# ROTAS
# ----------------------------------------------------
app.include_router(relatorio_router)
