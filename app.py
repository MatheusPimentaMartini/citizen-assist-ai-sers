"""Citizen Assist AI - Energia no banho (Global Solution 2026.2 - SERS / FIAP).

Rodar localmente:  streamlit run app.py
Online:            Streamlit Community Cloud (chave do Ollama Cloud em Settings > Secrets).

A interface foi pensada primeiro para o celular e segue um caminho em etapas:
  Simular    -> apresentação, perguntas sobre a casa (formulário) e o resultado logo abaixo
  Assistente -> perguntas sugeridas e chat (IA generativa via Ollama Cloud ou modo cálculo)
  Fontes     -> de onde vêm os números, como calculamos e as limitações
Os cálculos ficam no pacote `energia` e o assistente no pacote `assistente`; este arquivo só cuida da tela.
"""
from __future__ import annotations

import threading
import time
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from assistente import ConfigIA, responder, versao_instrucoes
from assistente.contexto import FONTES_CURTAS, FONTES_RESUMO, LIMITACOES, montar_ficha
from assistente.modo_calculo import normalizar
from energia import (
    BaseDados, Cenario, Familia, PraticasEficientes, Premissas, SistemaSolar, analisar, recomendacoes,
)
from energia.analise import MESES_NOME, comparar_perfis, sensibilidade_solar
from energia.formatacao import num, pct, pct_sem_100, reais
from energia.tarifa import PERFIS

LIMITE_IA_POR_SESSAO = 15
LIMITE_IA_POR_HORA = 120  # todas as sessões somadas (protege os créditos da conta)
REPO = "https://github.com/MatheusPimentaMartini/citizen-assist-ai-sers"
PASTA = Path(__file__).resolve().parent

# Valores iniciais do formulário = cenário de referência do estudo (docs/metodologia.md).
PADRAO = {
    "pessoas": 4, "minutos": 8, "potencia": 5500, "consumo": 200, "perfil": "convencional",
    "minutos_a": 5, "ajuste": True, "investimento": 3359.57,
}
SECOES = {
    "simular": ":material/calculate: Simular",
    "assistente": ":material/forum: Assistente",
    "fontes": ":material/menu_book: Fontes",
}
PERFIL_OPCAO = {
    "convencional": "Não, conta normal",
    "tarifa_social": "Sim, Tarifa Social",
    "desconto_social": "Sim, Desconto Social",
}
PERFIL_EXPLICACAO = [
    "Se não souber, escolha esta opção.",
    "CadÚnico com renda de até ½ salário mínimo por pessoa: até 80 kWh por mês grátis.",
    "Renda entre ½ e 1 salário mínimo por pessoa: até 120 kWh por mês com tarifa menor.",
]
PERFIL_CURTO = {"convencional": "conta normal", "tarifa_social": "Tarifa Social", "desconto_social": "Desconto Social"}
SUGESTOES = [
    "O aquecedor solar vale a pena para mim?",
    "Como economizar sem gastar nada?",
    "Quanto o chuveiro pesa na minha conta?",
    "E se eu tiver Tarifa Social?",
    "Qual o impacto no meio ambiente?",
    "De onde vêm esses números?",
]
# Cores fixas por alternativa (iguais no gráfico e nos cartões); o texto sempre diz qual é qual.
COR = {"L0": "#7B8794", "A": "#17703F", "B": "#C27C0E"}
NOME_CURTO = {"L0": "Hoje", "A": "A · Mudar hábitos", "B": "B · Aquecedor solar"}

st.set_page_config(page_title="Citizen Assist AI · Energia no banho", page_icon="🚿", layout="centered")
st.html(PASTA / "estilo.css")


# ----------------------------------------------------------------------------- cálculo e IA (sem mudanças)
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
    return res, sens, recomendacoes(res, sens), comparar_perfis(cenario, base)


def configuracao_ia() -> ConfigIA:
    try:
        segredos = st.secrets
    except Exception:
        segredos = None
    return ConfigIA.carregar(segredos)


