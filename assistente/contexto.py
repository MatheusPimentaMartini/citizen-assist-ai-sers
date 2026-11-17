"""Ficha de cálculo: o texto (com todos os números permitidos) que fundamenta as respostas."""
from __future__ import annotations

from energia.analise import MESES_NOME, Resultado
from energia.formatacao import num, pct, reais

FONTES_RESUMO = (
    "Fontes dos cálculos: ANEEL (tarifa Enel SP 2026) · Open-Meteo e CRESESB (clima e sol) · "
    "INMETRO e Idec (chuveiro e coletor) · SINAPI 103517 (custo do kit) · MCTI 2025 (CO₂) · Sabesp (tempo de banho). "
    "Detalhes na aba Método."
)

FONTES_CURTAS = [
    "Clima: Open-Meteo (irradiação diária e temperatura, 2016-2025) e CRESESB/Atlas Brasileiro de Energia Solar 2017 (irradiação no plano inclinado a 34°).",
    "Tarifa: ANEEL, REH 3.596/2026 da Enel SP (vigência 04/07/2026 a 03/07/2027) + ICMS-SP e PIS/COFINS estimado.",
    "Chuveiro: INMETRO/Idec (eficiência acima de 95%; 5.500 W = 88 kWh/mês na etiqueta) e literatura ENCAC/ANTAC (40 °C, 8 min).",
    "Solar: SINAPI 103517 (kit 2 m² + 200 L), coletor Komeco KOCS AP 2M (INMETRO classe A), INMETRO Portaria 301/2012 e ABNT NBR 15569.",
    "Emissões: MCTI/SIRENE, fator médio mensal do SIN de 2025.",
    "Hábito eficiente: Sabesp recomenda banhos de até 5 minutos.",
]

LIMITACOES = [
    "São estimativas para um ano típico (clima 2016-2025), não garantia de economia.",
    "A conta considera só energia + PIS/COFINS + ICMS; não inclui bandeiras, iluminação pública ou reajustes futuros.",
    "A temperatura da água fria foi aproximada pela temperatura média do ar de cada mês.",
    "O coletor solar foi modelado pelo ensaio INMETRO (condição padrão); no uso real pode render menos. Por isso há uma análise de sensibilidade.",
    "O investimento do SINAPI é média nacional e não inclui conexões, bomba e válvulas; o preço real deve ser orçado.",
    "Na alternativa A, o ajuste de potência supõe chuveiro com controle de temperatura; com chuveiro de 2 posições a economia pode ser menor.",
    "Retorno simples: não considera juros, inflação nem manutenção.",
]


