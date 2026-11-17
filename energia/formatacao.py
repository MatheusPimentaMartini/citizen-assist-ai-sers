"""Formatação de números no padrão brasileiro (1.234,56)."""
from __future__ import annotations


def num(valor: float, casas: int = 0) -> str:
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def reais(valor: float, casas: int = 2) -> str:
    sinal = "-" if valor < 0 else ""
    return f"{sinal}R$ {num(abs(valor), casas)}"


def pct(fracao: float, casas: int = 0) -> str:
    return f"{num(fracao * 100, casas)}%"


def anos(valor: float | None) -> str:
    if valor is None:
        return "não se paga com essa economia"
    return f"{num(valor, 1)} anos"