def pode_chamar_ia() -> tuple[bool, str]:
    if st.session_state.get("chamadas_ia", 0) >= LIMITE_IA_POR_SESSAO:
        return False, (f"Você chegou ao limite de {LIMITE_IA_POR_SESSAO} perguntas à IA nesta visita "
                       "(isso protege os créditos do projeto).")
    g = estado_global()
    with g["lock"]:
        agora = time.time()
        g["chamadas"] = [t for t in g["chamadas"] if agora - t < 3600]
        if len(g["chamadas"]) >= LIMITE_IA_POR_HORA:
            return False, "Muitas perguntas à IA na última hora em todo o app; tente de novo mais tarde."
    return True, ""


# ----------------------------------------------------------------------------- estado da sessão e ações
ss = st.session_state
ss.setdefault("casa", dict(PADRAO))  # dados usados no cálculo (só mudam ao tocar em "Calcular")
ss.setdefault("calculado", False)
ss.setdefault("mensagens", [])
ss.setdefault("secao", "simular")


def ir_para(secao: str) -> None:
    ss.secao = secao


def ao_calcular() -> None:
    """Guarda as respostas do formulário. O ajuste abaixo evita um banho 'eficiente' mais longo que o de hoje."""
    casa = {k: ss[f"f_{k}"] for k in PADRAO}
    ss.minutos_a_ajustado = casa["minutos_a"] > casa["minutos"]
    casa["minutos_a"] = min(casa["minutos_a"], casa["minutos"])
    ss.casa = casa
    ss.calculado = True
    ss.acao = "calculou"


def escolher_sugestao() -> None:
    if ss.get("sugestao"):
        ss.pergunta_pendente = ss.sugestao
    ss.sugestao = None  # libera o botão para ser tocado de novo


def limpar_conversa() -> None:
    ss.mensagens = []


def rolar(alvo: str | None = None) -> None:
    """Rola a tela até a âncora `alvo` (ou até o topo). Sem isso, no celular a pessoa ficaria no meio da página."""
    ss.rolagens = ss.get("rolagens", 0) + 1
    destino = f"document.getElementById('{alvo}')" if alvo else "null"
    st.html(
        f"""<script>
        /* rolagem {ss.rolagens} */
        (() => {{
        const rolar = () => {{
          const alvo = {destino};
          if (alvo) {{ alvo.scrollIntoView({{block: "start"}}); return; }}
          document.querySelectorAll('.stMain, [data-testid="stMain"], [data-testid="stAppScrollToBottomContainer"]')
            .forEach((el) => el.scrollTo({{top: 0}}));
          window.scrollTo({{top: 0}});
        }};
        /* duas tentativas: a página ainda pode estar terminando de desenhar */
        setTimeout(rolar, 250);
        setTimeout(rolar, 900);
        }})();
        </script>""",
        unsafe_allow_javascript=True,
    )


def rs(valor: float) -> str:
    """Valor em reais sem quebrar a linha entre "R$" e o número (espaço não separável)."""
    return reais(valor).replace(" ", "\u00a0")


def resumo_casa(casa: dict) -> str:
    pessoas = f"{casa['pessoas']} pessoa" + ("s" if casa["pessoas"] > 1 else "")
    return (f"{pessoas} · banho de {casa['minutos']} min · chuveiro de {num(casa['potencia'])} W · "
            f"{num(casa['consumo'])} kWh/mês · {PERFIL_CURTO[casa['perfil']]}")


def rodape() -> None:
    st.divider()
    st.caption("Citizen Assist AI · projeto acadêmico FIAP, Global Solution 2026.2 (SERS). "
               "Os valores são estimativas, não garantias.")


# ----------------------------------------------------------------------------- gráficos
def grafico_contas(alts: dict) -> alt.Chart:
    dados = pd.DataFrame({
        "opcao": [NOME_CURTO[k] for k in alts],
        "valor": [v["conta_energia_mes_medio_rs"] for v in alts.values()],
    })
    dados["rotulo"] = [f"{rs(v)}/mês" for v in dados["valor"]]
    topo = max(float(dados["valor"].max()) * 2.0, 1.0)  # espaço para o valor escrito ao lado da barra
    base = alt.Chart(dados).encode(
        y=alt.Y("opcao:N", sort=None, title=None,
                axis=alt.Axis(labelFontSize=14, labelLimit=170, labelColor="#1F2933", ticks=False, domain=False)),
        x=alt.X("valor:Q", title=None, axis=None, scale=alt.Scale(domain=[0, topo])),
    )
    barras = base.mark_bar(cornerRadiusEnd=6, size=26).encode(
        color=alt.Color("opcao:N", legend=None,
                        scale=alt.Scale(domain=list(dados["opcao"]), range=[COR[k] for k in alts])),
        tooltip=[alt.Tooltip("opcao:N", title="Opção"), alt.Tooltip("rotulo:N", title="Conta de energia")],
    )
    textos = base.mark_text(align="left", dx=6, fontSize=14, fontWeight=600).encode(text="rotulo:N")
    return (barras + textos).properties(height=130).configure_view(stroke=None)


