"""
Testes do Motor MACA
====================

Estes testes são CRÍTICOS: eles validam numericamente que o motor de cálculo
implementa corretamente as fórmulas do Anexo III. Qualquer alteração que
quebre um teste aqui caracteriza divergência normativa e deve ser bloqueada
no CI até revisão do GT-Ciber.

Inclui o exemplo numérico completo do cabo submarino do Anexo III, Seção 7.
"""

from decimal import Decimal

import pytest

from app.services.maca import (
    Classe,
    ClausulaInclusao,
    ContextoAtivo,
    FatorInterdependencia,
    Indicadores,
    avaliar,
    calcular_fd,
    calcular_pfa,
    calcular_pfa_ajustado,
    calcular_pp,
    classificar,
    verificar_clausulas_inclusao_direta,
)


# ==================================================================
# Testes unitários: cálculo de PP
# ==================================================================

class TestCalcularPP:

    def test_pp_pilar_homogeneo(self):
        """Indicadores todos iguais → PP = 0.70*max + 0.30*media = valor."""
        resultado = calcular_pp([3, 3, 3, 3, 3])
        assert resultado.maximo == Decimal("3")
        assert resultado.media == Decimal("3.00")
        assert resultado.pp == Decimal("3.00")

    def test_pp_pilar_com_um_5_puxa_pontuacao(self):
        """Um indicador 5 e o resto zero → PP fortemente puxado pelo máximo."""
        resultado = calcular_pp([5, 0, 0, 0, 0])
        # max=5, media=1 → 0.70*5 + 0.30*1 = 3.50 + 0.30 = 3.80
        assert resultado.maximo == Decimal("5")
        assert resultado.pp == Decimal("3.80")

    def test_pp_todos_zeros(self):
        resultado = calcular_pp([0, 0, 0, 0, 0])
        assert resultado.pp == Decimal("0.00")

    def test_pp_todos_cinco(self):
        resultado = calcular_pp([5, 5, 5, 5, 5])
        assert resultado.pp == Decimal("5.00")

    def test_pp_lista_vazia_levanta_erro(self):
        with pytest.raises(ValueError, match="não pode ser vazia"):
            calcular_pp([])

    @pytest.mark.parametrize("indicadores,esperado_pp", [
        ([4, 4, 4, 3, 4, 4], Decimal("3.95")),  # Pilar 1 do cabo submarino (max=4, media=3.83)
        ([5, 5, 5, 5, 3, 3, 2, 4], Decimal("4.70")),  # Pilar 2 (max=5, media=4.00)
        ([5, 5, 4, 5, 4], Decimal("4.88")),  # Pilar 3 (max=5, media=4.60)
        ([3, 4, 4, 4, 3], Decimal("3.88")),  # Pilar 4 (max=4, media=3.60)
        ([3, 4, 4, 3], Decimal("3.85")),  # Pilar 5 (max=4, media=3.50)
    ])
    def test_pp_exemplo_cabo_submarino(self, indicadores, esperado_pp):
        """Reproduz os cálculos de PP do exemplo do Anexo III."""
        resultado = calcular_pp(indicadores)
        assert resultado.pp == esperado_pp


# ==================================================================
# Testes unitários: cálculo de PFA
# ==================================================================

class TestCalcularPFA:

    def test_pfa_cabo_submarino(self):
        """Reproduz o cálculo de PFA do exemplo do Anexo III: 4.30."""
        pps = {
            1: Decimal("3.95"),
            2: Decimal("4.70"),
            3: Decimal("4.88"),
            4: Decimal("3.88"),
            5: Decimal("3.85"),
        }
        # PFA = 3.95*0.30 + 4.70*0.25 + 4.88*0.20 + 3.88*0.15 + 3.85*0.10
        #     = 1.185 + 1.175 + 0.976 + 0.582 + 0.385 = 4.303 → 4.30
        pfa = calcular_pfa(pps)
        assert pfa == Decimal("4.30")

    def test_pfa_todos_zeros(self):
        pps = {n: Decimal("0") for n in range(1, 6)}
        assert calcular_pfa(pps) == Decimal("0.00")

    def test_pfa_todos_cinco(self):
        pps = {n: Decimal("5") for n in range(1, 6)}
        assert calcular_pfa(pps) == Decimal("5.00")

    def test_pfa_pilar_faltante_erro(self):
        pps = {1: Decimal("3"), 2: Decimal("3"), 3: Decimal("3")}  # faltam 4 e 5
        with pytest.raises(ValueError, match="Pilares faltantes"):
            calcular_pfa(pps)

    def test_pfa_pesos_somam_um(self):
        """Os pesos normativos devem somar 1,00."""
        from app.services.maca.engine import PESOS_PILARES
        assert sum(PESOS_PILARES.values()) == Decimal("1.00")


