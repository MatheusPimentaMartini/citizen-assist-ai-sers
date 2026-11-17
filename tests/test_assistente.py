"""Assistente: modo cálculo, verificador de números e falhas da IA (sem chamar a internet)."""
import pytest
import requests

import assistente
from assistente import ConfigIA, responder
from assistente.contexto import montar_ficha
from assistente.modo_calculo import detectar_intencao
from assistente.ollama_cloud import ErroAutenticacao, ErroConexao, ErroLimite, ErroModelo, ErroPlano, conversar
from assistente.verificador import extrair_numeros, numeros_nao_conferidos
from energia import BaseDados, Cenario, analisar, recomendacoes
from energia.analise import sensibilidade_solar


@pytest.fixture(scope="module")
def caso():
    base = BaseDados.carregar()
    res = analisar(Cenario(), base)
    sens = sensibilidade_solar(Cenario(), base)
    return res, sens, recomendacoes(res, sens)


@pytest.mark.parametrize("pergunta, intencao", [
    ("O aquecedor solar vale a pena?", "solar"),
    ("Tenho tarifa social, muda algo?", "tarifa_social"),
    ("Como gastar menos no banho?", "economia"),
    ("Qual o impacto ambiental?", "ambiente"),
    ("Quanto pago de conta?", "conta"),
    ("Esses números são confiáveis?", "metodo"),
    ("oi", "saudacao"),
    ("Quem ganhou o jogo?", None),
])
def test_intencoes(pergunta, intencao):
    assert detectar_intencao(pergunta) == intencao


def test_numeros_pt_br():
    assert [v for v, _, _ in extrair_numeros("R$ 1.119,88; 46,6%; 3.0 anos; 1.071 kWh")] == [1119.88, 46.6, 3.0, 1071.0]


def test_modo_calculo_so_usa_numeros_da_ficha(caso):
    res, sens, recs = caso
    ficha = montar_ficha(res, sens, recs)
    for pergunta in ["o solar vale a pena?", "como economizar?", "quanto pago?", "impacto ambiental", "e no inverno?"]:
        r = responder(pergunta, res, sens, recs, ConfigIA(api_key=None), usar_ia=True)
        assert r.modo == "calculo" and "não é IA generativa" in r.texto
        assert numeros_nao_conferidos(r.texto, ficha) == []


def test_verificador_aponta_numero_inventado(caso):
    res, sens, recs = caso
    ficha = montar_ficha(res, sens, recs)
    assert numeros_nao_conferidos("A economia será de R$ 9.999,00 por ano.", ficha) == ["9.999,00"]


class RespostaFalsa:
    def __init__(self, status, corpo=None, text=""):
        self.status_code, self._corpo, self.text = status, corpo, text

    def json(self):
        if self._corpo is None:
            raise ValueError("sem json")
        return self._corpo


@pytest.mark.parametrize("status, erro", [(401, ErroAutenticacao), (402, ErroPlano), (403, ErroAutenticacao), (404, ErroModelo), (429, ErroLimite)])
def test_erros_http_viram_mensagens(monkeypatch, status, erro):
    monkeypatch.setattr(requests, "post", lambda *a, **k: RespostaFalsa(status))
    with pytest.raises(erro):
        conversar(ConfigIA(api_key="chave-de-teste"), [{"role": "user", "content": "oi"}])


def test_timeout_vira_erro_de_conexao(monkeypatch):
    def lento(*a, **k):
        raise requests.Timeout()
    monkeypatch.setattr(requests, "post", lento)
    with pytest.raises(ErroConexao):
        conversar(ConfigIA(api_key="chave-de-teste"), [{"role": "user", "content": "oi"}])


def test_falha_da_ia_cai_no_modo_calculo_sem_vazar_a_chave(monkeypatch, caso):
    res, sens, recs = caso
    monkeypatch.setattr(requests, "post", lambda *a, **k: RespostaFalsa(401))
    r = responder("o solar vale a pena?", res, sens, recs, ConfigIA(api_key="segredo-123"))
    assert r.modo == "calculo" and "IA generativa indisponível" in r.aviso
    assert "segredo-123" not in r.texto + r.aviso


def test_resposta_da_ia_e_conferida(monkeypatch, caso):
    res, sens, recs = caso
    corpo = {"message": {"role": "assistant", "content": "Economia estimada de R$ 1.119,88 por ano, mas 7.777 kWh."}}
    capturado = {}

    def falso_post(url, json, headers, timeout):
        capturado.update(url=url, headers=headers, json=json)
        return RespostaFalsa(200, corpo)

    monkeypatch.setattr(requests, "post", falso_post)
    r = responder("quanto economizo?", res, sens, recs, ConfigIA(api_key="k"))
    assert r.modo == "ia" and r.numeros_nao_conferidos == ["7.777"]
    assert capturado["url"] == "https://ollama.com/api/chat"
    assert capturado["headers"]["Authorization"] == "Bearer k"
    assert "FICHA DE CÁLCULO" in capturado["json"]["messages"][0]["content"]


def test_config_le_variaveis_de_ambiente(monkeypatch):
    monkeypatch.setenv("OLLAMA_API_KEY", "abc")
    monkeypatch.setenv("OLLAMA_MODEL", "gpt-oss:20b")
    cfg = ConfigIA.carregar(None)
    assert cfg.disponivel and cfg.modelo == "gpt-oss:20b" and cfg.host == "https://ollama.com"
    monkeypatch.delenv("OLLAMA_API_KEY")
    assert not ConfigIA.carregar({}).disponivel


def test_detalhe_do_erro_aparece_na_mensagem(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *a, **k: RespostaFalsa(402, {"error": "add credits to continue"}))
    with pytest.raises(ErroPlano, match="add credits to continue"):
        conversar(ConfigIA(api_key="chave-de-teste"), [{"role": "user", "content": "oi"}])


def test_numeros_com_espaco_de_milhar():
    # a IA às vezes escreve "R$ 3 359,57" ou "1 070 kWh"
    texto = "Investimento: R$ 3 359,57; economia R$ 1 119,89 (≈ 1 070 kWh/ano, 100 % do chuveiro); 4 pessoas"
    assert [v for v, _, _ in extrair_numeros(texto)] == [3359.57, 1119.89, 1070.0, 100.0, 4.0]


def test_resposta_real_da_ia_nao_gera_falso_alarme(caso):
    """Trecho da primeira resposta real do app publicado (17/11/2026), que antes gerava alerta falso."""
    res, sens, recs = caso
    ficha = montar_ficha(res, sens, recs)
    resposta = ("Investimento: R$ 3 359,57 (kit 2 m² + reservatório 200 L). Retorno simples: 3,0 anos. "
                "Economia anual: R$ 1 119,89 (≈ 1 070 kWh/ano, 100 % do chuveiro). CO₂: 0,1 kg/ano. "
                "Água: 36,6 m³/ano. Práticas eficientes: R$ 574,84/ano (499 kWh/ano) e 13,7 mil L. "
                "O solar cobre 99,9 % da energia do banho.")
    assert numeros_nao_conferidos(resposta, ficha) == []