# ----------------------------------------------------------------------------- seção 1: simular
def formulario(casa: dict) -> None:
    st.subheader("1. Conte sobre a sua casa", anchor="casa")
    with st.form("form_casa"):
        st.number_input("Quantas pessoas tomam banho na sua casa por dia?", 1, 10, casa["pessoas"], 1, key="f_pessoas")
        st.caption("O cálculo considera um banho por pessoa por dia. Se alguém toma dois banhos, conte essa pessoa duas vezes.")

        st.slider("Quanto tempo dura cada banho, em média?", 2, 20, casa["minutos"], key="f_minutos", format="%d min")
        st.caption("Exemplo: 8 minutos. Se não souber, cronometre um banho.")

        st.number_input("Qual é a potência do chuveiro, em watts (W)?", 2000, 9000, casa["potencia"], 100, key="f_potencia")
        st.caption("Use a potência maior (posição inverno). Ela aparece na etiqueta, na caixa ou no manual, "
                   "por exemplo 5.500 W ou 7.500 W. Se não souber, deixe 5.500 W, o valor de referência do estudo.")

        st.number_input("Quanto de energia a casa gasta por mês, em kWh?", 30, 1000, casa["consumo"], 10, key="f_consumo")
        st.caption("Está na conta de luz, no campo de consumo em kWh. Se puder, use a média dos últimos meses.")

        st.radio(
            "A sua conta de luz tem desconto social?", list(PERFIS), index=list(PERFIS).index(casa["perfil"]),
            format_func=PERFIL_OPCAO.get, captions=PERFIL_EXPLICACAO, key="f_perfil",
        )

        with st.expander("Ajustar as alternativas (opcional)", icon=":material/tune:"):
            st.slider("Alternativa A: quanto tempo duraria cada banho?", 2, 20, casa["minutos_a"],
                      key="f_minutos_a", format="%d min")
            st.caption("A Sabesp recomenda banhos de até 5 minutos. Não pode passar do tempo de banho de hoje.")
            st.checkbox("Alternativa A: usar a posição verão nos dias em que a água já chega morna",
                        casa["ajuste"], key="f_ajuste")
            st.number_input("Alternativa B: quanto custa o aquecedor solar instalado (R$)?", 0.0, 30000.0,
                            float(casa["investimento"]), 100.0, key="f_investimento")
            st.caption("Referência: R$ 3.359,57 (SINAPI 103517, kit de 2 m² + 200 litros instalado, set/2026). "
                       "Se você tiver um orçamento, use o seu valor.")

        st.form_submit_button("Calcular minha economia", type="primary", icon=":material/calculate:",
                              width="stretch", on_click=ao_calcular, key="calcular")


def cartao_hoje(L0: dict, minutos: int) -> None:
    with st.container(border=True, key="card_L0", height="stretch"):
        st.markdown("##### :material/shower: Como é hoje")
        st.caption(f"Chuveiro elétrico na posição inverno o ano todo, com banhos de {minutos} min.")
        st.metric("Conta de energia por mês", rs(L0["conta_energia_mes_medio_rs"]))
        st.markdown(
            f"- Chuveiro: **{num(L0['chuveiro_kwh_mes_medio'], 1)} kWh/mês**\n"
            f"- Água do banho: **{num(L0['agua_m3_ano'], 1)} mil litros/ano**\n"
            f"- CO₂: **{num(L0['co2_kg_ano'], 1)} kg/ano**"
        )


