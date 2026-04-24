"""
Schemas Pydantic — DTOs usados na API REST.

Refletem 1:1 a estrutura da FIA (Anexo V) e da MACA (Anexo III), preparados
para serialização JSON e validação de entrada.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# -------------------------------------------------------------------
# Enumerações
# -------------------------------------------------------------------

class PorteEnum(str, Enum):
    GRANDE = "grande"
    MEDIO = "medio"
    PEQUENO = "pequeno"


class TipoAtivoEnum(str, Enum):
    INFRAESTRUTURA_FISICA = "infraestrutura_fisica"
    SISTEMA_LOGICO = "sistema_logico"
    DADO = "dado"
    RECURSO_HUMANO = "recurso_humano"
    CADEIA_SUPRIMENTOS = "cadeia_suprimentos"
    OUTRO = "outro"


class NaturezaLocalizacaoEnum(str, Enum):
    FISICA_SITIO_UNICO = "fisica_sitio_unico"
    FISICA_MULTIPLOS = "fisica_multiplos"
    LOGICA_NUVEM_PUBLICA = "logica_nuvem_publica"
    LOGICA_NUVEM_PRIVADA = "logica_nuvem_privada"
    HIBRIDA = "hibrida"


class ClasseCriticidadeEnum(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class TierNistEnum(str, Enum):
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    T4 = "T4"


class FuncaoNistEnum(str, Enum):
    GV = "GV"
    ID = "ID"
    PR = "PR"
    DE = "DE"
    RS = "RS"
    RC = "RC"


# -------------------------------------------------------------------
# Entrada: FIA (Anexo V)
# -------------------------------------------------------------------

class Prestadora(BaseModel):
    razao_social: str = Field(..., max_length=255)
    cnpj: str = Field(..., pattern=r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$")
    porte: PorteEnum
    codigo_anatel: str
    servicos_autorizados: list[str]


class IdentificacaoAtivo(BaseModel):
    id_unico: str = Field(..., max_length=64, description="Código interno estável entre ciclos")
    nome: str = Field(..., max_length=255)
    tipo: TipoAtivoEnum
    fabricante: str | None = None
    modelo_versao: str | None = None
    descricao_funcional: str = Field(..., max_length=500)
    data_operacao: str | None = None  # MM/AAAA
    previsao_eol: str | None = None


class Localizacao(BaseModel):
    natureza: NaturezaLocalizacaoEnum
    paises: list[str] = ["Brasil"]
    ufs: list[str]
    municipios: list[str]
    coordenadas: tuple[float, float] | None = None  # (lat, lng)
    provedor_nuvem: str | None = None
    declaracao_soberania: str


class Responsaveis(BaseModel):
    area_tecnica: str
    gestor_nome: str
    gestor_cargo: str
    gestor_email: str
    gestor_contato: str
    ciso_nome: str
    plantao_24x7: str | None = None


class Dependencia(BaseModel):
    ativo_ou_recurso: str
    natureza: Literal["interno", "fornecedor", "intersetorial", "externo"]
    criticidade: Literal["alta", "media", "baixa"]
    observacoes: str | None = None


class ParametrosOperacionais(BaseModel):
    rto_horas: Decimal = Field(..., ge=0)
    rpo_minutos: Decimal = Field(..., ge=0)
    sla_disponibilidade: Decimal | None = None  # percentual
    disponibilidade_observada: Decimal | None = None
    acessos_atendidos: int | None = None
    volume_trafego_gbps_pico: Decimal | None = None
    populacao_coberta: int | None = None
    prestadoras_dependentes: int = 0
    setores_criticos_atendidos: list[str] = []
    versao_inventario: str


class PontuacoesMACA(BaseModel):
    """Os 28 indicadores MACA, todos entre 0 e 5."""
    # Pilar 1
    i_1_1: int = Field(..., ge=0, le=5)
    i_1_2: int = Field(..., ge=0, le=5)
    i_1_3: int = Field(..., ge=0, le=5)
    i_1_4: int = Field(..., ge=0, le=5)
    i_1_5: int = Field(..., ge=0, le=5)
    i_1_6: int = Field(..., ge=0, le=5)
    # Pilar 2
    i_2_1: int = Field(..., ge=0, le=5)
    i_2_2: int = Field(..., ge=0, le=5)
    i_2_3: int = Field(..., ge=0, le=5)
    i_2_4: int = Field(..., ge=0, le=5)
    i_2_5: int = Field(..., ge=0, le=5)
    i_2_6: int = Field(..., ge=0, le=5)
    i_2_7: int = Field(..., ge=0, le=5)
    i_2_8: int = Field(..., ge=0, le=5)
    # Pilar 3
    i_3_1: int = Field(..., ge=0, le=5)
    i_3_2: int = Field(..., ge=0, le=5)
    i_3_3: int = Field(..., ge=0, le=5)
    i_3_4: int = Field(..., ge=0, le=5)
    i_3_5: int = Field(..., ge=0, le=5)
    # Pilar 4
    i_4_1: int = Field(..., ge=0, le=5)
    i_4_2: int = Field(..., ge=0, le=5)
    i_4_3: int = Field(..., ge=0, le=5)
    i_4_4: int = Field(..., ge=0, le=5)
    i_4_5: int = Field(..., ge=0, le=5)
    # Pilar 5
    i_5_1: int = Field(..., ge=0, le=5)
    i_5_2: int = Field(..., ge=0, le=5)
    i_5_3: int = Field(..., ge=0, le=5)
    i_5_4: int = Field(..., ge=0, le=5)


class FatoresAjuste(BaseModel):
    fi_intra_leve: bool = False
    fi_intra_significativa: bool = False
    fi_inter_1_setor: bool = False
    fi_inter_2_mais_setores: bool = False
    fi_efeito_cascata: bool = False


class ContextoInclusaoDireta(BaseModel):
    setores_criticos_sustentados: int = 0
    descumpre_tratado_internacional: bool = False
    spof_setorial_reconhecido: bool = False


class PerfilNIST(BaseModel):
    funcao: FuncaoNistEnum
    tier_atual: TierNistEnum
    tier_alvo: TierNistEnum
    principais_lacunas: str | None = None


class Incidente(BaseModel):
    data: str  # DD/MM/AAAA
    tipo: str
    duracao: str
    resumo_impacto: str


class AcaoPlano(BaseModel):
    acao: str
    prioridade: Literal["alta", "media", "baixa"]
    prazo: str  # MM/AAAA
    responsavel: str


class FIACompleta(BaseModel):
    """
    Ficha de Identificação de Ativo (Anexo V) em formato estruturado.

    Esta é a entrada completa recebida pelo endpoint POST /api/v1/fia.
    """
    prestadora: Prestadora
    identificacao_ativo: IdentificacaoAtivo
    localizacao: Localizacao
    responsaveis: Responsaveis
    servicos_suportados: list[str]
    dependencias_upstream: list[Dependencia]
    dependentes_downstream: list[Dependencia]
    parametros_operacionais: ParametrosOperacionais
    pontuacoes_maca: PontuacoesMACA
    fatores_ajuste: FatoresAjuste
    contexto_inclusao_direta: ContextoInclusaoDireta = ContextoInclusaoDireta()
    perfis_nist: list[PerfilNIST] = []
    historico_incidentes: list[Incidente] = []
    plano_acao: list[AcaoPlano] = []
    assinatura_responsavel: str  # hash da assinatura digital ICP-Brasil
    assinatura_ciso: str
    data_preenchimento: datetime
    versao_documento: str


# -------------------------------------------------------------------
# Saída: Resultado MACA
# -------------------------------------------------------------------

class ResultadoPilarDTO(BaseModel):
    pilar: int
    maximo: Decimal
    media: Decimal
    pp: Decimal


class ResultadoMACADTO(BaseModel):
    pilares: list[ResultadoPilarDTO]
    pfa: Decimal
    fi: Decimal
    fd: Decimal
    rto_horas: Decimal
    pfa_ajustado: Decimal
    classe: ClasseCriticidadeEnum
    clausulas_disparadas: list[str]
    reclassificado_por_clausula: bool


class FIASubmetidaResponse(BaseModel):
    """Resposta ao submeter uma FIA."""
    id_fia: UUID
    id_ativo: str
    prestadora_cnpj: str
    resultado_maca: ResultadoMACADTO
    protocolo_submissao: str
    timestamp_submissao: datetime
    cifrada: bool = True


# -------------------------------------------------------------------
# Consolidação setorial (CSAC)
# -------------------------------------------------------------------

class AtivoCSAC(BaseModel):
    id_ativo: str
    nome_ativo: str
    prestadora_razao_social: str
    classe: ClasseCriticidadeEnum
    pfa_ajustado: Decimal
    ufs: list[str]
    tipo: TipoAtivoEnum
    ultima_avaliacao: datetime


class ResumoCSAC(BaseModel):
    total_ativos: int
    por_classe: dict[str, int]  # {"A": 12, "B": 47, "C": 133, "D": 268}
    por_uf: dict[str, int]
    por_tipo: dict[str, int]
    total_prestadoras: int
    spofs_identificados: int
    ciclo_referencia: str  # "2026"
    ultima_atualizacao: datetime


class Insight(BaseModel):
    """Insight gerado pelo motor de regras."""
    id_regra: str
    nome_regra: str
    severidade: Literal["critica", "alta", "media", "baixa", "informativa"]
    ativo_afetado: str
    prestadora: str
    descricao: str
    recomendacao: str
    evidencias: dict
    gerado_em: datetime
