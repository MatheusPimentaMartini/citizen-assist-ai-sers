"""Confere se os números de uma resposta da IA existem na ficha de cálculo.

Serve como trava contra números inventados: qualquer valor que não esteja na ficha
(com tolerância de arredondamento) é sinalizado ao usuário.
"""
from __future__ import annotations

import re

_NUMERO = re.compile(r"(?<![\w.,])(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+,\d+|\d+\.\d{1,2}(?!\d)|\d+)(\s*%)?")


def _para_float(bruto: str) -> float:
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?", bruto):  # 1.234,56 (pt-BR)
        return float(bruto.replace(".", "").replace(",", "."))
    if "," in bruto:  # 12,5
        return float(bruto.replace(",", "."))
    return float(bruto)  # 12 ou 12.5


def extrair_numeros(texto: str) -> list[tuple[float, str, bool]]:
    saida = []
    for m in _NUMERO.finditer(texto):
        bruto, porcento = m.group(1), bool(m.group(2))
        try:
            saida.append((_para_float(bruto), bruto + ("%" if porcento else ""), porcento))
        except ValueError:
            continue
    return saida


def _confere(valor: float, referencias: list[float]) -> bool:
    return any(abs(valor - r) <= max(0.6, 0.015 * abs(r)) for r in referencias)


def numeros_nao_conferidos(resposta: str, ficha: str) -> list[str]:
    referencias = [v for v, _, _ in extrair_numeros(ficha)]
    suspeitos = []
    for valor, bruto, porcento in extrair_numeros(resposta):
        if not porcento and valor <= 10 and float(valor).is_integer():
            continue  # contagens e enumerações ("3 dicas", "1.")
        if not porcento and 2000 <= valor <= 2035 and float(valor).is_integer():
            continue  # anos
        if not _confere(valor, referencias):
            suspeitos.append(bruto)
    return sorted(set(suspeitos), key=suspeitos.index)
