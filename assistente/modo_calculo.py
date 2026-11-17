"""Modo cálculo: respostas montadas por regras (palavras-chave + modelos de texto).

NÃO é IA generativa. Existe para o assistente continuar útil quando a IA está fora do ar,
sem chave ou sem créditos. Todo número vem do resultado calculado pelo pacote `energia`.
"""
from __future__ import annotations

import re
import unicodedata

from energia.analise import MESES_NOME, Resultado
from energia.formatacao import num, pct, reais

from .contexto import FONTES_CURTAS, LIMITACOES

RODAPE = "\n\n_Modo cálculo: resposta montada por regras a partir dos cálculos (não é IA generativa)._"

INTENCOES = {
    "tarifa_social": ["tarifa social", "baixa renda", "cadunico", "cad unico", "desconto social", "bolsa familia"],
    "solar": ["solar", "placa", "coletor", "aquecedor", "boiler", "vale a pena", "investimento", "investir",
              "retorno", "payback", "se paga", "instalar"],
    "ambiente": ["co2", "carbono", "emiss", "ambient", "sustent", "renovav", "planeta", "agua", "litro"],
    "economia": ["economiz", "dica", "reduzir", "diminuir", "gastar menos", "tempo de banho", "minuto",
                 "posicao", "verao", "habito", "pratica"],
    "comparar": ["compar", "melhor", "escolher", "diferenca", "opcao", "opcoes", "alternativa"],
    "conta": ["conta", "quanto pago", "quanto gasto", "gasto", "valor", "reais", "r$", "tarifa", "kwh",
              "consumo", "icms", "imposto"],
    "mes": ["inverno", "frio", "mes", "julho", "junho", "agosto", "nublad", "chuva"],
    "metodo": ["confiav", "precis", "limita", "premissa", "como calcul", "metodo", "fonte", "referencia",
               "dados", "garantia", "certeza", "de onde", "numeros"],
    "saudacao": ["oi", "ola", "bom dia", "boa tarde", "boa noite", "ajuda", "o que voce faz"],
}
ORDEM = ["tarifa_social", "solar", "ambiente", "economia", "comparar", "conta", "mes", "metodo", "saudacao"]


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto.lower())
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9$ ]+", " ", sem_acento)


def detectar_intencao(pergunta: str) -> str | None:
    t = f" {normalizar(pergunta)} "
    for intencao in ORDEM:
        for chave in INTENCOES[intencao]:
            if chave in ("oi", "ola", "mes") and f" {chave} " not in t:
                continue  # palavras curtas só contam isoladas
            if chave in t:
                return intencao
    return None


def _linha_alt(alt: dict) -> str:
    ret = f", retorno em ~{num(alt['retorno_simples_anos'], 1)} anos" if alt["retorno_simples_anos"] else ""
    inv = f", investimento {reais(alt['investimento_rs'], 0)}" if alt["investimento_rs"] else ", sem investimento"
    return (f"**{alt['nome']}**: {num(alt['chuveiro_kwh_mes_medio'], 1)} kWh/mês no chuveiro, "
            f"economia de {reais(alt['economia_ano_rs'])}/ano{inv}{ret}.")


