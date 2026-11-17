"""Citizen Assist AI - Energia no banho (Global Solution 2026.2 - SERS / FIAP).

Rodar localmente:  streamlit run app.py
Online:            Streamlit Community Cloud (chave do Ollama Cloud em Settings > Secrets).
"""
from __future__ import annotations

import threading
import time

import pandas as pd
import streamlit as st

from assistente import ConfigIA, responder
from assistente.contexto import FONTES_CURTAS, FONTES_RESUMO, LIMITACOES, montar_ficha
from assistente.modo_calculo import normalizar
from energia import (
    BaseDados, Cenario, Familia, PraticasEficientes, Premissas, SistemaSolar, analisar, recomendacoes,
)
from energia.analise import MESES_NOME, sensibilidade_solar
from energia.formatacao import num, pct, reais
from energia.tarifa import PERFIS

LIMITE_IA_POR_SESSAO = 15
LIMITE_IA_POR_HORA = 120  # todas as sessões somadas (protege os créditos da conta)
REPO = "https://github.com/MatheusPimentaMartini/citizen-assist-ai-sers"

st.set_page_config(page_title="Citizen Assist AI · Energia no banho", page_icon="🚿", layout="wide")


@st.cache_resource(show_spinner=False)
def base_dados() -> BaseDados:
    return BaseDados.carregar()


@st.cache_resource(show_spinner=False)
def estado_global() -> dict:
    """Cache de respostas da IA e contador de chamadas compartilhados entre sessões."""
    return {"lock": threading.Lock(), "respostas": {}, "chamadas": []}


@st.cache_data(show_spinner=False)
def calcular(pessoas, minutos, potencia, consumo, perfil, minutos_a, ajuste, investimento):
    cenario = Cenario(
        familia=Familia(pessoas, minutos, potencia),
        praticas=PraticasEficientes(minutos_a, ajuste),
        solar=SistemaSolar(investimento_rs=investimento),
        premissas=Premissas(),
        perfil_tarifario=perfil,
        consumo_conta_kwh=consumo,
    )
    base = base_dados()
    res = analisar(cenario, base)
    sens = sensibilidade_solar(cenario, base)
    return res, sens, recomendacoes(res, sens)


def configuracao_ia() -> ConfigIA:
    try:
        segredos = st.secrets
    except Exception:
        segredos = None
    return ConfigIA.carregar(segredos)


def pode_chamar_ia() -> tuple[bool, str]:
    if st.session_state.get("chamadas_ia", 0) >= LIMITE_IA_POR_SESSAO:
        return False, f"Limite de {LIMITE_IA_POR_SESSAO} perguntas à IA nesta sessão atingido (protege os créditos)."
    g = estado_global()
    with g["lock"]:
        agora = time.time()
        g["chamadas"] = [t for t in g["chamadas"] if agora - t < 3600]
        if len(g["chamadas"]) >= LIMITE_IA_POR_HORA:
            return False, "Muitas perguntas à IA na última hora em todo o app; tente mais tarde."
    return True, ""


# ----------------------------------------------------------------------------- entradas
with st.sidebar:
    st.header("🏠 Sua casa")
    pessoas = st.number_input("Pessoas que tomam banho por dia", 1, 10, 4)
    minutos = st.slider("Minutos por banho (hoje)", 2, 20, 8)
    potencia = st.number_input(
        "Potência do chuveiro (W)", 2000, 9000, 5500, step=100,
        help="Na etiqueta ou embalagem do chuveiro (posição inverno). Comuns: 5.500 W (127 V) e 7.500 W (220 V).",
    )
    consumo = st.number_input(
        "Consumo da conta de luz (kWh/mês)", 30, 1000, 200, step=10,
        help="Na conta da Enel aparece como consumo em kWh. Use a média dos últimos meses.",
    )
    perfil = st.radio("Tarifa", list(PERFIS), format_func=lambda k: PERFIS[k])
    st.header("A · Práticas eficientes")
    minutos_a = st.slider("Minutos por banho com a prática", 2, minutos, min(5, minutos))
    ajuste = st.checkbox("Usar posição verão quando a água já chega morna", True)
    st.header("B · Aquecimento solar")
    investimento = st.number_input(
        "Investimento no kit solar (R$)", 0.0, 30000.0, 3359.57, step=100.0,
        help="Referência SINAPI 103517 (kit 2 m² + 200 L instalado, set/2026). Troque pelo seu orçamento.",
    )