def cartao_alternativa(chave: str, alt_: dict, L0: dict, selos: list[str], descricao: str, nota: str | None) -> None:
    titulo = {"A": ":material/timer: A · Mudar hábitos no banho",
              "B": ":material/solar_power: B · Aquecedor solar"}[chave]
    with st.container(border=True, key=f"card_{chave}", height="stretch"):
        st.markdown(f"##### {titulo}")
        if selos:
            st.markdown(" ".join(selos))
        st.caption(descricao)
        if alt_["economia_ano_rs"] > 0:
            st.metric("Você economiza por mês", rs(alt_["economia_mes_medio_rs"]))
            st.caption(f"{rs(alt_['economia_ano_rs'])} por ano")
        else:
            st.metric("Você economiza por mês", "R$ 0,00")
            st.caption("Com estes dados não há economia na conta.")
        if alt_["investimento_rs"] > 0:
            custo = f"**{rs(alt_['investimento_rs'])}**"
            retorno = (f"cerca de **{num(alt_['retorno_simples_anos'], 1)} anos**" if alt_["retorno_simples_anos"]
                       else "**não se paga** com estes dados")
            linhas = [f"Custo para começar: {custo}", f"Se paga em: {retorno}"]
        else:
            linhas = ["Custo para começar: **R$ 0**"]
        menos_agua = L0["agua_m3_ano"] - alt_["agua_m3_ano"]
        agua = (f"**{num(alt_['agua_m3_ano'], 1)} mil litros/ano** ({num(menos_agua, 1)} mil a menos)" if menos_agua > 0.05
                else f"**{num(alt_['agua_m3_ano'], 1)} mil litros/ano** (igual a hoje)")
        linhas += [
            f"Conta de energia: **{rs(alt_['conta_energia_mes_medio_rs'])}/mês**",
            f"Chuveiro: **{num(alt_['chuveiro_kwh_mes_medio'], 1)} kWh/mês** "
            f"({pct_sem_100(alt_['reducao_consumo_chuveiro'])} a menos)",
            f"Água do banho: {agua}",
            f"CO₂: **{num(alt_['co2_kg_ano'], 1)} kg/ano**",
        ]
        st.markdown("\n".join(f"- {x}" for x in linhas))
        if nota:
            st.caption(nota)