def responder_por_regras(
    pergunta: str, res: Resultado, sensibilidade: list[dict], recs: list[str], perfis: list[dict] | None = None
) -> str:
    L0, A, B = (res.alternativas[k] for k in ("L0", "A", "B"))
    d = res.derivados
    intencao = detectar_intencao(pergunta)

    if intencao == "saudacao" or intencao is None:
        inicio = "Não entendi bem a pergunta. " if intencao is None else "Olá! "
        texto = (
            f"{inicio}Eu comparo três formas de aquecer a água do banho da sua casa: chuveiro elétrico como hoje, "
            "chuveiro com práticas de uso eficiente e aquecimento solar térmico. Pergunte, por exemplo: "
            "*quanto vou economizar?*, *o solar vale a pena?*, *dicas para gastar menos*, *e a tarifa social?*, "
            "*qual o impacto ambiental?* ou *esses números são confiáveis?*.\n\n"
            f"Resumo da sua simulação: o chuveiro gasta cerca de {num(d['consumo_chuveiro_atual_kwh_mes'], 1)} kWh/mês "
            f"({pct(d['participacao_chuveiro_na_conta'])} do consumo da casa)."
        )
    elif intencao == "solar":
        faixa = [s for s in sensibilidade if s["id"] in ("base", "pessimista")]
        texto = (
            f"{_linha_alt(B)}\n\n"
            f"Com o clima de São Paulo ({d['periodo_clima']}), o sol cobre {pct(B['fracao_solar_ano'], 1)} da energia do banho "
            f"no cenário de referência. Isso é um **limite superior**: com premissas mais pessimistas "
            f"({faixa[-1]['rotulo'].lower()}) a cobertura cai para {pct(faixa[-1]['fracao_solar_ano'], 1)} e o retorno "
            f"para ~{num(faixa[-1]['retorno_simples_anos'] or 0, 1)} anos.\n\n"
            "O valor do kit (SINAPI) não inclui conexões, bomba e válvulas; peça orçamento local antes de decidir."
        )
    elif intencao == "economia":
        texto = (
            f"{_linha_alt(A)}\n\n"
            f"- Banho de {num(res.cenario.praticas.minutos_banho)} minutos (recomendação da Sabesp) em vez de "
            f"{num(res.cenario.familia.minutos_banho)}.\n"
            "- Feche o registro enquanto se ensaboa.\n"
            "- Nos meses quentes, use a posição \"verão\" (menos potência) se ela já deixar a água confortável.\n\n"
            f"Isso reduz cerca de {pct(A['reducao_consumo_chuveiro'])} do consumo do chuveiro e "
            f"{num(L0['agua_m3_ano'] - A['agua_m3_ano'], 1)} m³ de água por ano, sem gastar nada.\n\n"
            f"Para economizar mais, há o aquecimento solar: {_linha_alt(B)}"
        )
    elif intencao == "comparar":
        texto = "\n".join(f"- {_linha_alt(x)}" for x in (L0, A, B)) + "\n\n" + "\n".join(f"- {r}" for r in recs[:2])
    elif intencao == "conta":
        texto = (
            f"Pelo que você informou, a casa consome {num(res.cenario.consumo_conta_kwh)} kWh/mês e o chuveiro responde por "
            f"cerca de {num(d['consumo_chuveiro_atual_kwh_mes'], 1)} kWh/mês ({pct(d['participacao_chuveiro_na_conta'])}). "
            f"A parcela de energia da conta fica em torno de {reais(d['conta_atual_mes_medio_rs'])}/mês "
            f"(tarifa ANEEL 2026 da Enel SP + PIS/COFINS + ICMS de {pct(d['icms_atual'])}); "
            f"desse valor, cerca de {reais(d['custo_chuveiro_mes_medio_rs'])}/mês vêm do chuveiro "
            "(diferença entre a conta com e sem o consumo dele).\n\n"
            f"- Com práticas eficientes (A): {reais(A['conta_energia_mes_medio_rs'])}/mês.\n"
            f"- Com aquecimento solar (B): {reais(B['conta_energia_mes_medio_rs'])}/mês.\n\n"
            "Não incluímos bandeiras tarifárias nem iluminação pública."
        )
    elif intencao == "tarifa_social":
        social = [p for p in (perfis or []) if p["perfil"] == "tarifa_social"]
        if social:
            p = social[0]
            ret = f"~{num(p['retorno_b_anos'], 1)} anos" if p["retorno_b_anos"] is not None else "não se paga"
            extra = (f"Para a sua família com Tarifa Social e o mesmo consumo: conta de energia de {reais(p['conta_atual_mes_rs'])}/mês, "
                     f"economia de {reais(p['economia_a_ano_rs'])}/ano com as práticas (A) e {reais(p['economia_b_ano_rs'])}/ano "
                     f"com o solar (B), que se pagaria em {ret}.")
        elif res.cenario.perfil_tarifario == "tarifa_social":
            extra = (f"Na sua simulação (Tarifa Social), a economia com o solar é de {reais(B['economia_ano_rs'])}/ano "
                     f"e o retorno é de ~{num(B['retorno_simples_anos'] or 0, 1)} anos.")
        else:
            extra = "Para ver o efeito na sua conta, escolha o perfil \"Tarifa Social\" no simulador."
        texto = (
            "Pela Lei 15.235/2025, famílias do CadÚnico com renda de até ½ salário mínimo por pessoa não pagam os "
            "primeiros 80 kWh do mês; quem tem renda entre ½ e 1 salário mínimo por pessoa tem desconto até 120 kWh. "
            "Por isso, nessas famílias a economia em reais é menor que a economia em kWh: parte do consumo já é gratuita "
            f"ou mais barata. {extra}\n\nQuem tem direito deve conferir o cadastro com a distribuidora (Enel SP)."
        )
    elif intencao == "ambiente":
        texto = (
            f"Emissões estimadas do chuveiro (fator do MCTI 2025): {num(L0['co2_kg_ano'], 1)} kg de CO₂/ano hoje, "
            f"{num(A['co2_kg_ano'], 1)} com práticas eficientes e {num(B['co2_kg_ano'], 1)} com solar. São valores baixos porque "
            "a eletricidade brasileira é majoritariamente renovável; em anos secos o fator sobe.\n\n"
            f"Água: hoje {num(L0['agua_m3_ano'], 1)} m³/ano no banho; com práticas eficientes {num(A['agua_m3_ano'], 1)} m³/ano. "
            "Atenção: se, com o solar, a família trocar para uma ducha de maior vazão, o consumo de água pode dobrar "
            f"(cenário de sensibilidade: {num([s for s in sensibilidade if s['id'] == 'vazao_maior'][0]['agua_m3_ano'], 1)} m³/ano)."
        )
    elif intencao == "mes":
        pior = int(res.mensal["e_a_kwh"].idxmax())
        melhor = int(res.mensal["e_a_kwh"].idxmin())
        texto = (
            f"O inverno pesa mais: a água fria chega a ~{num(d['temp_agua_fria_minima_c'], 1)} °C em média no mês mais frio. "
            f"Mesmo com práticas eficientes, o chuveiro gasta {num(res.mensal.loc[pior, 'e_a_kwh'], 1)} kWh em "
            f"{MESES_NOME[pior - 1]} contra {num(res.mensal.loc[melhor, 'e_a_kwh'], 1)} kWh em {MESES_NOME[melhor - 1]}. "
            f"No solar, o mês mais difícil é {MESES_NOME[B['mes_menor_fracao_solar'] - 1]} "
            f"(sol cobre {pct(B['menor_fracao_solar_mensal'], 1)}), e em sequências de dias nublados o chuveiro "
            f"complementa (~{num(B['dias_com_complemento_por_ano'])} dias/ano no cenário de referência)."
        )
    else:  # metodo
        texto = (
            "Os números são **estimativas**, calculadas dia a dia para 2016-2025 com dados públicos:\n"
            + "\n".join(f"- {f}" for f in FONTES_CURTAS)
            + "\n\nPrincipais limitações:\n" + "\n".join(f"- {x}" for x in LIMITACOES[:5])
        )
    if res.avisos:
        texto += "\n\n⚠️ " + " ".join(res.avisos)
    return texto + RODAPE
