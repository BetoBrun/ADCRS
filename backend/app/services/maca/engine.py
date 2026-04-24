"""
Motor de Cálculo MACA — Metodologia de Avaliação de Criticidade de Ativos
===========================================================================

Implementação determinística das fórmulas do Anexo III da Resolução ANATEL
nº 740/2020, conforme Metodologia de Joias da Coroa — IC Telecom V2.0.

Este módulo é INTENCIONALMENTE PURO:
  - sem dependência de banco de dados
  - sem dependência de framework web
  - sem side effects
  - 100% testável via pytest com inputs JSON

Toda alteração neste arquivo exige revisão do GT-Ciber e atualização do
Anexo III correspondente, pois ele é a implementação normativa da MACA.

Fórmulas:
  PP  = 0,70 * máx(indicadores) + 0,30 * média(indicadores)
  PFA = Σ (PPₙ * pesoₙ)    com pesos (0,30; 0,25; 0,20; 0,15; 0,10)
  FI  ≤ 0,20  (soma de 5 componentes)
  FD  ∈ {0,00; 0,03; 0,06; 0,10}  conforme RTO
  PFA* = mín(PFA * (1 + FI + FD); 5,00)

Classes:
  D: PFA* < 2,0
  C: 2,0 ≤ PFA* < 3,0
  B: 3,0 ≤ PFA* < 4,0
  A: PFA* ≥ 4,0  OU  cláusula de inclusão direta disparada
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Literal

# -------------------------------------------------------------------
# Constantes normativas — NÃO ALTERAR sem revisão do GT-Ciber
# -------------------------------------------------------------------

PESOS_PILARES: dict[int, Decimal] = {
    1: Decimal("0.30"),  # Pilar 1 — Missão do Estado
    2: Decimal("0.25"),  # Pilar 2 — Impacto Social
    3: Decimal("0.20"),  # Pilar 3 — Impacto Econômico
    4: Decimal("0.15"),  # Pilar 4 — Segurança da Informação
    5: Decimal("0.10"),  # Pilar 5 — Legal/Regulatório
}

COEF_MAX = Decimal("0.70")
COEF_MEDIA = Decimal("0.30")
PFA_TETO = Decimal("5.00")
FI_TETO = Decimal("0.20")

# Componentes do Fator de Interdependência (FI)
FI_COMPONENTES: dict[str, Decimal] = {
    "intra_leve": Decimal("0.03"),           # 2-3 prestadoras
    "intra_significativa": Decimal("0.07"),  # ≥4 prestadoras OU infra única
    "inter_1_setor": Decimal("0.04"),        # 1 setor crítico
    "inter_2_mais_setores": Decimal("0.08"), # ≥2 setores críticos
    "efeito_cascata": Decimal("0.05"),       # cascata <2h demonstrada
}

# Faixas do Fator de Duração (FD) por RTO em horas
FD_FAIXAS: list[tuple[Decimal, Decimal, Decimal, str]] = [
    # (rto_min, rto_max, fd, descricao)   — intervalo fechado à esquerda, aberto à direita
    (Decimal("0"), Decimal("4"), Decimal("0.00"), "≤ 4h"),
    (Decimal("4"), Decimal("24"), Decimal("0.03"), "4h < RTO ≤ 24h"),
    (Decimal("24"), Decimal("72"), Decimal("0.06"), "24h < RTO ≤ 72h"),
    (Decimal("72"), Decimal("99999"), Decimal("0.10"), "> 72h"),
]

# Thresholds das classes
CLASSE_LIMITES: list[tuple[Decimal, str]] = [
    (Decimal("4.00"), "A"),
    (Decimal("3.00"), "B"),
    (Decimal("2.00"), "C"),
    (Decimal("0.00"), "D"),
]


# -------------------------------------------------------------------
# Tipos
# -------------------------------------------------------------------

class Classe(str, Enum):
    """Classes de criticidade conforme Anexo III, Art. 12."""
    A = "A"  # Joia da Coroa
    B = "B"  # Alta
    C = "C"  # Moderada
    D = "D"  # Não crítico


class ClausulaInclusao(str, Enum):
    """Cláusulas de inclusão direta conforme Anexo III, Art. 13."""
    PILAR_1_CATASTROFICO = "pilar_1_catastrofico"
    CIDADAOS_OU_GEOGRAFIA = "cidadaos_ou_geografia"
    SISTEMA_SFN = "sistema_sfn"
    INFO_SECRETA_OU_ULTRA = "info_secreta_ou_ultrassecreta"
    TRES_SETORES_CRITICOS = "tres_setores_criticos"
    TRATADO_INTERNACIONAL = "tratado_internacional"
    SPOF_SETORIAL = "spof_setorial"


@dataclass(frozen=True)
class Indicadores:
    """Indicadores dos 5 pilares — cada valor entre 0 e 5."""
    # Pilar 1 — Missão do Estado (6 indicadores)
    i_1_1: int  # Criticidade do serviço público
    i_1_2: int  # Interdependência governamental
    i_1_3: int  # Tempo de contingência
    i_1_4: int  # Potencial de pânico/desordem
    i_1_5: int  # Suporte a forças de segurança
    i_1_6: int  # Tratados internacionais
    # Pilar 2 — Impacto Social (8 indicadores)
    i_2_1: int  # Cidadãos afetados
    i_2_2: int  # Abrangência geográfica
    i_2_3: int  # Acessos desconectados
    i_2_4: int  # Volume de tráfego
    i_2_5: int  # Suporte a emergência
    i_2_6: int  # Saúde
    i_2_7: int  # Populações vulneráveis
    i_2_8: int  # Exposição midiática
    # Pilar 3 — Impacto Econômico (5 indicadores)
    i_3_1: int  # Perda de receita
    i_3_2: int  # Sistemas estruturantes do SFN
    i_3_3: int  # Cadeias produtivas
    i_3_4: int  # Custo de recuperação
    i_3_5: int  # Risco sistêmico financeiro
    # Pilar 4 — Segurança da Informação (5 indicadores)
    i_4_1: int  # Classificação da informação (LAI)
    i_4_2: int  # Atratividade para adversários
    i_4_3: int  # Dados pessoais (LGPD)
    i_4_4: int  # Sigilo das comunicações
    i_4_5: int  # Interceptação legal
    # Pilar 5 — Legal/Regulatório (4 indicadores)
    i_5_1: int  # Conformidade LGPD
    i_5_2: int  # Conformidade LGT/MC/R-Ciber
    i_5_3: int  # Sanções
    i_5_4: int  # Litígios de massa

    def __post_init__(self):
        for campo, valor in self.__dict__.items():
            if not isinstance(valor, int) or not (0 <= valor <= 5):
                raise ValueError(
                    f"Indicador {campo} = {valor!r} inválido. "
                    f"Deve ser inteiro de 0 a 5."
                )

    def pilar(self, n: Literal[1, 2, 3, 4, 5]) -> list[int]:
        """Retorna a lista de indicadores de um pilar específico."""
        mapa = {
            1: [self.i_1_1, self.i_1_2, self.i_1_3, self.i_1_4, self.i_1_5, self.i_1_6],
            2: [self.i_2_1, self.i_2_2, self.i_2_3, self.i_2_4, self.i_2_5, self.i_2_6, self.i_2_7, self.i_2_8],
            3: [self.i_3_1, self.i_3_2, self.i_3_3, self.i_3_4, self.i_3_5],
            4: [self.i_4_1, self.i_4_2, self.i_4_3, self.i_4_4, self.i_4_5],
            5: [self.i_5_1, self.i_5_2, self.i_5_3, self.i_5_4],
        }
        return mapa[n]


@dataclass(frozen=True)
class FatorInterdependencia:
    """Flags de contribuição ao FI (soma limitada a 0,20)."""
    intra_leve: bool = False
    intra_significativa: bool = False
    inter_1_setor: bool = False
    inter_2_mais_setores: bool = False
    efeito_cascata: bool = False

    def calcular(self) -> Decimal:
        """Soma os componentes aplicáveis, limitada ao teto de 0,20."""
        total = Decimal("0.00")
        if self.intra_leve:
            total += FI_COMPONENTES["intra_leve"]
        if self.intra_significativa:
            total += FI_COMPONENTES["intra_significativa"]
        if self.inter_1_setor:
            total += FI_COMPONENTES["inter_1_setor"]
        if self.inter_2_mais_setores:
            total += FI_COMPONENTES["inter_2_mais_setores"]
        if self.efeito_cascata:
            total += FI_COMPONENTES["efeito_cascata"]
        return min(total, FI_TETO)


@dataclass(frozen=True)
class ContextoAtivo:
    """Contexto para cláusulas de inclusão direta que dependem de dados além dos indicadores."""
    setores_criticos_sustentados: int = 0        # Cláusula "tres_setores_criticos"
    descumpre_tratado_internacional: bool = False  # Cláusula "tratado_internacional"
    spof_setorial_reconhecido: bool = False        # Cláusula "spof_setorial"


@dataclass
class ResultadoPilar:
    pilar: int
    maximo: Decimal
    media: Decimal
    pp: Decimal

    def to_dict(self) -> dict:
        return {
            "pilar": self.pilar,
            "maximo": float(self.maximo),
            "media": float(self.media),
            "pp": float(self.pp),
        }


@dataclass
class ResultadoMACA:
    """Resultado completo da avaliação MACA de um ativo."""
    pilares: list[ResultadoPilar]
    pfa: Decimal
    fi: Decimal
    fd: Decimal
    rto_horas: Decimal
    pfa_ajustado: Decimal
    classe: Classe
    clausulas_disparadas: list[ClausulaInclusao] = field(default_factory=list)
    reclassificado_por_clausula: bool = False

    def to_dict(self) -> dict:
        return {
            "pilares": [p.to_dict() for p in self.pilares],
            "pfa": float(self.pfa),
            "fi": float(self.fi),
            "fd": float(self.fd),
            "rto_horas": float(self.rto_horas),
            "pfa_ajustado": float(self.pfa_ajustado),
            "classe": self.classe.value,
            "clausulas_disparadas": [c.value for c in self.clausulas_disparadas],
            "reclassificado_por_clausula": self.reclassificado_por_clausula,
        }


# -------------------------------------------------------------------
# Funções de cálculo
# -------------------------------------------------------------------

def _q(v: Decimal) -> Decimal:
    """Arredonda para 2 casas decimais (HALF_UP) conforme convenção MACA."""
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_pp(indicadores_pilar: list[int]) -> ResultadoPilar:
    """
    Calcula a Pontuação do Pilar (PP).

    Fórmula: PP = 0,70 × máx(indicadores) + 0,30 × média(indicadores)

    Raises:
        ValueError: se a lista de indicadores estiver vazia.
    """
    if not indicadores_pilar:
        raise ValueError("Lista de indicadores não pode ser vazia")

    valores = [Decimal(v) for v in indicadores_pilar]
    maximo = max(valores)
    media = sum(valores) / Decimal(len(valores))
    pp = _q(COEF_MAX * maximo + COEF_MEDIA * media)
    return ResultadoPilar(
        pilar=0,  # preenchido pelo chamador
        maximo=maximo,
        media=_q(media),
        pp=pp,
    )


def calcular_pfa(pps: dict[int, Decimal]) -> Decimal:
    """
    Calcula a Pontuação Final do Ativo (PFA).

    Fórmula: PFA = Σ (PPₙ × pesoₙ)

    Args:
        pps: dicionário {pilar: PP}. Deve conter todos os 5 pilares.

    Raises:
        ValueError: se faltar algum pilar.
    """
    faltantes = set(PESOS_PILARES.keys()) - set(pps.keys())
    if faltantes:
        raise ValueError(f"Pilares faltantes: {sorted(faltantes)}")

    pfa = sum(pps[n] * PESOS_PILARES[n] for n in sorted(PESOS_PILARES.keys()))
    return _q(Decimal(pfa))


def calcular_fd(rto_horas: Decimal) -> tuple[Decimal, str]:
    """
    Calcula o Fator de Duração (FD) a partir do RTO em horas.

    Raises:
        ValueError: se RTO for negativo.
    """
    if rto_horas < 0:
        raise ValueError(f"RTO não pode ser negativo: {rto_horas}")

    for rto_min, rto_max, fd, descricao in FD_FAIXAS:
        if rto_min <= rto_horas < rto_max or (rto_min == 0 and rto_horas == 0):
            # Casos de borda documentados no Anexo III:
            #   RTO = 4h exato → faixa 0,03 (intervalo aberto em 4)
            #   RTO = 24h exato → faixa 0,06
            #   RTO = 72h exato → faixa 0,10
            if rto_horas == Decimal("4"):
                return Decimal("0.03"), "4h < RTO ≤ 24h"
            if rto_horas == Decimal("24"):
                return Decimal("0.06"), "24h < RTO ≤ 72h"
            if rto_horas == Decimal("72"):
                return Decimal("0.10"), "> 72h"
            return fd, descricao
    return Decimal("0.10"), "> 72h"


def calcular_pfa_ajustado(pfa: Decimal, fi: Decimal, fd: Decimal) -> Decimal:
    """
    Calcula a PFA*.

    Fórmula: PFA* = mín(PFA × (1 + FI + FD); 5,00)
    """
    valor = pfa * (Decimal("1") + fi + fd)
    return _q(min(valor, PFA_TETO))


def verificar_clausulas_inclusao_direta(
    indicadores: Indicadores,
    contexto: ContextoAtivo,
) -> list[ClausulaInclusao]:
    """
    Verifica as 7 cláusulas de inclusão direta (Anexo III, Art. 13).

    Qualquer cláusula disparada resulta em classificação automática como Classe A.
    """
    clausulas: list[ClausulaInclusao] = []

    # Cláusula 1: Pontuação 5 em qualquer indicador do Pilar 1
    if 5 in indicadores.pilar(1):
        clausulas.append(ClausulaInclusao.PILAR_1_CATASTROFICO)

    # Cláusula 2: Pontuação 5 em 2.1 (cidadãos) OU 2.2 (abrangência)
    if indicadores.i_2_1 == 5 or indicadores.i_2_2 == 5:
        clausulas.append(ClausulaInclusao.CIDADAOS_OU_GEOGRAFIA)

    # Cláusula 3: Pontuação 5 em 3.2 (sistemas estruturantes do SFN)
    if indicadores.i_3_2 == 5:
        clausulas.append(ClausulaInclusao.SISTEMA_SFN)

    # Cláusula 4: Pontuação 5 em 4.1 (informação secreta/ultrassecreta)
    if indicadores.i_4_1 == 5:
        clausulas.append(ClausulaInclusao.INFO_SECRETA_OU_ULTRA)

    # Cláusula 5: 3+ setores críticos sustentados
    if contexto.setores_criticos_sustentados >= 3:
        clausulas.append(ClausulaInclusao.TRES_SETORES_CRITICOS)

    # Cláusula 6: descumprimento de tratado internacional
    if contexto.descumpre_tratado_internacional:
        clausulas.append(ClausulaInclusao.TRATADO_INTERNACIONAL)

    # Cláusula 7: SPOF setorial reconhecido pelo GT-Ciber
    if contexto.spof_setorial_reconhecido:
        clausulas.append(ClausulaInclusao.SPOF_SETORIAL)

    return clausulas


def classificar(pfa_ajustado: Decimal, clausulas: list[ClausulaInclusao]) -> tuple[Classe, bool]:
    """
    Determina a classe de criticidade.

    Retorna (classe, reclassificado_por_clausula).

    Se qualquer cláusula foi disparada → Classe A (reclassificado=True).
    Caso contrário, aplica as faixas por PFA*.
    """
    if clausulas:
        return Classe.A, True

    for limite, classe_str in CLASSE_LIMITES:
        if pfa_ajustado >= limite:
            return Classe(classe_str), False

    return Classe.D, False


# -------------------------------------------------------------------
# Função de orquestração
# -------------------------------------------------------------------

def avaliar(
    indicadores: Indicadores,
    fator_inter: FatorInterdependencia,
    rto_horas: float | Decimal,
    contexto: ContextoAtivo | None = None,
) -> ResultadoMACA:
    """
    Avalia um ativo pela MACA completa.

    Esta é a função de entrada principal. Dado um conjunto de indicadores,
    o FI e o RTO, retorna o resultado MACA completo, incluindo classe final.

    Exemplo:
        >>> from app.services.maca import avaliar, Indicadores, FatorInterdependencia
        >>> ind = Indicadores(
        ...     i_1_1=4, i_1_2=4, i_1_3=4, i_1_4=3, i_1_5=4, i_1_6=4,
        ...     i_2_1=5, i_2_2=5, i_2_3=5, i_2_4=5, i_2_5=3, i_2_6=3, i_2_7=2, i_2_8=4,
        ...     i_3_1=5, i_3_2=5, i_3_3=4, i_3_4=5, i_3_5=4,
        ...     i_4_1=3, i_4_2=4, i_4_3=4, i_4_4=4, i_4_5=3,
        ...     i_5_1=3, i_5_2=4, i_5_3=4, i_5_4=3,
        ... )
        >>> fi = FatorInterdependencia(
        ...     intra_significativa=True,
        ...     inter_2_mais_setores=True,
        ...     efeito_cascata=True,
        ... )
        >>> resultado = avaliar(ind, fi, rto_horas=120)
        >>> resultado.classe
        <Classe.A: 'A'>
        >>> float(resultado.pfa_ajustado)
        5.0
    """
    contexto = contexto or ContextoAtivo()
    rto = Decimal(str(rto_horas))

    # 1. Calcula PP de cada pilar
    pilares: list[ResultadoPilar] = []
    pps: dict[int, Decimal] = {}
    for n in sorted(PESOS_PILARES.keys()):
        resultado = calcular_pp(indicadores.pilar(n))
        resultado.pilar = n
        pilares.append(resultado)
        pps[n] = resultado.pp

    # 2. Calcula PFA
    pfa = calcular_pfa(pps)

    # 3. Calcula FI
    fi = fator_inter.calcular()

    # 4. Calcula FD
    fd, _ = calcular_fd(rto)

    # 5. Calcula PFA*
    pfa_ajustado = calcular_pfa_ajustado(pfa, fi, fd)

    # 6. Verifica cláusulas de inclusão direta
    clausulas = verificar_clausulas_inclusao_direta(indicadores, contexto)

    # 7. Classifica
    classe, reclassificado = classificar(pfa_ajustado, clausulas)

    return ResultadoMACA(
        pilares=pilares,
        pfa=pfa,
        fi=fi,
        fd=fd,
        rto_horas=rto,
        pfa_ajustado=pfa_ajustado,
        classe=classe,
        clausulas_disparadas=clausulas,
        reclassificado_por_clausula=reclassificado,
    )