res, sens, recs = calcular(pessoas, minutos, potencia, consumo, perfil, minutos_a, ajuste, investimento)
L0, A, B = (res.alternativas[k] for k in ("L0", "A", "B"))
d = res.derivados

st.title("🚿 Citizen Assist AI · Energia no banho")
st.caption(
    "Para famílias que moram em casas na Grande São Paulo e usam chuveiro elétrico. Compara o chuveiro atual, "
    "práticas de uso eficiente e aquecimento solar térmico para a **mesma necessidade** (banho a 40 °C). "
    "Projeto acadêmico FIAP · Global Solution 2026.2 · SERS. **Valores são estimativas, não garantias.**"
)
for aviso in res.avisos:
    st.warning(aviso)

aba_comp, aba_chat, aba_metodo = st.tabs(["📊 Comparação", "💬 Assistente", "📚 Método, fontes e limitações"])

# ----------------------------------------------------------------------------- comparação
with aba_comp:
    c1, c2, c3 = st.columns(3)
    c1.metric("Chuveiro hoje", f"{num(d['consumo_chuveiro_atual_kwh_mes'], 1)} kWh/mês")
    c2.metric("Parte do consumo da casa", pct(d["participacao_chuveiro_na_conta"]))
    c3.metric("Conta de energia hoje (média)", reais(d["conta_atual_mes_medio_rs"]) + "/mês")

    st.subheader("As três alternativas")
    cols = st.columns(3)
    for col, (chave, alt) in zip(cols, (("L0", L0), ("A", A), ("B", B))):
        with col.container(border=True):
            st.markdown(f"**{chave} · {alt['nome']}**")
            st.metric(
                "Conta de energia (média)", reais(alt["conta_energia_mes_medio_rs"]) + "/mês",
                delta=None if chave == "L0" else f"-{reais(alt['economia_mes_medio_rs'])}/mês",
                delta_color="inverse",
            )
            st.write(f"Chuveiro: **{num(alt['chuveiro_kwh_mes_medio'], 1)} kWh/mês**")
            if chave != "L0":
                st.write(f"Economia: **{reais(alt['economia_ano_rs'])}/ano** ({pct(alt['reducao_consumo_chuveiro'])} do chuveiro)")
            st.write(f"Investimento: **{reais(alt['investimento_rs'])}**")
            if alt["retorno_simples_anos"] is not None:
                st.write(f"Retorno simples: **~{num(alt['retorno_simples_anos'], 1)} anos**")
            st.write(f"CO₂: {num(alt['co2_kg_ano'], 1)} kg/ano · Água: {num(alt['agua_m3_ano'], 1)} m³/ano")

    st.subheader("Recomendações (calculadas)")
    for r in recs:
        st.markdown(f"- {r}")

    st.subheader("Consumo do chuveiro mês a mês (ano típico, clima 2016-2025)")
    mensal = pd.DataFrame(
        {
            "L0 · convencional": res.mensal["e_l0_kwh"].values,
            "A · uso eficiente": res.mensal["e_a_kwh"].values,
            "B · solar + complemento": res.mensal["e_b_kwh"].values,
        },
        index=pd.Index([f"{i:02d}-{MESES_NOME[i - 1][:3]}" for i in res.mensal.index], name="mês"),
    )
    st.bar_chart(mensal, stack=False, y_label="kWh/mês")
    st.caption(
        f"No solar, o sol cobre {pct(B['fracao_solar_ano'], 1)} da energia do banho no ano (cenário de referência); "
        f"o chuveiro complementa em cerca de {num(B['dias_com_complemento_por_ano'])} dias por ano, "
        "nas sequências de dias nublados."
    )

    st.subheader("Sensibilidade do solar (premissas incertas)")
    st.dataframe(
        pd.DataFrame([
            {
                "Cenário": s["rotulo"],
                "Sol cobre": pct(s["fracao_solar_ano"], 1),
                "Economia (R$/ano)": reais(s["economia_ano_rs"]),
                "Retorno simples": f"{num(s['retorno_simples_anos'], 1)} anos" if s["retorno_simples_anos"] else "não se paga",
                "Água (m³/ano)": num(s["agua_m3_ano"], 1),
                "Fonte": s["fonte"],
            }
            for s in sens
        ]),
        hide_index=True, width="stretch",
    )

    with st.expander("Tabela completa da comparação"):
        st.dataframe(
            pd.DataFrame([
                {
                    "Alternativa": f"{k} · {v['nome']}",
                    "Chuveiro (kWh/ano)": v["chuveiro_kwh_ano"],
                    "Conta de energia (R$/ano)": v["conta_energia_ano_rs"],
                    "Economia (R$/ano)": v["economia_ano_rs"],
                    "Investimento (R$)": v["investimento_rs"],
                    "Retorno simples (anos)": v["retorno_simples_anos"],
                    "CO₂ (kg/ano)": v["co2_kg_ano"],
                    "Água (m³/ano)": v["agua_m3_ano"],
                }
                for k, v in res.alternativas.items()
            ]),
            hide_index=True, width="stretch",
        )