def resultado(res, sens, recs, casa: dict, recem_calculado: bool) -> None:
    L0, A, B = (res.alternativas[k] for k in ("L0", "A", "B"))
    d = res.derivados
    st.subheader("2. O resultado da sua casa", anchor="resultado")
    if recem_calculado:  # retorno visual da ação, sem cobrir a tela (um aviso flutuante taparia o título no celular)
        st.success(f"**Pronto!** Resultado calculado para: {resumo_casa(casa)}.", icon=":material/check_circle:")
    else:
        st.caption(f"Calculado para: {resumo_casa(casa)}")
    if ss.get("minutos_a_ajustado"):
        st.info(f"Na alternativa A, o banho não pode ser mais longo que o de hoje; usamos {casa['minutos_a']} min.",
                icon=":material/info:")
    for aviso in res.avisos:
        st.warning(f"**Confira os dados.** {aviso}", icon=":material/warning:")

    with st.container(border=True, key="destaque"):
        st.markdown(
            f"Hoje o chuveiro gasta cerca de **{num(d['consumo_chuveiro_atual_kwh_mes'], 1)} kWh por mês**, "
            f"{pct(d['participacao_chuveiro_na_conta'])} de toda a energia da casa. "
            f"Na conta de luz, isso dá cerca de **{rs(d['custo_chuveiro_mes_medio_rs'])} por mês**."
        )
        st.caption("Custo do chuveiro = conta de energia estimada com o chuveiro menos a conta só dos outros aparelhos.")

    st.markdown("#### Quanto ficaria a conta de energia por mês")
    st.altair_chart(grafico_contas(res.alternativas), width="stretch")
    st.caption("Estimativa com a tarifa da Enel SP 2026, ICMS e PIS/COFINS. Não inclui bandeira tarifária nem "
               "iluminação pública, por isso pode ficar abaixo do total da sua conta.")

    st.markdown("#### Compare as opções")
    economias = {k: res.alternativas[k]["economia_ano_rs"] for k in ("A", "B")}
    maior = max(economias, key=economias.get)
    selos = {}
    for k in ("A", "B"):
        alt_ = res.alternativas[k]
        s = []
        if alt_["investimento_rs"] == 0 and alt_["economia_ano_rs"] > 0:
            s.append(":green-badge[:material/check_circle: Sem custo inicial]")
        if k == maior and economias[k] > 0:
            s.append(":orange-badge[:material/star: Maior economia]")
        selos[k] = s
    pratica = (f"Banhos de {casa['minutos_a']} min" +
               (" e posição verão nos dias em que a água já chega morna." if casa["ajuste"] else "."))
    pess = next((s for s in sens if s["id"] == "pessimista"), None)
    nota_b = None
    if pess:
        ret = f"se paga em cerca de {num(pess['retorno_simples_anos'], 1)} anos" if pess["retorno_simples_anos"] \
            else "não se paga"
        nota_b = (f"Se o sistema render menos (cenário pessimista), a economia cai para "
                  f"{rs(pess['economia_ano_rs'])} por ano e ele {ret}. O preço real depende de orçamento local.")

    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        cartao_hoje(L0, casa["minutos"])
    with c2:
        cartao_alternativa("A", A, L0, selos["A"], pratica, None)
    with c3:
        cartao_alternativa(
            "B", B, L0, selos["B"],
            "Coletor solar de 2 m² e reservatório de 200 litros aquecem a água; o chuveiro só completa nos dias nublados.",
            nota_b,
        )

    st.markdown("#### O que fazer agora")
    st.markdown("\n".join(f"{i}. {r}" for i, r in enumerate(recs, 1)))

    with st.expander("Ver o consumo do chuveiro mês a mês", icon=":material/bar_chart:"):
        mensal = pd.DataFrame({
            "Mês": [MESES_NOME[i - 1][:3] for i in res.mensal.index],
            NOME_CURTO["L0"]: res.mensal["e_l0_kwh"].values,
            NOME_CURTO["A"]: res.mensal["e_a_kwh"].values,
            NOME_CURTO["B"]: res.mensal["e_b_kwh"].values,
        })
        st.caption("Ano típico (clima de 2016 a 2025). Barras menores = menos energia gasta pelo chuveiro.")
        st.bar_chart(mensal, x="Mês", y=list(NOME_CURTO.values()), color=list(COR.values()), stack=False,
                     sort=False, x_label="", y_label="kWh por mês", height=320)
        st.caption(
            f"Com o aquecedor solar, o sol cobre {pct(B['fracao_solar_ano'], 1)} da energia do banho no ano "
            f"(cenário de referência); o chuveiro completa em cerca de {num(B['dias_com_complemento_por_ano'])} "
            f"dias por ano, nas sequências de dias nublados. O mês mais difícil é "
            f"{MESES_NOME[B['mes_menor_fracao_solar'] - 1]}."
        )

    with st.expander("E se o aquecedor solar render menos?", icon=":material/help:"):
        st.caption("Recalculamos a alternativa B com premissas mais pessimistas, todas com fonte.")
        for s in sens:
            ret = f"cerca de {num(s['retorno_simples_anos'], 1)} anos" if s["retorno_simples_anos"] else "não se paga"
            st.markdown(
                f"**{s['rotulo']}**\n\n"
                f"Sol cobre {pct(s['fracao_solar_ano'], 1)} · economia de {rs(s['economia_ano_rs'])}/ano · "
                f"se paga em {ret} · água {num(s['agua_m3_ano'], 1)} mil litros/ano"
            )
            st.caption(f"Fonte: {s['fonte']}")

    with st.expander("Ver todos os números em tabela", icon=":material/table:"):
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

    st.markdown("#### Próximos passos")
    b1, b2 = st.columns(2)
    b1.button("Tirar dúvidas com o assistente", type="primary", icon=":material/forum:", width="stretch",
              on_click=ir_para, args=("assistente",), key="ir_assistente")
    b2.button("Ver de onde vêm os números", icon=":material/menu_book:", width="stretch",
              on_click=ir_para, args=("fontes",), key="ir_fontes")


