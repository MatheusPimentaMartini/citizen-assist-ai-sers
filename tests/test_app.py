"""Teste do app sem navegador (streamlit.testing). Roda sem chave de IA: deve usar o modo cálculo.

Cobre o caminho que uma pessoa faz no celular: abrir, responder as perguntas, calcular,
ir ao assistente, perguntar (digitando e tocando numa sugestão) e abrir as fontes.
"""
import pytest

pytest.importorskip("streamlit")
from pathlib import Path  # noqa: E402

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parent.parent / "app.py"


def _abrir(monkeypatch):
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    at = AppTest.from_file(str(APP), default_timeout=90).run()
    assert not at.exception
    return at


def _textos(at):
    return " ".join(m.value for m in at.markdown).replace("\xa0", " ")


def test_abre_com_apresentacao_e_formulario(monkeypatch):
    at = _abrir(monkeypatch)
    assert any("Energia no banho" in t.value for t in at.title)
    assert any("CITIZEN ASSIST AI" in c.value for c in at.caption)
    assert at.button_group(key="secao").value == "simular"
    assert at.number_input(key="f_pessoas").value == 4
    assert at.number_input(key="f_potencia").value == 5500
    # antes de calcular, só a orientação (nenhum resultado inventado na tela)
    assert not at.metric
    assert any("Calcular minha economia" in i.value for i in at.info)


def test_calcular_mostra_cartoes_e_selos_conferidos(monkeypatch):
    at = _abrir(monkeypatch)
    at.button(key="calcular").click().run()
    assert not at.exception
    rotulos = [m.label for m in at.metric]
    assert rotulos == ["Conta de energia por mês", "Você economiza por mês", "Você economiza por mês"]
    textos = _textos(at)
    assert "Sem custo inicial" in textos and "Maior economia" in textos
    assert "cenário pessimista" in " ".join(c.value for c in at.caption)
    assert any(s.value == "2. O resultado da sua casa" for s in at.subheader)


def test_mudar_entradas_recalcula(monkeypatch):
    at = _abrir(monkeypatch)
    at.button(key="calcular").click().run()
    antes = at.metric[0].value
    at.number_input(key="f_potencia").set_value(7500)
    at.button(key="calcular").click().run()
    assert not at.exception and at.metric[0].value != antes
    # as respostas continuam guardadas ao trocar de seção e voltar
    at.button_group(key="secao").set_value("fontes").run()
    at.button_group(key="secao").set_value("simular").run()
    assert at.number_input(key="f_potencia").value == 7500


def test_banho_com_pratica_nao_passa_do_banho_de_hoje(monkeypatch):
    at = _abrir(monkeypatch)
    at.slider(key="f_minutos").set_value(4)
    at.slider(key="f_minutos_a").set_value(10)
    at.button(key="calcular").click().run()
    assert not at.exception
    assert at.session_state["casa"]["minutos_a"] == 4
    assert any("usamos 4 min" in i.value for i in at.info)


def test_assistente_responde_sem_chave_no_modo_calculo(monkeypatch):
    at = _abrir(monkeypatch)
    at.button(key="calcular").click().run()
    at.button(key="ir_assistente").click().run()
    assert at.session_state["secao"] == "assistente"
    assert any("Modo cálculo" in i.value for i in at.info)
    at.chat_input(key="chat").set_value("O aquecedor solar vale a pena?").run()
    assert not at.exception
    textos = _textos(at)
    assert "retorno" in textos and "não é IA generativa" in textos


def test_pergunta_sugerida_vira_pergunta(monkeypatch):
    at = _abrir(monkeypatch)
    at.button_group(key="secao").set_value("assistente").run()
    assert any("família de exemplo" in i.value for i in at.info)  # ainda não calculou: avisa
    at.button_group(key="sugestao").set_value("Quanto o chuveiro pesa na minha conta?").run()
    assert not at.exception
    textos = _textos(at)
    assert "Quanto o chuveiro pesa na minha conta?" in textos
    assert "vêm do chuveiro" in textos
    assert at.button_group(key="sugestao").value is None  # pronta para outro toque
    at.button(key="limpar").click().run()
    assert at.session_state["mensagens"] == []


def test_secao_fontes_mostra_fontes_e_limitacoes(monkeypatch):
    at = _abrir(monkeypatch)
    at.button_group(key="secao").set_value("fontes").run()
    assert not at.exception
    textos = _textos(at)
    assert "ANEEL" in textos and "INMETRO" in textos and "Limitações" in textos
    assert "referencias.md" in textos
