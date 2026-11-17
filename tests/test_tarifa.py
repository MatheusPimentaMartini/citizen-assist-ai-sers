"""Conta de luz: valores conferidos à mão (R$/kWh da REH ANEEL 3.596/2026)."""
import pytest

from energia.dados import carregar_parametros
from energia.tarifa import Tarifa, aliquota_icms, valor_conta, valor_sem_tributos

T = Tarifa.de_parametros(carregar_parametros())


def test_tarifas_da_aneel_em_reais_por_kwh():
    assert T.residencial_rs_kwh == pytest.approx(0.78938)          # 472,42 + 316,96 R$/MWh
    assert T.baixa_renda_rs_kwh == pytest.approx(0.62309)          # 306,31 + 316,78
    assert T.desconto_social_faixa1_rs_kwh == pytest.approx(0.63366)  # 316,88 + 316,78


@pytest.mark.parametrize("consumo, aliquota", [(0, 0), (90, 0), (90.5, 0.12), (200, 0.12), (200.1, 0.18), (500, 0.18)])
def test_faixas_de_icms_sp(consumo, aliquota):
    assert aliquota_icms(consumo, T) == aliquota


def test_conta_convencional_e_degrau_do_icms():
    # 200 kWh: 200 x 0,78938 / (0,94 x 0,88) = 190,856
    assert valor_conta(200, "convencional", T) == pytest.approx(190.856, abs=0.01)
    # 201 kWh muda a alíquota para 18%: 201 x 0,78938 / (0,94 x 0,82) = 205,846
    assert valor_conta(201, "convencional", T) == pytest.approx(205.846, abs=0.01)


def test_tarifa_social_gratuidade_ate_80_kwh():
    assert valor_conta(79, "tarifa_social", T) == 0
    assert valor_conta(80, "tarifa_social", T) == 0
    # 81 kWh: só 1 kWh cobrado, sem ICMS (até 90 kWh): 0,62309 / 0,94
    assert valor_conta(81, "tarifa_social", T) == pytest.approx(0.66286, abs=1e-4)


def test_desconto_social_faixas():
    assert valor_sem_tributos(120, "desconto_social", T) == pytest.approx(120 * 0.63366)
    assert valor_sem_tributos(121, "desconto_social", T) == pytest.approx(120 * 0.63366 + 0.78938)


def test_entradas_invalidas():
    with pytest.raises(ValueError):
        valor_conta(-1, "convencional", T)
    with pytest.raises(ValueError):
        valor_conta(100, "inexistente", T)