# ==================================================================
# Testes unitários: Fator de Interdependência
# ==================================================================

class TestFatorInterdependencia:

    def test_fi_sem_componentes(self):
        assert FatorInterdependencia().calcular() == Decimal("0.00")

    def test_fi_apenas_intra_leve(self):
        assert FatorInterdependencia(intra_leve=True).calcular() == Decimal("0.03")

    def test_fi_cabo_submarino(self):
        """Exemplo do Anexo III: FI = 0.20 (no teto)."""
        fi = FatorInterdependencia(
            intra_significativa=True,    # +0.07
            inter_2_mais_setores=True,   # +0.08
            efeito_cascata=True,         # +0.05
        ).calcular()
        # Soma = 0.20, exatamente no teto
        assert fi == Decimal("0.20")

    def test_fi_limitado_ao_teto(self):
        """Todos os componentes somam > 0.20, mas devem ser limitados."""
        fi = FatorInterdependencia(
            intra_leve=True,             # 0.03
            intra_significativa=True,    # 0.07
            inter_1_setor=True,          # 0.04
            inter_2_mais_setores=True,   # 0.08
            efeito_cascata=True,         # 0.05
        ).calcular()
        # Soma bruta = 0.27, mas teto é 0.20
        assert fi == Decimal("0.20")


# ==================================================================
# Testes unitários: Fator de Duração
# ==================================================================

class TestFatorDuracao:

    @pytest.mark.parametrize("rto,fd_esperado", [
        (Decimal("0"), Decimal("0.00")),
        (Decimal("2"), Decimal("0.00")),
        (Decimal("4"), Decimal("0.03")),    # 4h exato → próxima faixa
        (Decimal("12"), Decimal("0.03")),
        (Decimal("24"), Decimal("0.06")),   # 24h exato → próxima faixa
        (Decimal("48"), Decimal("0.06")),
        (Decimal("72"), Decimal("0.10")),   # 72h exato → última faixa
        (Decimal("168"), Decimal("0.10")),
        (Decimal("720"), Decimal("0.10")),
    ])
    def test_fd_faixas(self, rto, fd_esperado):
        fd, _ = calcular_fd(rto)
        assert fd == fd_esperado

    def test_fd_rto_negativo_erro(self):
        with pytest.raises(ValueError, match="não pode ser negativo"):
            calcular_fd(Decimal("-1"))


# ==================================================================
# Testes unitários: PFA*
# ==================================================================

class TestPFAAjustado:

    def test_pfa_ajustado_sem_multiplicadores(self):
        """FI=0 e FD=0 → PFA* = PFA."""
        assert calcular_pfa_ajustado(
            Decimal("3.50"), Decimal("0"), Decimal("0")
        ) == Decimal("3.50")

    def test_pfa_ajustado_cabo_submarino(self):
        """Exemplo do Anexo III: PFA=4.30, FI=0.20, FD=0.10 → PFA*=5.00 (teto)."""
        pfa_aj = calcular_pfa_ajustado(
            Decimal("4.30"), Decimal("0.20"), Decimal("0.10")
        )
        # 4.30 * 1.30 = 5.59 → limitado a 5.00
        assert pfa_aj == Decimal("5.00")

    def test_pfa_ajustado_nao_excede_teto(self):
        pfa_aj = calcular_pfa_ajustado(
            Decimal("5.00"), Decimal("0.20"), Decimal("0.10")
        )
        assert pfa_aj == Decimal("5.00")

    def test_pfa_ajustado_abaixo_do_teto(self):
        # PFA=2.00, FI=0.10, FD=0.03 → 2.00 * 1.13 = 2.26
        pfa_aj = calcular_pfa_ajustado(
            Decimal("2.00"), Decimal("0.10"), Decimal("0.03")
        )
        assert pfa_aj == Decimal("2.26")


# ==================================================================
# Testes: Cláusulas de Inclusão Direta
# ==================================================================

