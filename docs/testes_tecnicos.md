# Testes técnicos (automatizados e manuais)

Rodar: `pip install -r requirements-dev.txt` e `pytest`.

| Arquivo | O que verifica |
| --- | --- |
| `tests/test_tarifa.py` | Tarifas ANEEL em R$/kWh; faixas de ICMS (0/90/90,5/200/200,1 kWh); degrau de ICMS entre 200 e 201 kWh; gratuidade da Tarifa Social (79/80/81 kWh); faixas do Desconto Social (120/121 kWh); entradas inválidas |
| `tests/test_modelo.py` | Vazão do chuveiro; energia térmica; L0 = P×t; ajuste de potência nunca passa da nominal; três dias do reservatório calculados à mão; sem sol o chuveiro faz tudo; validação de entradas |
| `tests/test_dados_e_analise.py` | Série diária completa (3.653 dias); média mensal no plano inclinado = CRESESB; fator de emissão médio de 2025 = MCTI; cenário de referência coerente; aviso quando a conta é menor que o chuveiro; Tarifa Social reduz a economia em R$; sensibilidade pessimista reduz a fração solar |
| `tests/test_assistente.py` | Detecção de intenções; leitura de números em pt-BR; modo cálculo só usa números da ficha; verificador aponta número inventado; erros 401/402/403/404/429 e timeout viram mensagens; falha da IA cai no modo cálculo sem vazar a chave; resposta da IA é conferida e enviada com a ficha |
| `tests/test_app.py` | App abre sem chave (modo cálculo), responde no chat e recalcula ao mudar a potência (sem navegador, `streamlit.testing`) |
| `tests/test_integracao_http.py` | Ponta a ponta com um servidor HTTP falso no formato da API do Ollama: o app envia a ficha de cálculo e mostra a resposta como IA generativa |

Resultado na última execução da equipe: **54 testes aprovados** (Python 3.13, pandas 3.0, Streamlit 1.67).

## Checklist manual após publicar (marcar com data)

- [x] 17/11/2026 — Link abre sem login; aba Assistente mostra "IA generativa ativa" (Secrets configurado).
- [x] 17/11/2026 — Com `gpt-oss:120b` a API respondeu HTTP 402; o app mostrou o aviso e respondeu no modo cálculo (fallback funcionou). Ajuste: modelo padrão `gpt-oss:20b` e mensagem específica para 402.
- [x] 17/11/2026 — Com `gpt-oss:20b` também HTTP 402; com o detalhe do serviço exibido, a causa ficou clara ("Add usage credits or subscribe"): a conta não tinha créditos. A equipe comprou US$ 5 de créditos e trocou a chave no Secrets.
- [x] 17/11/2026 — IA generativa respondeu com os números da ficha. O verificador acusou falso alarme porque a IA escreveu milhares com espaço ("R$ 3 359,57"). Ajustes: verificador aceita espaço como separador de milhar; instruções pedem números no formato da ficha, cenário pessimista ao falar do solar e linhas finais "Limitações:" e "Fontes:".
- [ ] Link abre em janela anônima, sem login.
- [ ] Aba Assistente mostra "IA generativa ativa" e responde em menos de ~30 s.
- [ ] Desligar o seletor "Usar IA generativa" → resposta aparece como "Modo cálculo".
- [ ] Mudar a potência para 7.500 W altera os números da aba Comparação.
- [ ] Perfil "Tarifa Social" com 150 kWh reduz a economia em R$ do solar.
- [ ] Testado por Leonardo, Lucas e professor em outros computadores (anotar data e navegador).
