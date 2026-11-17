"""Citizen Assist AI - assistente de orientação energética para o banho.

Fluxo de uma pergunta:
1. Os cálculos (pacote `energia`) viram uma FICHA DE CÁLCULO em texto.
2. Se a IA generativa estiver configurada (Ollama Cloud), ela responde usando só a ficha.
   Os números da resposta são conferidos contra a ficha (verificador).
3. Se a IA falhar (sem chave, limite, rede, modelo fora do ar), o assistente responde em
   MODO CÁLCULO: regras + modelos de texto, sempre identificado como "não é IA generativa".
"""
from __future__ import annotations

from dataclasses import dataclass, field

from energia.analise import Resultado

from .contexto import montar_ficha
from .modo_calculo import responder_por_regras
from .ollama_cloud import ConfigIA, ErroIA, conversar
from .verificador import numeros_nao_conferidos

INSTRUCOES = """Você é o Citizen Assist AI, assistente de orientação energética para famílias que moram em casas na Região Metropolitana de São Paulo e usam chuveiro elétrico. O tema é o aquecimento da água do banho: chuveiro elétrico convencional (L0), chuveiro com práticas de uso eficiente (A) e aquecimento solar térmico (B).

Regras obrigatórias:
1. Use SOMENTE os números da FICHA DE CÁLCULO abaixo. Não faça contas novas e não invente valores. Se o número pedido não estiver na ficha, diga que ele não foi calculado e peça para ajustar os dados no simulador (aba "Comparação").
2. Deixe claro que são estimativas, não garantias. Ao citar um número, diga de onde ele vem (por exemplo: "tarifa ANEEL 2026", "clima 2016-2025", "SINAPI").
3. Ao recomendar, considere custo, investimento, retorno, impacto ambiental (CO2 e água) e as limitações listadas na ficha.
4. Responda em português do Brasil, com linguagem simples, em no máximo 170 palavras. Listas curtas ajudam.
5. Se a pergunta não for sobre energia ou água no banho, ou sobre esta análise, diga educadamente que você só ajuda com esse tema.
6. Não peça dados pessoais (CPF, endereço, número de cliente).
7. Se o usuário informar dados diferentes dos da ficha (outro chuveiro, outra conta), não recalcule: peça para alterar no simulador.

FICHA DE CÁLCULO (gerada pelo código a partir dos dados públicos do repositório):
"""


@dataclass
class Resposta:
    texto: str
    modo: str  # "ia" ou "calculo"
    numeros_nao_conferidos: list = field(default_factory=list)
    aviso: str | None = None


def montar_mensagens(ficha: str, pergunta: str, historico: list[dict] | None = None) -> list[dict]:
    mensagens = [{"role": "system", "content": INSTRUCOES + ficha}]
    for m in (historico or [])[-6:]:  # contexto curto: últimas 3 trocas
        if m.get("role") in ("user", "assistant") and m.get("content"):
            mensagens.append({"role": m["role"], "content": m["content"]})
    mensagens.append({"role": "user", "content": pergunta})
    return mensagens


def responder(
    pergunta: str,
    res: Resultado,
    sensibilidade: list[dict],
    recs: list[str],
    config: ConfigIA,
    historico: list[dict] | None = None,
    usar_ia: bool = True,
) -> Resposta:
    pergunta = (pergunta or "").strip()[:800]
    if not pergunta:
        return Resposta("Escreva uma pergunta sobre o consumo do banho.", "calculo")
    ficha = montar_ficha(res, sensibilidade, recs)
    aviso = None
    if usar_ia and config.disponivel:
        try:
            texto = conversar(config, montar_mensagens(ficha, pergunta, historico))
            return Resposta(texto, "ia", numeros_nao_conferidos(texto, ficha))
        except ErroIA as e:
            aviso = f"IA generativa indisponível agora ({e}) Resposta gerada no modo cálculo."
    elif usar_ia:
        aviso = "IA generativa não configurada neste servidor. Resposta gerada no modo cálculo."
    return Resposta(responder_por_regras(pergunta, res, sensibilidade, recs), "calculo", aviso=aviso)


__all__ = ["ConfigIA", "Resposta", "montar_mensagens", "responder"]
