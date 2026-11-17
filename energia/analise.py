"""Análise comparativa: energia, custo, investimento, retorno, CO2 e água."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import pandas as pd

from .dados import BaseDados
from .formatacao import num, pct, reais
from .modelo import (
    Familia, PraticasEficientes, Premissas, SistemaSolar, ano_tipico, simular, totais_por_ano,
)
from .tarifa import PERFIS, aliquota_icms, valor_conta

NOMES = {
    "L0": "Chuveiro elétrico convencional (situação atual)",
    "A": "Chuveiro elétrico com práticas de uso eficiente",
    "B": "Aquecimento solar térmico + chuveiro como complemento",
}
COLUNA = {"L0": "e_l0_kwh", "A": "e_a_kwh", "B": "e_b_kwh"}
AGUA = {"L0": "agua_l0_l", "A": "agua_a_l", "B": "agua_b_l"}


@dataclass(frozen=True)
class Cenario:
    familia: Familia = field(default_factory=Familia)
    praticas: PraticasEficientes = field(default_factory=PraticasEficientes)
    solar: SistemaSolar = field(default_factory=SistemaSolar)
    premissas: Premissas = field(default_factory=Premissas)
    perfil_tarifario: str = "convencional"
    consumo_conta_kwh: float = 200.0

    def validar(self) -> None:
        if self.perfil_tarifario not in PERFIS:
            raise ValueError(f"Perfil tarifário inválido: {self.perfil_tarifario}")
        if not 0 < self.consumo_conta_kwh <= 3000:
            raise ValueError("Consumo da conta deve estar entre 1 e 3.000 kWh/mês.")


@dataclass
class Resultado:
    cenario: Cenario
    derivados: dict
    alternativas: dict
    mensal: pd.DataFrame
    por_ano: pd.DataFrame
    avisos: list

    def para_dict(self) -> dict:
        """Versão serializável (usada como contexto do assistente)."""
        meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
        m = self.mensal
        return {
            "entradas": asdict(self.cenario),
            "derivados": self.derivados,
            "alternativas": self.alternativas,
            "mensal_kwh": {
                alt: {meses[i - 1]: round(float(m.loc[i, COLUNA[alt]]), 1) for i in m.index}
                for alt in COLUNA
            },
            "fracao_solar_mensal": {meses[i - 1]: round(float(m.loc[i, "fracao_solar"]), 3) for i in m.index},
            "avisos": self.avisos,
        }


def analisar(cenario: Cenario, base: BaseDados) -> Resultado:
    cenario.validar()
    sim = simular(base.clima, cenario.familia, cenario.praticas, cenario.solar, cenario.premissas)
    mensal = ano_tipico(sim)
    por_ano = totais_por_ano(sim)
    avisos: list[str] = []

    # O consumo da conta inclui o chuveiro atual (L0); o resto ("outros") não muda.
    e_l0_mes = float(mensal["e_l0_kwh"].mean())
    outros = cenario.consumo_conta_kwh - e_l0_mes
    if outros < 0:
        avisos.append(
            f"O consumo informado ({num(cenario.consumo_conta_kwh)} kWh/mês) é menor que o "
            f"consumo estimado só do chuveiro ({num(e_l0_mes)} kWh/mês). Confira a potência, o tempo "
            "de banho ou o valor da conta. Para continuar, consideramos 0 kWh para os outros aparelhos."
        )
        outros = 0.0

    fe = base.fator_emissao_mensal.reindex(mensal.index)
    perfil = cenario.perfil_tarifario
    for alt in COLUNA:
        consumo_total = outros + mensal[COLUNA[alt]]
        mensal[f"conta_{alt}_rs"] = [valor_conta(c, perfil, base.tarifa) for c in consumo_total]
        mensal[f"co2_{alt}_kg"] = mensal[COLUNA[alt]] * fe

    alternativas = {}
    conta_l0_ano = float(mensal["conta_L0_rs"].sum())
    kwh_l0_ano = float(mensal["e_l0_kwh"].sum())
    for alt in COLUNA:
        kwh_ano = float(mensal[COLUNA[alt]].sum())
        conta_ano = float(mensal[f"conta_{alt}_rs"].sum())
        economia_rs = conta_l0_ano - conta_ano
        investimento = cenario.solar.investimento_rs if alt == "B" else 0.0
        payback = investimento / economia_rs if (investimento > 0 and economia_rs > 0) else None
        alternativas[alt] = {
            "nome": NOMES[alt],
            "chuveiro_kwh_ano": round(kwh_ano, 1),
            "chuveiro_kwh_mes_medio": round(kwh_ano / 12, 1),
            "economia_kwh_ano": round(kwh_l0_ano - kwh_ano, 1),
            "reducao_consumo_chuveiro": round(1 - kwh_ano / kwh_l0_ano, 3),
            "conta_energia_ano_rs": round(conta_ano, 2),
            "conta_energia_mes_medio_rs": round(conta_ano / 12, 2),
            "economia_ano_rs": round(economia_rs, 2),
            "economia_mes_medio_rs": round(economia_rs / 12, 2),
            "investimento_rs": round(investimento, 2),
            "retorno_simples_anos": round(payback, 1) if payback is not None else None,
            "co2_kg_ano": round(float(mensal[f"co2_{alt}_kg"].sum()), 1),
            "agua_m3_ano": round(float(mensal[AGUA[alt]].sum()) / 1000, 1),
        }

    b = alternativas["B"]
    b["fracao_solar_ano"] = round(float(mensal["solar_usado_kwh"].sum() / mensal["necessidade_kwh"].sum()), 3)
    b["dias_com_complemento_por_ano"] = round(float(por_ano["dias_com_complemento"].mean()), 0)
    b["chuveiro_kwh_ano_min"] = round(float(por_ano["e_b_kwh"].min()), 1)
    b["chuveiro_kwh_ano_max"] = round(float(por_ano["e_b_kwh"].max()), 1)
    b["ano_pior"] = int(por_ano["e_b_kwh"].idxmax())
    b["ano_melhor"] = int(por_ano["e_b_kwh"].idxmin())
    b["mes_menor_fracao_solar"] = int(mensal["fracao_solar"].idxmin())
    b["menor_fracao_solar_mensal"] = round(float(mensal["fracao_solar"].min()), 3)

    consumo_atual = outros + mensal["e_l0_kwh"]
    derivados = {
        "vazao_chuveiro_l_min": round(float(sim.attrs["vazao_l_min"]), 2),
        "temp_agua_fria_minima_c": round(float(sim.attrs["temp_agua_fria_minima_c"]), 1),
        "consumo_outros_aparelhos_kwh_mes": round(outros, 1),
        "consumo_chuveiro_atual_kwh_mes": round(e_l0_mes, 1),
        "participacao_chuveiro_na_conta": round(e_l0_mes / max(cenario.consumo_conta_kwh, 1e-9), 3),
        "conta_atual_mes_medio_rs": round(conta_l0_ano / 12, 2),
        "icms_atual": aliquota_icms(float(consumo_atual.mean()), base.tarifa),
        "periodo_clima": f"{int(sim['ano'].min())}-{int(sim['ano'].max())}",
        "ano_fator_emissao": 2025,
        "perfil_tarifario_descricao": PERFIS[perfil],
    }
    return Resultado(cenario, derivados, alternativas, mensal, por_ano, avisos)


MESES_NOME = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
              "agosto", "setembro", "outubro", "novembro", "dezembro"]


def recomendacoes(res: Resultado, sensibilidade: list[dict] | None = None) -> list[str]:
    """Recomendações determinísticas, derivadas apenas dos números calculados."""
    a, b = res.alternativas["A"], res.alternativas["B"]
    recs = [
        f"Comece pelas práticas eficientes (A): custo zero, economia estimada de "
        f"{reais(a['economia_ano_rs'])} por ano ({num(a['economia_kwh_ano'])} kWh/ano) e "
        f"{num(res.alternativas['L0']['agua_m3_ano'] - a['agua_m3_ano'], 1)} mil litros de água a menos por ano."
    ]
    if b["retorno_simples_anos"] is not None:
        texto = (
            f"O aquecimento solar (B) reduz até {pct(b['reducao_consumo_chuveiro'])} do consumo do chuveiro "
            f"(economia estimada de {reais(b['economia_ano_rs'])}/ano), mas exige cerca de "
            f"{reais(b['investimento_rs'], 0)}. Retorno simples estimado: {num(b['retorno_simples_anos'], 1)} anos "
            "(sem juros e sem reajustes de tarifa)."
        )
        pess = [s for s in (sensibilidade or []) if s["id"] == "pessimista"]
        if pess:
            p = pess[0]
            ret = f"{num(p['retorno_simples_anos'], 1)} anos" if p["retorno_simples_anos"] else "não se paga"
            texto += (f" No cenário pessimista (coletor de menor desempenho e ducha de maior vazão) a economia cai para "
                      f"{reais(p['economia_ano_rs'])}/ano e o retorno vai para {ret}.")
        recs.append(texto)
    else:
        recs.append("Com os dados informados, a economia do solar (B) não paga o investimento.")
    if res.cenario.perfil_tarifario == "tarifa_social":
        recs.append(
            "Na Tarifa Social os primeiros 80 kWh do mês já são gratuitos; por isso a economia em reais "
            "é menor que a economia em kWh e o retorno do solar demora mais."
        )
    recs.append(
        f"O chuveiro solar precisa mais do complemento elétrico em {MESES_NOME[b['mes_menor_fracao_solar'] - 1]} "
        f"(o sol cobre {pct(b['menor_fracao_solar_mensal'])} da necessidade nesse mês, em média) e em "
        f"sequências de dias nublados (cerca de {num(b['dias_com_complemento_por_ano'])} dias por ano)."
    )
    recs.append(
        "Se optar pelo solar, escolha coletor e reservatório com etiqueta INMETRO e instalação por "
        "profissional seguindo a ABNT NBR 15569. As práticas de A continuam valendo junto com o solar."
    )
    return recs


SENSIBILIDADES_SOLAR = [
    {
        "id": "base",
        "rotulo": "Referência: coletor classe A (Komeco KOCS AP 2M) e mesma vazão do chuveiro elétrico",
        "ajustes": {},
        "fonte": "Parâmetros de referência (dados/parametros.json).",
    },
    {
        "id": "coletor_minimo",
        "rotulo": "Coletor com o menor desempenho aceito pelo INMETRO (PMEe 52,3 kWh/mês·m²)",
        "ajustes": {"pmee_kwh_mes_m2": 52.3},
        "fonte": "INMETRO, Portaria 301/2012 (limite inferior da classe E).",
    },
    {
        "id": "vazao_maior",
        "rotulo": "Família passa a usar ducha de maior vazão com o solar (o dobro da água quente)",
        "ajustes": {"fator_uso_agua_quente": 8.4 / 4.2},
        "fonte": "Estudo da USP citado pela ABINEE e pelo Idec: chuveiro elétrico 4,2 L/min; aquecedor solar 8,4 L/min.",
    },
    {
        "id": "pessimista",
        "rotulo": "Combinação pessimista: coletor mínimo + ducha de maior vazão",
        "ajustes": {"pmee_kwh_mes_m2": 52.3, "fator_uso_agua_quente": 8.4 / 4.2},
        "fonte": "Combinação dos dois casos acima.",
    },
]


def sensibilidade_solar(cenario: Cenario, base: BaseDados) -> list[dict]:
    """Recalcula a alternativa B variando premissas incertas (todas com fonte)."""
    from dataclasses import replace

    linhas = []
    for caso in SENSIBILIDADES_SOLAR:
        solar = replace(cenario.solar, **caso["ajustes"])
        res = analisar(replace(cenario, solar=solar), base)
        b = res.alternativas["B"]
        linhas.append({
            "id": caso["id"],
            "rotulo": caso["rotulo"],
            "fonte": caso["fonte"],
            "fracao_solar_ano": b["fracao_solar_ano"],
            "chuveiro_kwh_ano": b["chuveiro_kwh_ano"],
            "economia_ano_rs": b["economia_ano_rs"],
            "retorno_simples_anos": b["retorno_simples_anos"],
            "agua_m3_ano": b["agua_m3_ano"],
            "dias_com_complemento_por_ano": b["dias_com_complemento_por_ano"],
        })
    return linhas