# ----------------------------------------------------------------------------- assistente
config = configuracao_ia()
with aba_chat:
    if config.disponivel:
        st.success(
            f"🤖 IA generativa ativa ({config.descricao}). Ela recebe a ficha de cálculo da sua simulação e só pode usar "
            "esses números; os números da resposta são conferidos automaticamente."
        )
    else:
        st.info(
            "🧮 **Modo cálculo**: a IA generativa não está configurada neste servidor. As respostas são montadas por "
            "regras a partir dos cálculos (não é IA generativa)."
        )
    usar_ia = st.toggle("Usar IA generativa", value=config.disponivel, disabled=not config.disponivel)
    st.caption("Não digite dados pessoais. Com a IA ativa, a pergunta e a ficha de cálculo são enviadas ao Ollama Cloud; o app não guarda conversas.")

    if "mensagens" not in st.session_state:
        st.session_state.mensagens = []
    exemplos = ["Quanto vou economizar?", "O aquecedor solar vale a pena?", "Dicas para gastar menos no banho",
                "E se eu tiver Tarifa Social?", "Qual o impacto ambiental?", "Esses números são confiáveis?"]
    pergunta_botao = None
    bcols = st.columns(3)
    for i, ex in enumerate(exemplos):
        if bcols[i % 3].button(ex, width="stretch"):
            pergunta_botao = ex

    for m in st.session_state.mensagens:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("rotulo"):
                st.caption(m["rotulo"])
                st.caption(FONTES_RESUMO)
            if m.get("nao_conferidos"):
                st.warning("Confira na aba Comparação: estes números não aparecem nos cálculos: " + ", ".join(m["nao_conferidos"]))
            if m.get("aviso"):
                st.info(m["aviso"])

    pergunta = st.chat_input("Pergunte sobre o consumo do banho da sua casa...") or pergunta_botao
    if pergunta:
        st.session_state.mensagens.append({"role": "user", "content": pergunta})
        with st.chat_message("user"):
            st.markdown(pergunta)
        chave = (normalizar(pergunta).strip(), pessoas, minutos, potencia, consumo, perfil, minutos_a, ajuste,
                 investimento, config.modelo)
        g = estado_global()
        resposta = g["respostas"].get(chave) if usar_ia else None
        ia_liberada, motivo = pode_chamar_ia() if (usar_ia and resposta is None) else (usar_ia, "")
        with st.chat_message("assistant"):
            if resposta is None:
                with st.spinner("Calculando a resposta..."):
                    resposta = responder(pergunta, res, sens, recs, config, usar_ia=usar_ia and ia_liberada)
                if usar_ia and not ia_liberada:
                    resposta.aviso = motivo + " Resposta gerada no modo cálculo."
                if resposta.modo == "ia":
                    st.session_state.chamadas_ia = st.session_state.get("chamadas_ia", 0) + 1
                    with g["lock"]:
                        g["chamadas"].append(time.time())
                        if len(g["respostas"]) > 500:
                            g["respostas"].clear()
                        g["respostas"][chave] = resposta
            rotulo = (f"🤖 Resposta da IA generativa ({config.descricao}) com base na ficha de cálculo."
                      if resposta.modo == "ia" else "🧮 Modo cálculo: regras + cálculos (não é IA generativa).")
            st.markdown(resposta.texto)
            st.caption(rotulo)
            st.caption(FONTES_RESUMO)
            if resposta.numeros_nao_conferidos:
                st.warning("Confira na aba Comparação: estes números não aparecem nos cálculos: "
                           + ", ".join(resposta.numeros_nao_conferidos))
            if resposta.aviso:
                st.info(resposta.aviso)
        st.session_state.mensagens.append({
            "role": "assistant", "content": resposta.texto, "rotulo": rotulo,
            "nao_conferidos": resposta.numeros_nao_conferidos, "aviso": resposta.aviso,
        })

    cols_fim = st.columns(2)
    if cols_fim[0].button("Limpar conversa"):
        st.session_state.mensagens = []
        st.rerun()
    with st.expander("Ver a ficha de cálculo que fundamenta as respostas"):
        st.code(montar_ficha(res, sens, recs), language="markdown")

