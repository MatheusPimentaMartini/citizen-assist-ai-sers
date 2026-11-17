"""Cálculos energéticos do Citizen Assist AI (banho: convencional x uso eficiente x solar térmico)."""
from .analise import Cenario, Resultado, analisar, recomendacoes
from .dados import BaseDados
from .modelo import Familia, PraticasEficientes, Premissas, SistemaSolar

__all__ = [
    "BaseDados", "Cenario", "Familia", "PraticasEficientes", "Premissas", "Resultado",
    "SistemaSolar", "analisar", "recomendacoes",
]
