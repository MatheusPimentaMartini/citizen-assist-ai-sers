"""Cliente mínimo da API de chat do Ollama (Ollama Cloud ou Ollama local).

A chave nunca é gravada em código: vem de st.secrets (Streamlit Cloud) ou da variável de
ambiente OLLAMA_API_KEY. Erros são traduzidos em mensagens simples, sem expor a chave.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

import requests

HOST_PADRAO = "https://ollama.com"
MODELO_PADRAO = "gpt-oss:20b"  # modelo de baixo uso, disponível no plano gratuito


class ErroIA(Exception):
    """Falha ao usar a IA generativa; a mensagem é segura para mostrar ao usuário."""


class ErroAutenticacao(ErroIA):
    pass


class ErroLimite(ErroIA):
    pass


class ErroModelo(ErroIA):
    pass


class ErroPlano(ErroIA):
    pass


class ErroConexao(ErroIA):
    pass


class ErroServidor(ErroIA):
    pass


@dataclass(frozen=True)
class ConfigIA:
    api_key: str | None = None
    host: str = HOST_PADRAO
    modelo: str = MODELO_PADRAO
    timeout_s: float = 45.0

    @classmethod
    def carregar(cls, segredos: Mapping | None = None) -> "ConfigIA":
        """Lê de st.secrets (se houver) e depois de variáveis de ambiente."""
        def ler(nome: str, padrao: str | None = None) -> str | None:
            if segredos is not None:
                try:
                    if nome in segredos and str(segredos[nome]).strip():
                        return str(segredos[nome]).strip()
                except Exception:  # st.secrets sem arquivo levanta erro ao acessar
                    pass
            valor = os.environ.get(nome, "").strip()
            return valor or padrao

        return cls(
            api_key=ler("OLLAMA_API_KEY"),
            host=ler("OLLAMA_HOST", HOST_PADRAO),
            modelo=ler("OLLAMA_MODEL", MODELO_PADRAO),
        )

    @property
    def local(self) -> bool:
        return any(h in self.host for h in ("localhost", "127.0.0.1"))

    @property
    def disponivel(self) -> bool:
        return self.local or bool(self.api_key)

    @property
    def descricao(self) -> str:
        onde = "Ollama local" if self.local else "Ollama Cloud"
        return f"{onde} · modelo {self.modelo}"


def conversar(config: ConfigIA, mensagens: list[dict], temperatura: float = 0.2) -> str:
    if not config.disponivel:
        raise ErroIA("IA generativa não configurada (falta a chave OLLAMA_API_KEY no servidor).")
    url = config.host.rstrip("/") + "/api/chat"
    cabecalho = {"Content-Type": "application/json"}
    if config.api_key and not config.local:
        cabecalho["Authorization"] = f"Bearer {config.api_key}"
    corpo = {
        "model": config.modelo,
        "messages": mensagens,
        "stream": False,
        "options": {"temperature": temperatura},
    }
    try:
        r = requests.post(url, json=corpo, headers=cabecalho, timeout=(10, config.timeout_s))
    except requests.Timeout as e:
        raise ErroConexao("A IA demorou demais para responder.") from e
    except requests.RequestException as e:
        raise ErroConexao("Não foi possível conectar ao serviço de IA.") from e

    if r.status_code in (401, 403):
        raise ErroAutenticacao("A chave da IA foi recusada (inválida, revogada ou sem permissão).")
    if r.status_code == 402:
        raise ErroPlano(
            f"A conta do Ollama Cloud não tem plano ou créditos para o modelo '{config.modelo}' (HTTP 402). "
            "Use um modelo do plano gratuito, como gpt-oss:20b, ou adicione créditos."
        )
    if r.status_code == 404:
        raise ErroModelo(f"O modelo '{config.modelo}' não está disponível no serviço de IA.")
    if r.status_code == 429:
        raise ErroLimite("Limite de uso da IA atingido no momento. Tente mais tarde.")
    if r.status_code >= 500:
        raise ErroServidor("O serviço de IA está instável no momento.")
    if r.status_code != 200:
        raise ErroIA(f"O serviço de IA respondeu com erro (HTTP {r.status_code}).")
    try:
        texto = r.json()["message"]["content"]
    except (ValueError, KeyError, TypeError) as e:
        raise ErroIA("Resposta da IA em formato inesperado.") from e
    if not texto or not texto.strip():
        raise ErroIA("A IA devolveu uma resposta vazia.")
    return texto.strip()
