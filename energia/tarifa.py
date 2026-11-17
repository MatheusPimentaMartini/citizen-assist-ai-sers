"""Conta de luz (parcela de energia) para consumidores residenciais B1 da Enel SP.

Valor com tributos "por dentro":

    conta = valor_sem_tributos / ((1 - PIS/COFINS) x (1 - ICMS))

A alíquota de ICMS em SP depende do consumo TOTAL do mês (isento até 90 kWh,
12% até 200 kWh, 18% acima). Por isso a economia é calculada como
conta(consumo atual) - conta(consumo com a alternativa), e não como kWh x preço fixo.
Não inclui bandeiras tarifárias nem contribuição de iluminação pública (COSIP).
"""
from __future__ import annotations

from dataclasses import dataclass

PERFIS = {
    "convencional": "Residencial convencional",
    "tarifa_social": "Tarifa Social (CadÚnico, renda por pessoa de até ½ salário mínimo): até 80 kWh/mês gratuitos",
    "desconto_social": "Desconto Social (renda por pessoa entre ½ e 1 salário mínimo): até 120 kWh/mês com tarifa reduzida",
}


@dataclass(frozen=True)
class Tarifa:
    residencial_rs_kwh: float
    baixa_renda_rs_kwh: float
    desconto_social_faixa1_rs_kwh: float
    gratuidade_kwh: float = 80.0
    limite_desconto_social_kwh: float = 120.0
    pis_cofins: float = 0.06
    faixas_icms: tuple = ((90.0, 0.0), (200.0, 0.12), (None, 0.18))

    @classmethod
    def de_parametros(cls, p: dict) -> "Tarifa":
        t = p["tarifa"]
        mwh = lambda tusd, te: (t[tusd] + t[te]) / 1000  # R$/MWh -> R$/kWh
        return cls(
            residencial_rs_kwh=mwh("residencial_tusd_rs_mwh", "residencial_te_rs_mwh"),
            baixa_renda_rs_kwh=mwh("baixa_renda_tusd_rs_mwh", "baixa_renda_te_rs_mwh"),
            desconto_social_faixa1_rs_kwh=mwh(
                "desconto_social_faixa1_tusd_rs_mwh", "desconto_social_faixa1_te_rs_mwh"
            ),
            gratuidade_kwh=t["tarifa_social_gratuidade_kwh"]["valor"],
            limite_desconto_social_kwh=t["desconto_social_limite_kwh"]["valor"],
            pis_cofins=t["pis_cofins"]["valor"],
            faixas_icms=tuple((lim, aliq) for lim, aliq in t["icms_faixas"]["valor"]),
        )


def aliquota_icms(consumo_kwh: float, tarifa: Tarifa) -> float:
    for limite, aliquota in tarifa.faixas_icms:
        if limite is None or consumo_kwh <= limite:
            return aliquota
    return tarifa.faixas_icms[-1][1]


def valor_sem_tributos(consumo_kwh: float, perfil: str, tarifa: Tarifa) -> float:
    if consumo_kwh < 0:
        raise ValueError("Consumo não pode ser negativo.")
    if perfil == "convencional":
        return consumo_kwh * tarifa.residencial_rs_kwh
    if perfil == "tarifa_social":
        cobrado = max(0.0, consumo_kwh - tarifa.gratuidade_kwh)
        return cobrado * tarifa.baixa_renda_rs_kwh
    if perfil == "desconto_social":
        faixa1 = min(consumo_kwh, tarifa.limite_desconto_social_kwh)
        faixa2 = max(0.0, consumo_kwh - tarifa.limite_desconto_social_kwh)
        return faixa1 * tarifa.desconto_social_faixa1_rs_kwh + faixa2 * tarifa.residencial_rs_kwh
    raise ValueError(f"Perfil tarifário desconhecido: {perfil}")


def valor_conta(consumo_kwh: float, perfil: str, tarifa: Tarifa) -> float:
    """Parcela de energia da conta, com PIS/COFINS e ICMS (R$/mês)."""
    base = valor_sem_tributos(consumo_kwh, perfil, tarifa)
    divisor = (1 - tarifa.pis_cofins) * (1 - aliquota_icms(consumo_kwh, tarifa))
    return base / divisor