class TestClausulasInclusaoDireta:

    def _indicadores_baseline(self, **overrides) -> Indicadores:
        """Indicadores todos zerados, com possibilidade de override."""
        defaults = {
            "i_1_1": 0, "i_1_2": 0, "i_1_3": 0, "i_1_4": 0, "i_1_5": 0, "i_1_6": 0,
            "i_2_1": 0, "i_2_2": 0, "i_2_3": 0, "i_2_4": 0,
            "i_2_5": 0, "i_2_6": 0, "i_2_7": 0, "i_2_8": 0,
            "i_3_1": 0, "i_3_2": 0, "i_3_3": 0, "i_3_4": 0, "i_3_5": 0,
            "i_4_1": 0, "i_4_2": 0, "i_4_3": 0, "i_4_4": 0, "i_4_5": 0,
            "i_5_1": 0, "i_5_2": 0, "i_5_3": 0, "i_5_4": 0,
        }
        defaults.update(overrides)
        return Indicadores(**defaults)

    def test_sem_clausulas(self):
        ind = self._indicadores_baseline()
        clausulas = verificar_clausulas_inclusao_direta(ind, ContextoAtivo())
        assert clausulas == []

    def test_pilar_1_catastrofico(self):
        ind = self._indicadores_baseline(i_1_3=5)  # qualquer do pilar 1
        clausulas = verificar_clausulas_inclusao_direta(ind, ContextoAtivo())
        assert ClausulaInclusao.PILAR_1_CATASTROFICO in clausulas

    def test_cidadaos_afetados_5(self):
        ind = self._indicadores_baseline(i_2_1=5)
        clausulas = verificar_clausulas_inclusao_direta(ind, ContextoAtivo())
        assert ClausulaInclusao.CIDADAOS_OU_GEOGRAFIA in clausulas

    def test_abrangencia_geografica_5(self):
        ind = self._indicadores_baseline(i_2_2=5)
        clausulas = verificar_clausulas_inclusao_direta(ind, ContextoAtivo())
        assert ClausulaInclusao.CIDADAOS_OU_GEOGRAFIA in clausulas

    def test_sistema_estruturante_sfn(self):
        ind = self._indicadores_baseline(i_3_2=5)
        clausulas = verificar_clausulas_inclusao_direta(ind, ContextoAtivo())
        assert ClausulaInclusao.SISTEMA_SFN in clausulas

    def test_informacao_secreta(self):
        ind = self._indicadores_baseline(i_4_1=5)
        clausulas = verificar_clausulas_inclusao_direta(ind, ContextoAtivo())
        assert ClausulaInclusao.INFO_SECRETA_OU_ULTRA in clausulas

    def test_tres_setores_criticos(self):
        ind = self._indicadores_baseline()
        ctx = ContextoAtivo(setores_criticos_sustentados=3)
        clausulas = verificar_clausulas_inclusao_direta(ind, ctx)
        assert ClausulaInclusao.TRES_SETORES_CRITICOS in clausulas

    def test_tratado_internacional(self):
        ind = self._indicadores_baseline()
        ctx = ContextoAtivo(descumpre_tratado_internacional=True)
        clausulas = verificar_clausulas_inclusao_direta(ind, ctx)
        assert ClausulaInclusao.TRATADO_INTERNACIONAL in clausulas

    def test_spof_setorial(self):
        ind = self._indicadores_baseline()
        ctx = ContextoAtivo(spof_setorial_reconhecido=True)
        clausulas = verificar_clausulas_inclusao_direta(ind, ctx)
        assert ClausulaInclusao.SPOF_SETORIAL in clausulas

    def test_multiplas_clausulas(self):
        """Cabo submarino dispara 3 cláusulas simultâneas."""
        ind = self._indicadores_baseline(i_2_1=5, i_2_2=5, i_3_2=5)
        clausulas = verificar_clausulas_inclusao_direta(ind, ContextoAtivo())
        assert len(clausulas) == 2  # 2.1 OU 2.2 conta como uma cláusula; 3.2 conta como outra


# ==================================================================
# Testes: Classificação
# ==================================================================

class TestClassificar:

    def test_clausula_sempre_produz_A(self):
        classe, recl = classificar(Decimal("0"), [ClausulaInclusao.PILAR_1_CATASTROFICO])
        assert classe == Classe.A
        assert recl is True

    @pytest.mark.parametrize("pfa,classe_esperada", [
        (Decimal("0.00"), Classe.D),
        (Decimal("1.99"), Classe.D),
        (Decimal("2.00"), Classe.C),
        (Decimal("2.99"), Classe.C),
        (Decimal("3.00"), Classe.B),
        (Decimal("3.99"), Classe.B),
        (Decimal("4.00"), Classe.A),
        (Decimal("5.00"), Classe.A),
    ])
    def test_faixas_sem_clausula(self, pfa, classe_esperada):
        classe, recl = classificar(pfa, [])
        assert classe == classe_esperada
        assert recl is False