def montar_ficha(res: Resultado, sensibilidade: list[dict], recs: list[str], perfis: list[dict] | None = None) -> str:
    c = res.cenario
    d = res.derivados
    L0, A, B = (res.alternativas[k] for k in ("L0", "A", "B"))
    f = c.familia
    linhas = [
        "## Situação informada",
        f"- Família de {f.pessoas} pessoas, banho de {num(f.minutos_banho)} min, chuveiro de {num(f.potencia_w)} W.",
        f"- Consumo total da conta: {num(c.consumo_conta_kwh)} kWh/mês; perfil tarifário: {d['perfil_tarifario_descricao']}.",
        f"- Chuveiro hoje: {num(d['consumo_chuveiro_atual_kwh_mes'], 1)} kWh/mês "
        f"({pct(d['participacao_chuveiro_na_conta'])} do consumo da casa); conta de energia média {reais(d['conta_atual_mes_medio_rs'])}/mês.",
        f"- ICMS aplicado na conta atual: {pct(d['icms_atual'])} (SP: isento até 90 kWh, 12% até 200 kWh, 18% acima); PIS/COFINS estimado em 6%.",
        f"- Vazão estimada do chuveiro: {num(d['vazao_chuveiro_l_min'], 2)} L/min; água fria no mês mais frio: {num(d['temp_agua_fria_minima_c'], 1)} °C.",
        "",
        "## Comparação (ano típico)",
    ]
    for chave, alt in (("L0", L0), ("A", A), ("B", B)):
        if alt["retorno_simples_anos"] is not None:
            retorno = f"{num(alt['retorno_simples_anos'], 1)} anos (retorno simples)"
        else:
            retorno = "sem investimento" if alt["investimento_rs"] == 0 else "não se paga"
        linhas += [
            f"### {chave} · {alt['nome']}",
            f"- consumo do chuveiro: {num(alt['chuveiro_kwh_ano'])} kWh/ano ({num(alt['chuveiro_kwh_mes_medio'], 1)} kWh/mês)",
            f"- conta de energia da casa: {reais(alt['conta_energia_mes_medio_rs'])}/mês",
            f"- energia economizada em relação a L0: {num(alt['economia_kwh_ano'])} kWh/ano ({pct(alt['reducao_consumo_chuveiro'])} do consumo do chuveiro)",
            f"- economia na conta em relação a L0: {reais(alt['economia_ano_rs'])}/ano ({reais(alt['economia_mes_medio_rs'])}/mês)",
            f"- investimento: {reais(alt['investimento_rs'])}; retorno: {retorno}",
            f"- CO2 do chuveiro: {num(alt['co2_kg_ano'], 1)} kg/ano; água do banho: {num(alt['agua_m3_ano'], 1)} m³/ano",
        ]
    linhas += [
        f"- Na alternativa A o banho cai para {num(c.praticas.minutos_banho)} min"
        + (" e a potência é ajustada ao clima (posição verão nos meses quentes)." if c.praticas.ajustar_potencia_no_calor else "."),
        f"- Na alternativa B o sol cobre {pct(B['fracao_solar_ano'], 1)} da energia do banho no ano; "
        f"o mês mais difícil é {MESES_NOME[B['mes_menor_fracao_solar'] - 1]} ({pct(B['menor_fracao_solar_mensal'], 1)}); "
        f"cerca de {num(B['dias_com_complemento_por_ano'])} dias/ano precisam de complemento elétrico; "
        f"entre os anos de 2016-2025 o chuveiro com solar variou de {num(B['chuveiro_kwh_ano_min'], 1)} a {num(B['chuveiro_kwh_ano_max'], 1)} kWh/ano.",
        "",
        "## Sensibilidade da alternativa B (premissas incertas)",
    ]
    for s in sensibilidade:
        ret = f"{num(s['retorno_simples_anos'], 1)} anos" if s["retorno_simples_anos"] is not None else "não se paga"
        linhas.append(
            f"- {s['rotulo']}: sol cobre {pct(s['fracao_solar_ano'], 1)}; economia {reais(s['economia_ano_rs'])}/ano; "
            f"retorno {ret}; água {num(s['agua_m3_ano'], 1)} m³/ano. Fonte: {s['fonte']}"
        )
    if perfis:
        linhas += ["", "## Mesma família em outros perfis tarifários (mesmo consumo da conta)",
                   "- Regras (Lei 15.235/2025): Tarifa Social = CadÚnico com renda por pessoa de até 1/2 salário mínimo, "
                   "primeiros 80 kWh/mês gratuitos; Desconto Social = renda por pessoa entre 1/2 e 1 salário mínimo, "
                   "até 120 kWh/mês com tarifa reduzida (sem CDE)."]
        for pf in perfis:
            ret = f"{num(pf['retorno_b_anos'], 1)} anos" if pf["retorno_b_anos"] is not None else "não se paga"
            linhas.append(
                f"- {pf['descricao']}: conta de energia hoje {reais(pf['conta_atual_mes_rs'])}/mês; "
                f"economia na conta com A {reais(pf['economia_a_ano_rs'])}/ano; com B {reais(pf['economia_b_ano_rs'])}/ano; "
                f"retorno de B {ret}."
            )
    linhas += ["", "## Mês a mês (kWh do chuveiro, ano típico)"]
    for i in res.mensal.index:
        m = res.mensal.loc[i]
        linhas.append(
            f"- {MESES_NOME[i - 1]}: L0 {num(m['e_l0_kwh'], 1)}; A {num(m['e_a_kwh'], 1)}; B {num(m['e_b_kwh'], 1)}; "
            f"sol cobre {pct(m['fracao_solar'], 1)}; água fria {num(m['temp_agua_fria_c'], 1)} °C."
        )
    linhas += ["", "## Recomendações calculadas"] + [f"- {r}" for r in recs]
    linhas += ["", "## Limitações"] + [f"- {x}" for x in LIMITACOES]
    linhas += ["", "## Fontes"] + [f"- {x}" for x in FONTES_CURTAS]
    if res.avisos:
        linhas += ["", "## Avisos"] + [f"- {x}" for x in res.avisos]
    return "\n".join(linhas)
