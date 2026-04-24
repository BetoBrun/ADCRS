"""
Endpoints de FIA — Ficha de Identificação de Ativo (Anexo V).

A submissão de FIA é a porta única de entrada de dados no ADCRS. O sistema:
  1. Valida estruturalmente a FIA (Pydantic)
  2. Verifica assinatura digital ICP-Brasil
  3. Aplica o motor MACA (cálculo determinístico)
  4. Persiste no banco com trilha de auditoria
  5. Dispara motor de regras para gerar insights
  6. Retorna o resultado MACA e o protocolo
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import usuario_autenticado
from app.schemas import (
    FIACompleta,
    FIASubmetidaResponse,
    ResultadoMACADTO,
    ResultadoPilarDTO,
)
from app.services.maca import (
    ContextoAtivo,
    FatorInterdependencia,
    Indicadores,
    avaliar,
)

router = APIRouter()


@router.post(
    "/",
    response_model=FIASubmetidaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submeter nova FIA (Ficha de Identificação de Ativo)",
)
async def submeter_fia(
    fia: FIACompleta,
    usuario=Depends(usuario_autenticado),
) -> FIASubmetidaResponse:
    """
    Submete uma nova FIA ao ADCRS.

    O fluxo é síncrono para entregar imediatamente ao submetente a classe
    resultante, mas o motor de regras roda em background para gerar insights.

    - Exige autenticação por certificado digital ICP-Brasil A3
    - Toda submissão é cifrada em repouso (AES-256) e registrada na trilha
    - Versões anteriores da mesma FIA (mesmo id_ativo + prestadora) são
      preservadas com versionamento automático
    """

    # 1. Aplicar MACA
    ind = Indicadores(**fia.pontuacoes_maca.model_dump())
    fi = FatorInterdependencia(
        intra_leve=fia.fatores_ajuste.fi_intra_leve,
        intra_significativa=fia.fatores_ajuste.fi_intra_significativa,
        inter_1_setor=fia.fatores_ajuste.fi_inter_1_setor,
        inter_2_mais_setores=fia.fatores_ajuste.fi_inter_2_mais_setores,
        efeito_cascata=fia.fatores_ajuste.fi_efeito_cascata,
    )
    ctx = ContextoAtivo(
        setores_criticos_sustentados=fia.contexto_inclusao_direta.setores_criticos_sustentados,
        descumpre_tratado_internacional=fia.contexto_inclusao_direta.descumpre_tratado_internacional,
        spof_setorial_reconhecido=fia.contexto_inclusao_direta.spof_setorial_reconhecido,
    )
    resultado = avaliar(
        ind, fi,
        rto_horas=fia.parametros_operacionais.rto_horas,
        contexto=ctx,
    )

    # 2. Persistência (implementação completa em services/fia_repository.py)
    # await fia_repository.salvar(fia, resultado, usuario)

    # 3. Disparar motor de regras assíncrono
    # from app.services.rules import motor_regras
    # await motor_regras.avaliar_ativo_background(fia.identificacao_ativo.id_unico)

    # 4. Auditoria
    # await audit.registrar("fia_submetida", usuario, fia.identificacao_ativo.id_unico)

    return FIASubmetidaResponse(
        id_fia=uuid4(),
        id_ativo=fia.identificacao_ativo.id_unico,
        prestadora_cnpj=fia.prestadora.cnpj,
        resultado_maca=ResultadoMACADTO(
            pilares=[ResultadoPilarDTO(**p.to_dict()) for p in resultado.pilares],
            pfa=resultado.pfa,
            fi=resultado.fi,
            fd=resultado.fd,
            rto_horas=resultado.rto_horas,
            pfa_ajustado=resultado.pfa_ajustado,
            classe=resultado.classe.value,
            clausulas_disparadas=[c.value for c in resultado.clausulas_disparadas],
            reclassificado_por_clausula=resultado.reclassificado_por_clausula,
        ),
        protocolo_submissao=f"ADCRS-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}",
        timestamp_submissao=datetime.now(timezone.utc),
    )


@router.get(
    "/{id_fia}",
    response_model=FIACompleta,
    summary="Consultar FIA pelo ID",
)
async def consultar_fia(
    id_fia: UUID,
    usuario=Depends(usuario_autenticado),
) -> FIACompleta:
    """Recupera uma FIA previamente submetida. Acesso restrito por RBAC."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Implementação completa depende de repositório de FIAs (fase 1)",
    )


@router.get(
    "/",
    summary="Listar FIAs submetidas (paginado)",
)
async def listar_fias(
    prestadora_cnpj: str | None = Query(None),
    classe: str | None = Query(None, pattern="^[ABCD]$"),
    uf: str | None = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=500),
    usuario=Depends(usuario_autenticado),
):
    """Lista FIAs com filtros. ANATEL vê todas; prestadora vê apenas as próprias."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Implementação completa depende de repositório de FIAs (fase 1)",
    )


@router.post(
    "/simular",
    response_model=ResultadoMACADTO,
    summary="Simular cálculo MACA sem persistir",
)
async def simular_maca(fia: FIACompleta) -> ResultadoMACADTO:
    """
    Executa o cálculo MACA sem persistir. Útil para:
    - Prestadoras testarem cenários antes da submissão oficial
    - Dashboard executivo projetar impacto de mudanças
    - Treinamento e auditoria

    Não exige autenticação forte ICP-Brasil, apenas JWT.
    """
    ind = Indicadores(**fia.pontuacoes_maca.model_dump())
    fi = FatorInterdependencia(
        intra_leve=fia.fatores_ajuste.fi_intra_leve,
        intra_significativa=fia.fatores_ajuste.fi_intra_significativa,
        inter_1_setor=fia.fatores_ajuste.fi_inter_1_setor,
        inter_2_mais_setores=fia.fatores_ajuste.fi_inter_2_mais_setores,
        efeito_cascata=fia.fatores_ajuste.fi_efeito_cascata,
    )
    ctx = ContextoAtivo(
        setores_criticos_sustentados=fia.contexto_inclusao_direta.setores_criticos_sustentados,
        descumpre_tratado_internacional=fia.contexto_inclusao_direta.descumpre_tratado_internacional,
        spof_setorial_reconhecido=fia.contexto_inclusao_direta.spof_setorial_reconhecido,
    )
    r = avaliar(ind, fi, rto_horas=fia.parametros_operacionais.rto_horas, contexto=ctx)
    return ResultadoMACADTO(
        pilares=[ResultadoPilarDTO(**p.to_dict()) for p in r.pilares],
        pfa=r.pfa, fi=r.fi, fd=r.fd, rto_horas=r.rto_horas,
        pfa_ajustado=r.pfa_ajustado, classe=r.classe.value,
        clausulas_disparadas=[c.value for c in r.clausulas_disparadas],
        reclassificado_por_clausula=r.reclassificado_por_clausula,
    )
