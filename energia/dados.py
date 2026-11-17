"""Leitura dos dados do repositório (pasta dados/). Nada é baixado em tempo de execução."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .tarifa import Tarifa

PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"


def carregar_parametros(pasta: Path = PASTA_DADOS) -> dict:
    with open(pasta / "parametros.json", encoding="utf-8") as f:
        return json.load(f)


def carregar_clima(pasta: Path = PASTA_DADOS) -> pd.DataFrame:
    """Série diária 2016-2025 com irradiação no plano do coletor e temperatura da água fria.

    A irradiação diária horizontal do Open-Meteo é levada ao plano inclinado (34°, CRESESB)
    por um fator mensal: H_incl(d) = GHI(d) x H_CRESESB,34°(mês) / média GHI Open-Meteo(mês).
    Assim a média de cada mês fica igual à do Atlas/CRESESB e a variação dia a dia
    (dias nublados) vem da série real do Open-Meteo.
    """
    diario = pd.read_csv(pasta / "open_meteo_irradiacao_diaria_sp_2016_2025.csv", parse_dates=["data"])
    mensal = pd.read_csv(pasta / "open_meteo_mensal_sp_2016_2025.csv")
    cresesb = pd.read_csv(pasta / "cresesb_sundata_sao_paulo.csv").set_index("mes")

    diario["ano"] = diario["data"].dt.year
    diario["mes"] = diario["data"].dt.month
    diario = diario.merge(mensal[["ano", "mes", "temp_media_c"]], on=["ano", "mes"], how="left")
    if diario["temp_media_c"].isna().any():
        raise ValueError("Há dias sem temperatura mensal correspondente.")

    ghi_medio_mes = diario.groupby("mes")["ghi_kwh_m2_dia"].mean()
    fator = cresesb["inclinado_34graus_maior_minimo"] / ghi_medio_mes
    diario["fator_transposicao"] = diario["mes"].map(fator)
    diario["h_inclinado_kwh_m2_dia"] = diario["ghi_kwh_m2_dia"] * diario["fator_transposicao"]
    diario = diario.rename(columns={"temp_media_c": "temp_agua_fria_c"})
    return diario


def carregar_fator_emissao_mensal(pasta: Path = PASTA_DADOS, ano: int = 2025) -> pd.Series:
    fe = pd.read_csv(pasta / "mcti_fator_emissao_sin.csv")
    serie = fe[fe["ano"] == ano].set_index("mes")["fator_medio_tco2_mwh"]
    if len(serie) != 12:
        raise ValueError(f"Fator de emissão de {ano} incompleto.")
    return serie  # tCO2/MWh = kg CO2/kWh


@dataclass
class BaseDados:
    parametros: dict
    clima: pd.DataFrame
    tarifa: Tarifa
    fator_emissao_mensal: pd.Series

    @classmethod
    def carregar(cls, pasta: Path = PASTA_DADOS) -> "BaseDados":
        p = carregar_parametros(pasta)
        return cls(
            parametros=p,
            clima=carregar_clima(pasta),
            tarifa=Tarifa.de_parametros(p),
            fator_emissao_mensal=carregar_fator_emissao_mensal(pasta),
        )
