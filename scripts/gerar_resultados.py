"""Gera as tabelas de resultados (resultados/*.csv e docs/resultados.md) a partir dos dados do repositório.

Uso:  python scripts/gerar_resultados.py
Os números do README e do vídeo devem vir deste script, para serem reproduzíveis.
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from energia import BaseDados, Cenario, Familia, analisar, recomendacoes  # noqa: E402
from energia.analise import MESES_NOME, sensibilidade_solar  # noqa: E402
from energia.formatacao import num, pct, reais  # noqa: E402

SAIDA_CSV = RAIZ / "resultados"
SAIDA_MD = RAIZ / "docs" / "resultados.md"


def tabela_md(df: pd.DataFrame) -> str:
    cab = "| " + " | ".join(df.columns) + " |"
    sep = "| " + " | ".join("---" for _ in df.columns) + " |"
    linhas = ["| " + " | ".join(str(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([cab, sep, *linhas])


def linha_alt(chave: str, alt: dict) -> dict:
    return {
        "Alternativa": f"{chave} · {alt['nome']}",
        "Chuveiro (kWh/ano)": num(alt["chuveiro_kwh_ano"]),
        "Redução": pct(alt["reducao_consumo_chuveiro"], 1),
        "Conta de energia (R$/mês)": reais(alt["conta_energia_mes_medio_rs"]),
        "Economia (R$/ano)": reais(alt["economia_ano_rs"]),
        "Investimento": reais(alt["investimento_rs"]),
        "Retorno simples": f"{num(alt['retorno_simples_anos'], 1)} anos" if alt["retorno_simples_anos"] else "-",
        "CO₂ (kg/ano)": num(alt["co2_kg_ano"], 1),
        "Água (m³/ano)": num(alt["agua_m3_ano"], 1),
    }


def main() -> None:
    base = BaseDados.carregar()
    SAIDA_CSV.mkdir(exist_ok=True)
    partes = [
        "# Resultados",
        "",
        "> Gerado automaticamente por `python scripts/gerar_resultados.py` a partir de `dados/`. "
        "Valores são **estimativas** para um ano típico (clima 2016-2025), não garantias.",
        "",
    ]

    # 1) Cenário de referência
    ref = Cenario()
    res = analisar(ref, base)
    sens = sensibilidade_solar(ref, base)
    d = res.derivados
    comp = pd.DataFrame([linha_alt(k, v) for k, v in res.alternativas.items()])
    pd.DataFrame(res.alternativas).T.to_csv(SAIDA_CSV / "comparacao_referencia.csv")
    partes += [
        "## 1. Cenário de referência",
        "",
        f"Família de 4 pessoas, banho de 8 min, chuveiro de 5.500 W, conta de 200 kWh/mês, tarifa residencial "
        f"convencional da Enel SP. O chuveiro representa {num(d['consumo_chuveiro_atual_kwh_mes'], 1)} kWh/mês "
        f"({pct(d['participacao_chuveiro_na_conta'])} do consumo) e a parcela de energia da conta é "
        f"{reais(d['conta_atual_mes_medio_rs'])}/mês. Vazão estimada: {num(d['vazao_chuveiro_l_min'], 2)} L/min.",
        "",
        tabela_md(comp),
        "",
        "**Recomendações geradas pelo código:**",
        "",
        *[f"- {r}" for r in recomendacoes(res, sens)],
        "",
    ]

    # 2) Mês a mês
    m = res.mensal
    mensal = pd.DataFrame({
        "Mês": [MESES_NOME[i - 1] for i in m.index],
        "Água fria (°C)": [num(v, 1) for v in m["temp_agua_fria_c"]],
        "Sol no coletor (kWh/m²·dia)": [num(v, 2) for v in m["h_inclinado_kwh_m2_dia"]],
        "L0 (kWh)": [num(v, 1) for v in m["e_l0_kwh"]],
        "A (kWh)": [num(v, 1) for v in m["e_a_kwh"]],
        "B (kWh)": [num(v, 1) for v in m["e_b_kwh"]],
        "Sol cobre (B)": [pct(v, 1) for v in m["fracao_solar"]],
        "Fator CO₂ 2025 (kg/kWh)": [num(v, 4) for v in base.fator_emissao_mensal.reindex(m.index)],
    })
    m.to_csv(SAIDA_CSV / "mensal_referencia.csv")
    partes += ["## 2. Mês a mês (cenário de referência)", "", tabela_md(mensal), ""]

    # 3) Sensibilidade do solar
    tab_s = pd.DataFrame([{
        "Cenário": s["rotulo"],
        "Sol cobre": pct(s["fracao_solar_ano"], 1),
        "Dias com complemento/ano": num(s["dias_com_complemento_por_ano"]),
        "Economia (R$/ano)": reais(s["economia_ano_rs"]),
        "Retorno simples": f"{num(s['retorno_simples_anos'], 1)} anos" if s["retorno_simples_anos"] else "-",
        "Água (m³/ano)": num(s["agua_m3_ano"], 1),
        "Fonte da variação": s["fonte"],
    } for s in sens])
    pd.DataFrame(sens).to_csv(SAIDA_CSV / "sensibilidade_solar.csv", index=False)
    partes += [
        "## 3. Sensibilidade da alternativa B",
        "",
        "O cenário de referência é um **limite superior** (coletor classe A, mesma vazão do chuveiro elétrico). "
        "Os demais casos usam valores com fonte para mostrar até onde o resultado pode cair.",
        "",
        tabela_md(tab_s),
        "",
    ]

    # 4) Perfis tarifários e consumo da casa
    linhas = []
    for perfil, consumo in [("convencional", 150), ("convencional", 200), ("convencional", 250), ("convencional", 300),
                            ("desconto_social", 150), ("tarifa_social", 150)]:
        r = analisar(replace(ref, perfil_tarifario=perfil, consumo_conta_kwh=consumo), base)
        a, b = r.alternativas["A"], r.alternativas["B"]
        linhas.append({
            "Perfil": perfil.replace("_", " "),
            "Conta (kWh/mês)": consumo,
            "Conta hoje (R$/mês)": reais(r.derivados["conta_atual_mes_medio_rs"]),
            "Economia A (R$/ano)": reais(a["economia_ano_rs"]),
            "Economia B (R$/ano)": reais(b["economia_ano_rs"]),
            "Retorno B": f"{num(b['retorno_simples_anos'], 1)} anos" if b["retorno_simples_anos"] else "-",
        })
    tab_p = pd.DataFrame(linhas)
    tab_p.to_csv(SAIDA_CSV / "perfis_tarifarios.csv", index=False)
    partes += [
        "## 4. Efeito da tarifa e do consumo total da casa (mesma família)",
        "",
        "A economia em reais depende do consumo total (faixas de ICMS de SP) e do perfil tarifário. "
        "Na Tarifa Social os primeiros 80 kWh já são gratuitos, então a mesma economia em kWh vale menos em reais.",
        "",
        tabela_md(tab_p),
        "",
    ]

    # 5) Chuveiro de 7.500 W
    r75 = analisar(replace(ref, familia=Familia(4, 8, 7500), consumo_conta_kwh=250), base)
    comp75 = pd.DataFrame([linha_alt(k, v) for k, v in r75.alternativas.items()])
    partes += [
        "## 5. Variação: chuveiro de 7.500 W (220 V), conta de 250 kWh/mês",
        "",
        tabela_md(comp75),
        "",
    ]

    # 6) Variação entre anos (solar)
    pa = res.por_ano
    tab_a = pd.DataFrame({
        "Ano": pa.index,
        "Sol cobre": [pct(v, 1) for v in pa["fracao_solar"]],
        "Dias com complemento": [int(v) for v in pa["dias_com_complemento"]],
        "Chuveiro com solar (kWh/ano)": [num(v, 1) for v in pa["e_b_kwh"]],
    })
    partes += ["## 6. Alternativa B ano a ano (cenário de referência)", "", tabela_md(tab_a), ""]

    SAIDA_MD.write_text("\n".join(partes), encoding="utf-8")
    print(f"Escrito: {SAIDA_MD.relative_to(RAIZ)} e {SAIDA_CSV.relative_to(RAIZ)}/*.csv")


if __name__ == "__main__":
    main()
