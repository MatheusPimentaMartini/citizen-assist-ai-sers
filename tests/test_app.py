"""Teste do app sem navegador (streamlit.testing). Roda sem chave de IA: deve usar o modo cálculo."""
import pytest

pytest.importorskip("streamlit")
from pathlib import Path  # noqa: E402

from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parent.parent / "app.py"


def test_app_abre_e_responde_sem_chave(monkeypatch):
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    assert any("Citizen Assist AI" in t.value for t in at.title)
    assert any("Modo cálculo" in i.value for i in at.info)
    at.chat_input[0].set_value("O aquecedor solar vale a pena?").run()
    assert not at.exception
    textos = " ".join(m.value for m in at.markdown)
    assert "retorno" in textos and "não é IA generativa" in textos


def test_mudar_entradas_recalcula(monkeypatch):
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    antes = [m.value for m in at.metric][0]
    at.number_input[1].set_value(7500).run()  # potência
    depois = [m.value for m in at.metric][0]
    assert not at.exception and antes != depois
