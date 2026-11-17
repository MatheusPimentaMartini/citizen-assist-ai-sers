"""Dados do repositório e análise completa do cenário de referência."""
import pytest

from energia import BaseDados, Cenario, analisar, recomendacoes
from energia.analise import sensibilidade_solar


@pytest.fixture(scope="module")
def base():
    return BaseDados.carregar()


def test_serie_diaria_completa(base):
    c = base.clima
    assert len(c) == 3653 and c["data"].is_unique
    assert c["ghi_kwh_m2_dia"].between(0, 10).all()
    assert c["temp_agua_fria_c"].between(10, 30).all()


def test_media_mensal_no_plano_inclinado_igual_ao_cresesb(base):
    medias = base.clima.groupby("mes")["h_inclinado_kwh_m2_dia"].mean().round(2).tolist()
    assert medias == [4.37, 4.93, 4.71, 4.75, 4.41, 4.37, 4.33, 5.13, 4.45, 4.43, 4.38, 4.63]


def test_fator_de_emissao_2025(base):
    assert base.fator_emissao_mensal.mean() == pytest.approx(0.0461, abs=5e-4)  # média anual MCTI 2025


def test_cenario_de_referencia(base):
    res = analisar(Cenario(), base)
    L0, A, B = (res.alternativas[k] for k in ("L0", "A", "B"))
    # 5,5 kW x 32 min/dia x 365,3 dias
    assert L0["chuveiro_kwh_ano"] == pytest.approx(1071.5, abs=0.5)
    assert 0 < A["chuveiro_kwh_ano"] < L0["chuveiro_kwh_ano"]
    assert 0 <= B["chuveiro_kwh_ano"] <= A["chuveiro_kwh_ano"]
    assert 0 <= B["fracao_solar_ano"] <= 1
    assert A["investimento_rs"] == 0 and A["retorno_simples_anos"] is None
    assert B["retorno_simples_anos"] == pytest.approx(B["investimento_rs"] / B["economia_ano_rs"], abs=0.05)
    assert A["agua_m3_ano"] < L0["agua_m3_ano"] == B["agua_m3_ano"]
    assert len(recomendacoes(res)) >= 3


def test_consumo_da_conta_menor_que_o_chuveiro_gera_aviso(base):
    res = analisar(Cenario(consumo_conta_kwh=50), base)
    assert res.avisos and res.derivados["consumo_outros_aparelhos_kwh_mes"] == 0


def test_tarifa_social_limita_a_economia_em_reais(base):
    conv = analisar(Cenario(consumo_conta_kwh=150), base).alternativas["B"]
    social = analisar(Cenario(consumo_conta_kwh=150, perfil_tarifario="tarifa_social"), base).alternativas["B"]
    assert social["economia_kwh_ano"] == pytest.approx(conv["economia_kwh_ano"])
    assert social["economia_ano_rs"] < conv["economia_ano_rs"]


def test_sensibilidade_pessimista_reduz_cobertura(base):
    s = {x["id"]: x for x in sensibilidade_solar(Cenario(), base)}
    assert s["pessimista"]["fracao_solar_ano"] < s["coletor_minimo"]["fracao_solar_ano"] <= s["base"]["fracao_solar_ano"]
    assert s["vazao_maior"]["agua_m3_ano"] > s["base"]["agua_m3_ano"]