def secao_simular(res, sens, recs, recem_calculado: bool) -> None:
    with st.container(border=True, key="hero"):
        st.markdown("### Quanto o banho pesa na sua conta de luz?")
        st.markdown(
            "Responda **5 perguntas rápidas** e veja, para a sua casa:\n"
            "- quanto o chuveiro elétrico gasta hoje;\n"
            "- quanto você economiza **mudando hábitos**, sem gastar nada;\n"
            "- quanto economiza com **aquecedor solar** e em quanto tempo ele se paga."
        )
        st.caption("Para famílias que moram em casa na Grande São Paulo e usam chuveiro elétrico.")
    formulario(ss.casa)
    if not ss.calculado:
        st.info("Responda as perguntas e toque em **Calcular minha economia** para ver o resultado da sua casa.",
                icon=":material/arrow_upward:")
        return
    resultado(res, sens, recs, ss.casa, recem_calculado)


# ----------------------------------------------------------------------------- seção 2: assistente
def rotulo_resposta(modo: str, config: ConfigIA) -> str | None:
    if modo == "ia":
        return f"🤖 Resposta da IA generativa ({config.descricao}), escrita a partir da ficha de cálculo."
    return None  # o texto do modo cálculo já termina com "Modo cálculo: ... (não é IA generativa)"


def mostrar_resposta(m: dict) -> None:
    st.markdown(m["content"])
    if m["role"] != "assistant":
        return
    if m.get("rotulo"):
        st.caption(m["rotulo"])
    st.caption(FONTES_RESUMO)
    if m.get("nao_conferidos"):
        st.warning("**Atenção:** a resposta citou números que não aparecem nos cálculos ("
                   + ", ".join(m["nao_conferidos"]) + "). Confira os valores na seção Simular.",
                   icon=":material/warning:")
    if m.get("aviso"):
        st.info(m["aviso"], icon=":material/info:")


def processar(pergunta: str, res, sens, recs, perfis, config: ConfigIA, usar_ia: bool) -> None:
    ss.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)
    ficha_atual = montar_ficha(res, sens, recs, perfis)
    chave = (normalizar(pergunta).strip(), versao_instrucoes(ficha_atual), config.modelo)
    g = estado_global()
    resposta = g["respostas"].get(chave) if usar_ia else None
    ia_liberada, motivo = pode_chamar_ia() if (usar_ia and resposta is None) else (usar_ia, "")
    with st.chat_message("assistant"):
        if resposta is None:
            with st.spinner("Preparando a resposta..."):
                resposta = responder(pergunta, res, sens, recs, config, usar_ia=usar_ia and ia_liberada, perfis=perfis)
            if usar_ia and not ia_liberada:
                resposta.aviso = motivo + " Esta resposta foi montada pelo modo cálculo (sem IA)."
            if resposta.modo == "ia":
                ss.chamadas_ia = ss.get("chamadas_ia", 0) + 1
                with g["lock"]:
                    g["chamadas"].append(time.time())
                    if len(g["respostas"]) > 500:
                        g["respostas"].clear()
                    g["respostas"][chave] = resposta
        msg = {
            "role": "assistant", "content": resposta.texto, "rotulo": rotulo_resposta(resposta.modo, config),
            "nao_conferidos": resposta.numeros_nao_conferidos, "aviso": resposta.aviso,
        }
        mostrar_resposta(msg)
    ss.mensagens.append(msg)


