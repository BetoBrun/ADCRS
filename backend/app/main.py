"""
ADCRS — Ambiente Digital de Criticidade e Resiliência Setorial
==============================================================

Aplicação FastAPI principal.

Endpoints expostos:
  /api/v1/fia          — Submissão e consulta de Fichas de Identificação de Ativo
  /api/v1/maca         — Execução e consulta do motor de cálculo MACA
  /api/v1/csac         — Catálogo Setorial de Ativos Críticos (consolidado)
  /api/v1/rules        — Motor de regras e insights automáticos
  /api/v1/insights     — Consulta de insights gerados
  /api/v1/qlik         — Exportação Qlik (OData e QVD)
  /api/v1/coleta       — Integração com sistema COLETA-ANATEL
  /api/v1/audit        — Trilha de auditoria

Documentação interativa: /docs  (Swagger)  e  /redoc
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import audit, coleta, csac, fia, insights, maca, qlik, rules
from app.core.config import settings
from app.core.logging import configurar_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialização e finalização da aplicação."""
    configurar_logging()
    # Aqui entrariam: conexão com banco, warm-up de cache, carga de regras YAML
    yield
    # Finalização graceful


app = FastAPI(
    title="ADCRS — Ambiente Digital de Criticidade e Resiliência Setorial",
    description=(
        "API do ADCRS, plataforma digital que operacionaliza a Metodologia de "
        "Joias da Coroa (MACA V2.0) para o setor de telecomunicações brasileiro, "
        "em conformidade com a Resolução ANATEL nº 740/2020 e o NIST CSF 2.0."
    ),
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "GT-Ciber / ANATEL",
        "url": "https://www.anatel.gov.br",
    },
    license_info={
        "name": "MIT",
    },
)


# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Roteadores ---
app.include_router(fia.router, prefix="/api/v1/fia", tags=["FIA"])
app.include_router(maca.router, prefix="/api/v1/maca", tags=["MACA"])
app.include_router(csac.router, prefix="/api/v1/csac", tags=["CSAC"])
app.include_router(rules.router, prefix="/api/v1/rules", tags=["Regras"])
app.include_router(insights.router, prefix="/api/v1/insights", tags=["Insights"])
app.include_router(qlik.router, prefix="/api/v1/qlik", tags=["Qlik Sense"])
app.include_router(coleta.router, prefix="/api/v1/coleta", tags=["COLETA-ANATEL"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Auditoria"])


@app.get("/", include_in_schema=False)
async def raiz():
    """Página de boas-vindas."""
    return {
        "sistema": "ADCRS",
        "versao": "1.0.0",
        "documentacao": "/docs",
        "metodologia": "Joias da Coroa — IC Telecom V2.0",
    }


@app.get("/health", tags=["Saúde"])
async def health():
    """Endpoint de liveness / readiness para Kubernetes."""
    return {"status": "ok"}
