"""Baixa novamente os dados de clima do Open-Meteo (reprodutibilidade).

Uso:  python scripts/coletar_open_meteo.py
Gera dados/open_meteo_irradiacao_diaria_sp_2016_2025.csv e dados/open_meteo_mensal_sp_2016_2025.csv.
Fonte: Open-Meteo Historical Weather API (https://open-meteo.com/en/docs/historical-weather-api), dados gratuitos.
Obs.: reanálises podem ser revisadas pelo provedor; pequenas diferenças na 2ª casa decimal são esperadas.
"""
from __future__ import annotations

import calendar
import csv
from pathlib import Path

import requests

URL = "https://archive-api.open-meteo.com/v1/archive"
PARAMS = {
    "latitude": -23.55,
    "longitude": -46.63,
    "start_date": "2016-01-01",
    "end_date": "2025-12-31",
    "daily": "shortwave_radiation_sum,temperature_2m_mean",
    "timezone": "America/Sao_Paulo",
}
PASTA = Path(__file__).resolve().parent.parent / "dados"


def main() -> None:
    r = requests.get(URL, params=PARAMS, timeout=60)
    r.raise_for_status()
    j = r.json()
    datas = j["daily"]["time"]
    rad = j["daily"]["shortwave_radiation_sum"]  # MJ/m² por dia
    temp = j["daily"]["temperature_2m_mean"]     # °C
    if any(v is None for v in rad + temp):
        raise SystemExit("Há dias sem dado; verifique antes de usar.")

    with open(PASTA / "open_meteo_irradiacao_diaria_sp_2016_2025.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["data", "ghi_kwh_m2_dia"])
        for d, v in zip(datas, rad):
            w.writerow([d, f"{v / 3.6:.2f}"])  # MJ/m² -> kWh/m²

    grupos: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for d, v, t in zip(datas, rad, temp):
        grupos.setdefault((int(d[:4]), int(d[5:7])), []).append((v / 3.6, t))
    with open(PASTA / "open_meteo_mensal_sp_2016_2025.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ano", "mes", "dias", "ghi_media_kwh_m2_dia", "temp_media_c"])
        for (ano, mes), vals in sorted(grupos.items()):
            ghi = sum(v for v, _ in vals) / len(vals)
            tm = sum(t for _, t in vals) / len(vals)
            w.writerow([ano, mes, calendar.monthrange(ano, mes)[1], f"{ghi:.3f}", f"{tm:.2f}"])
    print(f"Ponto da grade: {j['latitude']}, {j['longitude']} ({j['elevation']} m). Dias: {len(datas)}.")


if __name__ == "__main__":
    main()
