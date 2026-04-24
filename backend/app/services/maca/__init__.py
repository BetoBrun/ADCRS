"""
Motor de Cálculo MACA — pacote público.

Exporta a API estável do motor, usada por:
  - app.api.v1.fia      (cálculo on-line ao receber FIA)
  - app.api.v1.maca     (recálculo batch, reavaliação)
  - app.services.consolidacao  (cálculos agregados)
  - app.services.rules         (motor de regras consome os resultados)
"""

from app.services.maca.engine import (
    Classe,
    ClausulaInclusao,
    ContextoAtivo,
    FatorInterdependencia,
    Indicadores,
    ResultadoMACA,
    ResultadoPilar,
    avaliar,
    calcular_fd,
    calcular_pfa,
    calcular_pfa_ajustado,
    calcular_pp,
    classificar,
    verificar_clausulas_inclusao_direta,
)

__all__ = [
    "Classe",
    "ClausulaInclusao",
    "ContextoAtivo",
    "FatorInterdependencia",
    "Indicadores",
    "ResultadoMACA",
    "ResultadoPilar",
    "avaliar",
    "calcular_fd",
    "calcular_pfa",
    "calcular_pfa_ajustado",
    "calcular_pp",
    "classificar",
    "verificar_clausulas_inclusao_direta",
]

__version__ = "1.0.0"