# ----------------------------------------------------------------------------- método
with aba_metodo:
    st.markdown(
        f"""
**Como calculamos** (detalhes e fórmulas em [docs/metodologia.md]({REPO}/blob/main/docs/metodologia.md))

1. **Necessidade**: {pessoas} banho(s) por dia a 40 °C. A vazão do chuveiro sai da potência e da água mais fria do ano
   (P·η = vazão·c·ΔT) → {num(d['vazao_chuveiro_l_min'], 2)} L/min.
2. **L0 · convencional**: energia = potência × tempo (posição inverno o ano todo).
3. **A · uso eficiente**: banho de {minutos_a} min (Sabesp) e potência ajustada ao ΔT de cada dia, sem passar da nominal.
4. **B · solar**: simulação dia a dia de 2016 a 2025. Produção do coletor pelo ensaio INMETRO (PMEe) escalada pela
   irradiação diária no plano inclinado (Open-Meteo ajustado ao Atlas/CRESESB, 34°); perdas de 15% (NBR 15569) e
   perda do reservatório no limite do INMETRO. O chuveiro completa o que o sol não cobre.
5. **Conta**: tarifa ANEEL 2026 da Enel SP + PIS/COFINS + ICMS da faixa de consumo, mês a mês. Retorno = investimento ÷ economia anual.
6. **Ambiente**: CO₂ = kWh × fator médio mensal do SIN (MCTI 2025); água = vazão × tempo.
"""
    )
    st.markdown("**Fontes**")
    for f_ in FONTES_CURTAS:
        st.markdown(f"- {f_}")
    st.markdown(f"Lista completa com links: [docs/referencias.md]({REPO}/blob/main/docs/referencias.md)")
    st.markdown("**Limitações**")
    for x in LIMITACOES:
        st.markdown(f"- {x}")
    st.markdown(
        "**Como o assistente funciona**: o código calcula tudo; a IA generativa (Ollama Cloud) só redige a resposta a "
        "partir da ficha de cálculo e tem os números conferidos. Sem IA disponível, o modo cálculo responde por regras "
        "e é identificado como tal."
    )
    st.caption("Equipe: Matheus Pimenta Martini (RM 569400) · Lucas Seiji (RM 569673) · Leonardo Soares Rodrigues (RM 572986)")