def secao_assistente(res, sens, recs, perfis) -> None:
    """Ordem pensada para o celular: o Streamlit mantém a conversa rolada até o fim (perto do campo de texto),
    então o que a pessoa mais precisa ver (situação da IA, boas-vindas e perguntas sugeridas) fica embaixo."""
    config = configuracao_ia()
    usar_ia = config.disponivel and ss.get("usar_ia", True)
    digitada = st.chat_input("Escreva sua pergunta", key="chat", max_chars=500)

    st.subheader("Tire suas dúvidas", anchor="assistente")
    st.markdown("Pergunte sobre o banho da sua casa: economia, aquecedor solar, Tarifa Social ou meio ambiente.")
    with st.expander("Como o assistente funciona e quais números ele usa", icon=":material/info:"):
        st.markdown(
            "- O código calcula todos os números. O assistente recebe a **ficha de cálculo** da sua simulação.\n"
            "- Com a IA generativa ativa, o Ollama Cloud escreve a resposta usando só os números da ficha, e o app "
            "confere os números de cada resposta. Se aparecer um número que não está nos cálculos, você vê um aviso.\n"
            "- No **modo cálculo**, a resposta é montada por regras (palavras-chave + modelos de texto). "
            "Não é IA generativa e aparece identificada.\n"
            "- Com a IA ativa, a pergunta e a ficha vão para o Ollama Cloud; o app não guarda conversas."
        )
        st.toggle("Usar IA generativa", value=usar_ia, disabled=not config.disponivel, key="t_usar_ia",
                  on_change=lambda: ss.update(usar_ia=ss.t_usar_ia))
        if config.disponivel:
            st.caption(f"Perguntas à IA nesta visita: {ss.get('chamadas_ia', 0)} de {LIMITE_IA_POR_SESSAO}.")
        st.markdown("**Ficha de cálculo desta simulação** (os únicos números que o assistente pode usar):")
        st.code(montar_ficha(res, sens, recs, perfis), language="markdown")

    if not ss.calculado:
        st.info("Você ainda não calculou a sua casa. Por enquanto, as respostas usam a família de exemplo: "
                f"{resumo_casa(ss.casa)}.", icon=":material/home:")
        st.button("Informar os dados da minha casa", icon=":material/edit:", on_click=ir_para, args=("simular",),
                  key="ir_simular")
    if usar_ia:
        st.success(f"**IA generativa ativa** ({config.descricao}): usa só os números da sua simulação, "
                   "conferidos pelo app.", icon=":material/smart_toy:")
    elif config.disponivel:
        st.info("**Modo cálculo** (não é IA generativa): as respostas são montadas por regras a partir dos "
                "cálculos.", icon=":material/calculate:")
    else:
        st.info("**Modo cálculo** (não é IA generativa): a IA não está configurada neste servidor; as respostas "
                "são montadas por regras a partir dos cálculos.", icon=":material/calculate:")

    with st.chat_message("assistant"):
        st.markdown("Olá! Eu explico o resultado da simulação da sua casa. Toque em uma das perguntas sugeridas "
                    "ou escreva a sua no campo **Escreva sua pergunta**, no fim da tela.\n\n"
                    "Não escreva dados pessoais, como nome, endereço ou telefone.")
        st.caption("Mensagem fixa de boas-vindas (não é gerada por IA).")
    for m in ss.mensagens:
        with st.chat_message(m["role"]):
            mostrar_resposta(m)

    pergunta = digitada or ss.pop("pergunta_pendente", None)
    if pergunta:
        processar(pergunta, res, sens, recs, perfis, config, usar_ia)

    if not ss.mensagens:
        st.pills("Perguntas sugeridas", SUGESTOES, key="sugestao", on_change=escolher_sugestao)
    else:
        with st.expander("Ver perguntas sugeridas", icon=":material/lightbulb:"):
            st.pills("Perguntas sugeridas", SUGESTOES, key="sugestao", on_change=escolher_sugestao,
                     label_visibility="collapsed")
    if ss.mensagens:
        st.button("Limpar conversa", icon=":material/delete:", type="tertiary", on_click=limpar_conversa,
                  key="limpar")