# ==================================================================
# TESTE INTEGRADO: Caso Cabo Submarino (Anexo III, Seção 7)
# ==================================================================

class TestCaboSubmarinoAnexoIII:
    """
    Reproduz integralmente o exemplo numérico do Anexo III, Seção 7.

    Este teste é uma CERTIDÃO de conformidade normativa: se falhar, o motor
    MACA está divergindo do exemplo oficial.
    """

    def test_cabo_submarino_resultado_completo(self):
        indicadores = Indicadores(
            # Pilar 1
            i_1_1=4, i_1_2=4, i_1_3=4, i_1_4=3, i_1_5=4, i_1_6=4,
            # Pilar 2
            i_2_1=5, i_2_2=5, i_2_3=5, i_2_4=5, i_2_5=3, i_2_6=3, i_2_7=2, i_2_8=4,
            # Pilar 3
            i_3_1=5, i_3_2=5, i_3_3=4, i_3_4=5, i_3_5=4,
            # Pilar 4
            i_4_1=3, i_4_2=4, i_4_3=4, i_4_4=4, i_4_5=3,
            # Pilar 5
            i_5_1=3, i_5_2=4, i_5_3=4, i_5_4=3,
        )
        fator = FatorInterdependencia(
            intra_significativa=True,
            inter_2_mais_setores=True,
            efeito_cascata=True,
        )
        resultado = avaliar(indicadores, fator, rto_horas=120)

        # Verifica cada PP calculada
        pps = {p.pilar: p.pp for p in resultado.pilares}
        assert pps[1] == Decimal("3.95")
        assert pps[2] == Decimal("4.70")
        assert pps[3] == Decimal("4.88")
        assert pps[4] == Decimal("3.88")
        assert pps[5] == Decimal("3.85")

        # Verifica PFA
        assert resultado.pfa == Decimal("4.30")

        # Verifica fatores
        assert resultado.fi == Decimal("0.20")
        assert resultado.fd == Decimal("0.10")

        # Verifica PFA* (limitada ao teto 5.00)
        assert resultado.pfa_ajustado == Decimal("5.00")

        # Verifica classe
        assert resultado.classe == Classe.A

        # Verifica cláusulas disparadas
        assert len(resultado.clausulas_disparadas) >= 2
        assert ClausulaInclusao.CIDADAOS_OU_GEOGRAFIA in resultado.clausulas_disparadas
        assert ClausulaInclusao.SISTEMA_SFN in resultado.clausulas_disparadas
        assert resultado.reclassificado_por_clausula is True


# ==================================================================
# Testes de validação de entrada
# ==================================================================

class TestValidacao:

    def test_indicador_acima_de_5_levanta_erro(self):
        with pytest.raises(ValueError, match="inválido"):
            Indicadores(
                i_1_1=6,  # inválido
                i_1_2=0, i_1_3=0, i_1_4=0, i_1_5=0, i_1_6=0,
                i_2_1=0, i_2_2=0, i_2_3=0, i_2_4=0,
                i_2_5=0, i_2_6=0, i_2_7=0, i_2_8=0,
                i_3_1=0, i_3_2=0, i_3_3=0, i_3_4=0, i_3_5=0,
                i_4_1=0, i_4_2=0, i_4_3=0, i_4_4=0, i_4_5=0,
                i_5_1=0, i_5_2=0, i_5_3=0, i_5_4=0,
            )

    def test_indicador_negativo_levanta_erro(self):
        with pytest.raises(ValueError, match="inválido"):
            Indicadores(
                i_1_1=-1,
                i_1_2=0, i_1_3=0, i_1_4=0, i_1_5=0, i_1_6=0,
                i_2_1=0, i_2_2=0, i_2_3=0, i_2_4=0,
                i_2_5=0, i_2_6=0, i_2_7=0, i_2_8=0,
                i_3_1=0, i_3_2=0, i_3_3=0, i_3_4=0, i_3_5=0,
                i_4_1=0, i_4_2=0, i_4_3=0, i_4_4=0, i_4_5=0,
                i_5_1=0, i_5_2=0, i_5_3=0, i_5_4=0,
            )
