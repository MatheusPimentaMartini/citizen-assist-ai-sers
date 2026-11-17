"""Integração de ponta a ponta com um servidor HTTP falso no formato da API do Ollama.

Sobe um servidor local que imita POST /api/chat, aponta OLLAMA_HOST para ele e verifica que
o app envia a ficha de cálculo e mostra a resposta como IA generativa. Não usa internet nem chave real.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = Path(__file__).resolve().parent.parent / "app.py"
RECEBIDO = {}


class Falso(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        corpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        RECEBIDO.update(path=self.path, corpo=corpo)
        resposta = {"model": corpo["model"], "message": {"role": "assistant",
                    "content": "Com o solar, a economia estimada é de R$ 1.119,89 por ano (estimativa, SINAPI e ANEEL 2026)."},
                    "done": True}
        dados = json.dumps(resposta).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def log_message(self, *args):
        pass


@pytest.fixture()
def servidor():
    srv = HTTPServer(("127.0.0.1", 0), Falso)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def test_app_usa_ia_quando_configurada(monkeypatch, servidor):
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_HOST", servidor)
    monkeypatch.setenv("OLLAMA_MODEL", "modelo-teste")
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert any("IA generativa ativa" in s.value for s in at.success)
    at.chat_input[0].set_value("O aquecedor solar vale a pena?").run()
    assert not at.exception
    assert RECEBIDO["path"] == "/api/chat" and RECEBIDO["corpo"]["model"] == "modelo-teste"
    assert RECEBIDO["corpo"]["stream"] is False
    assert "FICHA DE CÁLCULO" in RECEBIDO["corpo"]["messages"][0]["content"]
    assert any("Resposta da IA generativa" in c.value for c in at.caption)
    assert not at.warning  # 1.119,89 está na ficha: nada a sinalizar