# ----------------------------------------------------------------------------- seção 3: fontes
def secao_fontes(res, casa: dict) -> None:
    d = res.derivados
    st.subheader("De onde vêm os números", anchor="fontes")
    st.markdown(
        "Todos os números do app são **calculados pelo código** a partir de dados públicos. A IA generativa não "
        "cria valores: ela só explica os resultados, e o app confere os números de cada resposta."
    )
    st.markdown("#### Fontes")
    st.markdown("\n".join(f"- {f_}" for f_ in FONTES_CURTAS))
    st.markdown(f":material/open_in_new: [Ver a lista completa de referências, com links]({REPO}/blob/main/docs/referencias.md)")

    st.markdown("#### Como calculamos, em 5 passos")
    st.markdown(
        "1. **Água quente que a casa precisa**: pessoas × minutos de banho, com a água a 40 °C.\n"
        "2. **Hoje**: energia do chuveiro = potência × tempo de banho.\n"
        "3. **A · Mudar hábitos**: banho mais curto e menos potência nos dias em que a água já chega morna.\n"
        "4. **B · Aquecedor solar**: simulação dia a dia de 2016 a 2025 com o sol de São Paulo; "
        "o chuveiro completa o que o sol não cobre.\n"
        "5. **Conta, CO₂ e água**: tarifa da Enel SP 2026 com impostos; CO₂ pelo fator do MCTI; água pela vazão do chuveiro."
    )
    with st.expander("Ver as fórmulas e premissas", icon=":material/function:"):
        st.markdown(
            f"""
1. **Necessidade**: {casa['pessoas']} banho(s) por dia a 40 °C. A vazão do chuveiro sai da potência e da água mais fria
   do ano (P·η = vazão·c·ΔT) → {num(d['vazao_chuveiro_l_min'], 2)} L/min.
2. **Hoje (L0, convencional)**: energia = potência × tempo (posição inverno o ano todo).
3. **A · uso eficiente**: banho de {casa['minutos_a']} min (Sabesp) e potência ajustada ao ΔT de cada dia, sem passar da nominal.
4. **B · solar**: simulação dia a dia de 2016 a 2025. Produção do coletor pelo ensaio INMETRO (PMEe) escalada pela
   irradiação diária no plano inclinado (Open-Meteo ajustado ao Atlas/CRESESB, 34°); perdas de 15% (NBR 15569) e
   perda do reservatório no limite do INMETRO. O chuveiro completa o que o sol não cobre.
5. **Conta**: tarifa ANEEL 2026 da Enel SP + PIS/COFINS + ICMS da faixa de consumo, mês a mês. Retorno = investimento ÷ economia anual.
   Custo do chuveiro na conta = conta com o chuveiro − conta só dos outros aparelhos.
6. **Ambiente**: CO₂ = kWh × fator médio mensal do SIN (MCTI 2025); água = vazão × tempo.

Detalhes: [docs/metodologia.md]({REPO}/blob/main/docs/metodologia.md)
"""
        )
    st.markdown("#### Limitações")
    st.markdown("\n".join(f"- {x}" for x in LIMITACOES))
    st.markdown("#### Como o assistente funciona")
    st.markdown(
        "O código calcula tudo; a IA generativa (Ollama Cloud) só redige a resposta a partir da ficha de cálculo e "
        "tem os números conferidos. Sem IA disponível, o modo cálculo responde por regras e é identificado como tal."
    )
    st.markdown("#### Equipe")
    st.markdown("Matheus Pimenta Martini (RM 569400) · Lucas Seiji (RM 569673) · Leonardo Soares Rodrigues (RM 572986)")
    st.markdown(f":material/code: [Código, dados e testes no GitHub]({REPO})")


# ----------------------------------------------------------------------------- página
st.caption("CITIZEN ASSIST AI · GLOBAL SOLUTION FIAP 2026.2")
st.title("🚿 Energia no banho")
st.segmented_control("Ir para a seção", list(SECOES), format_func=SECOES.get, key="secao", required=True,
                     label_visibility="collapsed", width="stretch")

mudou_secao = ss.get("secao_anterior") not in (None, ss.secao)
ss.secao_anterior = ss.secao
try:
    res, sens, recs, perfis = calcular(**ss.casa)
except ValueError as erro:  # não deve acontecer (os campos têm limites), mas a tela nunca fica travada
    st.error(f"Não foi possível calcular com estes dados: {erro} Voltamos aos valores de exemplo; "
             "confira as respostas e calcule de novo.", icon=":material/error:")
    ss.casa, ss.calculado = dict(PADRAO), False
    res, sens, recs, perfis = calcular(**ss.casa)

recem_calculado = ss.pop("acao", None) == "calculou" and ss.secao == "simular"
if ss.secao == "assistente":
    secao_assistente(res, sens, recs, perfis)
else:
    if ss.secao == "fontes":
        secao_fontes(res, ss.casa)
    else:
        secao_simular(res, sens, recs, recem_calculado)
    rodape()

if recem_calculado:
    rolar("resultado")
elif mudou_secao and ss.secao != "assistente":
    rolar()
