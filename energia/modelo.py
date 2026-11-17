"""Modelo energético do banho.

Compara três formas de atender a MESMA necessidade (banho a 40 °C para a família):

* L0 - chuveiro elétrico convencional (situação atual, potência fixa o ano todo);
* A  - chuveiro elétrico com práticas de uso eficiente (banho mais curto e potência
       ajustada ao clima, ex.: posição "verão" nos meses quentes);
* B  - aquecimento solar térmico com o chuveiro elétrico como complemento.

Todas as alternativas são calculadas dia a dia sobre o mesmo período (2016-2025),
com os mesmos dados de clima. Fórmulas principais:

    Energia elétrica (kWh)   E = P (kW) x t (h)
    Energia térmica  (kWh)   Q = V (L) x c x ΔT / 3600,  c = 4,186 kJ/(kg·K), 1 L ≈ 1 kg
    Produção solar   (kWh)   P_sol = PMEe/30 x A x H_inclinado / H_ref   (ensaio INMETRO / NBR 15569)
    Perda do reservatório    k = perda_específica x 3600 / (30 x ΔT_ensaio x c)  (fração do calor guardado/dia)
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

CALOR_ESPECIFICO_AGUA = 4.186  # kJ/(kg·K)
KJ_POR_KWH = 3600.0


@dataclass(frozen=True)
class Familia:
    """Hábitos atuais da família (linha de base L0)."""

    pessoas: int = 4
    minutos_banho: float = 8.0
    potencia_w: float = 5500.0

    def validar(self) -> None:
        if not 1 <= self.pessoas <= 20:
            raise ValueError("Número de pessoas deve estar entre 1 e 20.")
        if not 1 <= self.minutos_banho <= 60:
            raise ValueError("Tempo de banho deve estar entre 1 e 60 minutos.")
        if not 1000 <= self.potencia_w <= 12000:
            raise ValueError("Potência do chuveiro deve estar entre 1.000 e 12.000 W.")


@dataclass(frozen=True)
class PraticasEficientes:
    """Alternativa A: mudanças de uso, sem investimento."""

    minutos_banho: float = 5.0
    ajustar_potencia_no_calor: bool = True

    def validar(self, familia: Familia) -> None:
        if not 1 <= self.minutos_banho <= familia.minutos_banho:
            raise ValueError("Na alternativa A o banho deve durar entre 1 minuto e o tempo atual.")


@dataclass(frozen=True)
class SistemaSolar:
    """Alternativa B: kit de aquecimento solar térmico (referência SINAPI 103517)."""

    area_m2: float = 2.0
    volume_l: float = 200.0
    pmee_kwh_mes_m2: float = 90.9
    irradiacao_ref_kwh_m2_dia: float = 4.889
    fator_perdas: float = 0.15
    temp_max_reservatorio_c: float = 60.0
    perda_especifica_kwh_l_mes: float = 0.27  # limite máximo INMETRO p/ 100-300 L (Portaria 301/2012)
    delta_t_ensaio_perda_k: float = 29.0      # ensaio: água a 50 °C, ambiente a 21 °C
    investimento_rs: float = 3359.57
    fator_desempenho: float = 1.0             # < 1 para testar coletor rendendo menos que no ensaio
    fator_uso_agua_quente: float = 1.0        # > 1 para testar "efeito rebote" (mais água quente)

    def perda_diaria_fracao(self) -> float:
        """Fração do calor guardado perdida por dia (modelo de resfriamento de Newton).

        Perda diária no ensaio = perda_específica x V / 30 (kWh/dia) com ΔT_ensaio entre água e ar.
        Dividindo pelo calor guardado nesse ΔT (V x c x ΔT / 3600) o volume se cancela.
        """
        return self.perda_especifica_kwh_l_mes * KJ_POR_KWH / (
            30 * self.delta_t_ensaio_perda_k * CALOR_ESPECIFICO_AGUA
        )

    def validar(self) -> None:
        if self.area_m2 <= 0 or self.volume_l <= 0 or self.pmee_kwh_mes_m2 <= 0:
            raise ValueError("Área, volume e produção do coletor devem ser positivos.")
        if self.investimento_rs < 0:
            raise ValueError("Investimento não pode ser negativo.")
        if not 0 <= self.perda_diaria_fracao() < 1:
            raise ValueError("Perda do reservatório inválida.")


@dataclass(frozen=True)
class Premissas:
    temperatura_banho_c: float = 40.0
    eficiencia_chuveiro: float = 0.95


def energia_termica_kwh(litros: float, delta_t: float) -> float:
    """Q = V x c x ΔT / 3600 (kWh)."""
    return litros * CALOR_ESPECIFICO_AGUA * delta_t / KJ_POR_KWH


def vazao_l_min(potencia_w: float, eficiencia: float, delta_t_max: float) -> float:
    """Vazão (L/min) que o chuveiro aquece até a temperatura do banho no mês mais frio.

    P x η = m' x c x ΔT  ->  m' (kg/s) = P x η / (c x 1000 x ΔT)
    """
    if delta_t_max <= 0:
        raise ValueError("A água fria precisa estar abaixo da temperatura do banho.")
    return potencia_w * eficiencia / (CALOR_ESPECIFICO_AGUA * 1000 * delta_t_max) * 60


def simular(
    clima: pd.DataFrame,
    familia: Familia,
    praticas: PraticasEficientes,
    solar: SistemaSolar,
    premissas: Premissas,
) -> pd.DataFrame:
    """Simula dia a dia as três alternativas.

    `clima` precisa das colunas: data, ano, mes, temp_agua_fria_c, h_inclinado_kwh_m2_dia.
    Retorna uma linha por dia com energia (kWh), água (L) e o estado do reservatório solar.
    """
    familia.validar()
    praticas.validar(familia)
    solar.validar()

    t_banho = premissas.temperatura_banho_c
    # Mês mais frio da série (média de todos os anos) define a vazão do chuveiro.
    temp_fria_mais_baixa = clima.groupby("mes")["temp_agua_fria_c"].mean().min()
    delta_t_max = t_banho - temp_fria_mais_baixa
    vazao = vazao_l_min(familia.potencia_w, premissas.eficiencia_chuveiro, delta_t_max)

    kw = familia.potencia_w / 1000
    min_dia_l0 = familia.pessoas * familia.minutos_banho
    min_dia_a = familia.pessoas * praticas.minutos_banho

    df = clima[["data", "ano", "mes", "temp_agua_fria_c", "h_inclinado_kwh_m2_dia"]].copy()
    delta_t = (t_banho - df["temp_agua_fria_c"]).clip(lower=0)

    # L0: potência fixa (posição "inverno") o ano todo -> E = P x t
    df["e_l0_kwh"] = kw * min_dia_l0 / 60
    df["agua_l0_l"] = vazao * min_dia_l0

    # A: banho mais curto + potência proporcional ao ΔT do dia (limitada à potência nominal)
    if praticas.ajustar_potencia_no_calor:
        fracao_potencia = (delta_t / delta_t_max).clip(upper=1.0)
    else:
        fracao_potencia = 1.0
    df["e_a_kwh"] = kw * fracao_potencia * min_dia_a / 60
    df["agua_a_l"] = vazao * min_dia_a

    # B: mesma água e mesmos hábitos de L0; o sol pré-aquece e o chuveiro completa.
    df["necessidade_kwh"] = energia_termica_kwh(vazao * min_dia_l0, delta_t) * solar.fator_uso_agua_quente
    producao = (
        solar.pmee_kwh_mes_m2 / 30 * solar.area_m2
        * df["h_inclinado_kwh_m2_dia"] / solar.irradiacao_ref_kwh_m2_dia
        * solar.fator_desempenho
    )
    df["solar_disponivel_kwh"] = producao / (1 + solar.fator_perdas)
    capacidade = (
        solar.volume_l * CALOR_ESPECIFICO_AGUA
        * (solar.temp_max_reservatorio_c - df["temp_agua_fria_c"]).clip(lower=0) / KJ_POR_KWH
    )

    k = solar.perda_diaria_fracao()
    estoque = 0.0  # energia guardada no reservatório (kWh acima da água fria)
    usados, estoques, perdas = [], [], []
    for disponivel, necessidade, cap in zip(
        df["solar_disponivel_kwh"], df["necessidade_kwh"], capacidade
    ):
        perda = estoque * k                       # o reservatório esfria em 24 h
        estoque = min(cap, estoque - perda + disponivel)  # o sol "enche" o reservatório
        usado = min(estoque, necessidade)         # os banhos "esvaziam"
        estoque -= usado
        usados.append(usado)
        estoques.append(estoque)
        perdas.append(perda)
    df["solar_usado_kwh"] = usados
    df["estoque_fim_dia_kwh"] = estoques
    df["perda_reservatorio_kwh"] = perdas
    nec = df["necessidade_kwh"]
    df["fracao_solar"] = (df["solar_usado_kwh"] / nec.where(nec > 0)).fillna(1.0)
    df["e_b_kwh"] = df["e_l0_kwh"] * (1 - df["fracao_solar"])
    df["agua_b_l"] = df["agua_l0_l"] * solar.fator_uso_agua_quente

    df.attrs["vazao_l_min"] = vazao
    df.attrs["delta_t_max_c"] = delta_t_max
    df.attrs["temp_agua_fria_minima_c"] = temp_fria_mais_baixa
    return df


COLUNAS_SOMA = [
    "e_l0_kwh", "e_a_kwh", "e_b_kwh", "necessidade_kwh", "solar_usado_kwh",
    "solar_disponivel_kwh", "perda_reservatorio_kwh", "agua_l0_l", "agua_a_l", "agua_b_l",
]


def totais_por_ano(sim: pd.DataFrame) -> pd.DataFrame:
    """Soma de cada ano da série (útil para ver a variação entre anos)."""
    anual = sim.groupby("ano")[COLUNAS_SOMA].sum()
    anual["dias_com_complemento"] = sim.assign(c=sim["fracao_solar"] < 0.99).groupby("ano")["c"].sum()
    anual["fracao_solar"] = anual["solar_usado_kwh"] / anual["necessidade_kwh"]
    return anual


def ano_tipico(sim: pd.DataFrame) -> pd.DataFrame:
    """Média, entre os anos da série, de cada mês do calendário (12 linhas)."""
    por_mes = sim.groupby(["ano", "mes"])[COLUNAS_SOMA].sum()
    por_mes["dias"] = sim.groupby(["ano", "mes"]).size()
    tipico = por_mes.groupby("mes").mean()
    tipico["fracao_solar"] = tipico["solar_usado_kwh"] / tipico["necessidade_kwh"]
    tipico["temp_agua_fria_c"] = sim.groupby("mes")["temp_agua_fria_c"].mean()
    tipico["h_inclinado_kwh_m2_dia"] = sim.groupby("mes")["h_inclinado_kwh_m2_dia"].mean()
    return tipico
