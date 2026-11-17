"""Modelo do banho: casos pequenos calculados à mão."""
import pandas as pd
import pytest

from energia.modelo import (
    Familia, PraticasEficientes, Premissas, SistemaSolar, energia_termica_kwh, simular, vazao_l_min,
)


def clima_sintetico(dias=3, temp=20.0, h=4.889):
    datas = pd.date_range("2025-07-01", periods=dias, freq="D")
    return pd.DataFrame({
        "data": datas, "ano": datas.year, "mes": datas.month,
        "temp_agua_fria_c": temp, "h_inclinado_kwh_m2_dia": h,
    })


def test_vazao_do_chuveiro():
    # 5500 W x 0,95 = m' x 4186 x 23,9  ->  0,05223 kg/s = 3,134 L/min
    assert vazao_l_min(5500, 0.95, 23.9) == pytest.approx(3.1336, abs=1e-3)


def test_energia_termica():
    # 100 L aquecidos 20 K: 100 x 4,186 x 20 / 3600 = 2,3256 kWh
    assert energia_termica_kwh(100, 20) == pytest.approx(2.3256, abs=1e-4)


def test_linha_de_base_e_potencia_vezes_tempo():
    sim = simular(clima_sintetico(), Familia(4, 8, 5500), PraticasEficientes(5, False), SistemaSolar(), Premissas())
    assert sim["e_l0_kwh"].iloc[0] == pytest.approx(5.5 * 32 / 60)   # 2,933 kWh/dia
    assert sim["e_a_kwh"].iloc[0] == pytest.approx(5.5 * 20 / 60)    # só o tempo menor
    # No mês mais frio (único mês), a necessidade térmica = η x energia elétrica de L0
    assert sim["necessidade_kwh"].iloc[0] == pytest.approx(0.95 * 5.5 * 32 / 60)


def test_ajuste_de_potencia_nunca_passa_da_nominal():
    clima = pd.concat([clima_sintetico(temp=15.0), clima_sintetico(temp=25.0).assign(mes=1)])
    sim = simular(clima, Familia(1, 10, 5500), PraticasEficientes(10, True), SistemaSolar(), Premissas())
    assert (sim["e_a_kwh"] <= sim["e_l0_kwh"] + 1e-9).all()
    quente = sim[sim["temp_agua_fria_c"] == 25.0]["e_a_kwh"].iloc[0]
    assert quente == pytest.approx(5.5 * 10 / 60 * (40 - 25) / (40 - 15))


def test_reservatorio_dia_a_dia():
    """1 pessoa, 10 min, água a 20 °C, sol igual ao dia padrão do INMETRO.

    vazão = 5500 x 0,95 x 60 / (4186 x 20) = 3,7446 L/min -> 37,446 L/dia
    necessidade = 37,446 x 4,186 x 20 / 3600 = 0,87083 kWh/dia
    sol disponível = 90,9/30 x 2 / 1,15 = 5,2696 kWh/dia
    perda k = 0,27 x 3600 / (30 x 29 x 4,186) = 0,26693 por dia
    capacidade = 200 x 4,186 x (60 - 20) / 3600 = 9,3022 kWh
    dia 1: 0 + 5,2696 - 0,8708 = 4,3987
    dia 2: 4,3987 - 1,1742 + 5,2696 - 0,8708 = 7,6233
    dia 3: min(9,3022; 7,6233 - 2,0349 + 5,2696) - 0,8708 = 8,4314
    """
    sim = simular(clima_sintetico(), Familia(1, 10, 5500), PraticasEficientes(5), SistemaSolar(), Premissas())
    assert sim["necessidade_kwh"].iloc[0] == pytest.approx(0.87083, abs=1e-4)
    assert sim["solar_disponivel_kwh"].iloc[0] == pytest.approx(5.2696, abs=1e-4)
    assert SistemaSolar().perda_diaria_fracao() == pytest.approx(0.26693, abs=1e-4)
    assert list(sim["estoque_fim_dia_kwh"].round(3)) == pytest.approx([4.399, 7.623, 8.431], abs=2e-3)
    assert (sim["fracao_solar"] == 1).all() and (sim["e_b_kwh"] == 0).all()


def test_sem_sol_o_chuveiro_faz_tudo():
    sim = simular(clima_sintetico(h=0.0), Familia(), PraticasEficientes(), SistemaSolar(), Premissas())
    assert (sim["fracao_solar"] == 0).all()
    assert sim["e_b_kwh"].sum() == pytest.approx(sim["e_l0_kwh"].sum())


@pytest.mark.parametrize("familia", [Familia(0, 8, 5500), Familia(4, 0, 5500), Familia(4, 8, 100)])
def test_entradas_invalidas(familia):
    with pytest.raises(ValueError):
        simular(clima_sintetico(), familia, PraticasEficientes(1), SistemaSolar(), Premissas())


def test_pratica_nao_pode_ser_maior_que_o_banho_atual():
    with pytest.raises(ValueError):
        simular(clima_sintetico(), Familia(4, 5, 5500), PraticasEficientes(8), SistemaSolar(), Premissas())
