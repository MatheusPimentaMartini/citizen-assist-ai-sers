# Testes técnicos (automatizados e manuais)

Rodar: `pip install -r requirements-dev.txt` e `pytest`.

| Arquivo | O que verifica |
| --- | --- |
| `tests/test_tarifa.py` | Tarifas ANEEL em R$/kWh; faixas de ICMS (0/90/90,5/200/200,1 kWh); degrau de ICMS entre 200 e 201 kWh; gratuidade da Tarifa Social (79/80/81 kWh); faixas do Desconto Social (120/121 kWh); entradas inválidas |
| `tests/test_modelo.py` | Vazão do chuveiro; energia térmica; L0 = P×t; ajuste de potência nunca passa da nominal; três dias do reservatório calculados à mão; sem sol o chuveiro faz tudo; validação de entradas |
| `tests/test_dados_e_analise.py` | Série diária completa (3.653 dias); média mensal no plano inclinado = CRESESB; fator de emissão médio de 2025 = MCTI; cenário de referência coerente; aviso quando a conta é menor que o chuveiro; Tarifa Social reduz a economia em R$; sensibilidade pessimista reduz a fração solar; custo do chuveiro na conta = conta com − conta sem o chuveiro, e nenhuma economia passa desse valor; porcentagem não arredonda 99,9% para 100% |
| `tests/test_assistente.py` | Detecção de intenções; leitura de números em pt-BR; modo cálculo só usa números da ficha; verificador aponta número inventado; erros 401/402/403/404/429 e timeout viram mensagens; falha da IA cai no modo cálculo sem vazar a chave; resposta da IA é conferida e enviada com a ficha |
| `tests/test_app.py` | Caminho da pessoa na interface, sem navegador (`streamlit.testing`): abre com apresentação e formulário (sem resultado inventado antes de calcular); calcular mostra cartões e selos; mudar a potência recalcula e as respostas continuam guardadas ao trocar de seção; banho "eficiente" mais longo que o de hoje é ajustado com aviso; assistente responde sem chave no modo cálculo; pergunta sugerida vira pergunta; limpar conversa; seção Fontes |
| `tests/test_integracao_http.py` | Ponta a ponta com um servidor HTTP falso no formato da API do Ollama: o app envia a ficha de cálculo e mostra a resposta como IA generativa |

Resultado na última execução: **62 testes aprovados** (Python 3.13, pandas 3.0, Streamlit 1.67), em 17/11/2026, depois da interface versão 2. A execução anterior da equipe, com a versão 1, teve 55 testes aprovados.

## Interface versão 2 (17/11/2026)

Verificação automatizada no ambiente de desenvolvimento, com `scripts/capturar_telas.py` (Chrome sem janela, app local sem chave):

| Tela | Rolagem horizontal | Botões com menos de 44 px | Erros de JavaScript |
| --- | --- | --- | --- |
| Celular (390 × 844) | não | nenhum | nenhum |
| Computador (1280 × 900) | não | nenhum | nenhum |

App publicado conferido em 17/11/2026, depois do deploy da versão 2 (navegador com tela emulada de celular, 375 × 812, e de computador, 1280 × 900): as seções abrem; "Calcular minha economia" leva até o resultado com os mesmos valores de `docs/resultados.md` (conta R$ 199,07 / R$ 151,17 / R$ 105,74 por mês); as respostas continuam guardadas ao voltar para Simular; o assistente mostra "IA generativa ativa (Ollama Cloud · modelo gpt-oss:20b)" e a pergunta sugerida "O aquecedor solar vale a pena para mim?" foi respondida pela IA com o rótulo "Resposta da IA generativa", com cenário pessimista, limitações e fontes, sem aviso do verificador; sem rolagem horizontal nas duas larguras.

Na primeira execução do script o botão "Limpar conversa" tinha menos de 44 px; o `estilo.css` passou a dar 48 px também a esse tipo de botão. Capturas e decisões: [`interface.md`](interface.md).

Checklist manual com a interface nova (cada integrante, no próprio celular):

- [ ] Responder as perguntas, tocar em "Calcular minha economia" e a tela ir sozinha até o resultado.
- [ ] Trocar de seção (Simular, Assistente, Fontes) e voltar: as respostas continuam lá.
- [ ] Tocar numa pergunta sugerida e receber resposta com o rótulo "IA generativa".
- [ ] Desligar "Usar IA generativa" (em "Como o assistente funciona e quais números ele usa") e receber resposta em "Modo cálculo".
- [ ] Ler tudo sem precisar dar zoom e sem a tela "vazar" para os lados.

## Checklist manual da versão 1 (registro histórico)

Itens marcados pela equipe com a interface versão 1 (abas e barra lateral):

- [x] 17/11/2026 — Link abre sem login; aba Assistente mostra "IA generativa ativa" (Secrets configurado).
- [x] 17/11/2026 — Com `gpt-oss:120b` a API respondeu HTTP 402; o app mostrou o aviso e respondeu no modo cálculo (fallback funcionou). Ajuste: modelo padrão `gpt-oss:20b` e mensagem específica para 402.
- [x] 17/11/2026 — Com `gpt-oss:20b` também HTTP 402; com o detalhe do serviço exibido, a causa ficou clara ("Add usage credits or subscribe"): a conta não tinha créditos. A equipe comprou US$ 5 de créditos e trocou a chave no Secrets.
- [x] 17/11/2026 — IA generativa respondeu com os números da ficha. O verificador acusou falso alarme porque a IA escreveu milhares com espaço ("R$ 3 359,57"). Ajustes: verificador aceita espaço como separador de milhar; instruções pedem números no formato da ficha, cenário pessimista ao falar do solar e linhas finais "Limitações:" e "Fontes:".
- [x] 17/11/2026 — Segunda resposta da IA: sem alertas do verificador, com cenário pessimista e linhas de limitações/fontes, mas chamou de "economia" o consumo restante do solar e citou "ficha de cálculo" como fonte. Ajustes: ficha com rótulos explícitos por alternativa e legenda fixa de fontes no app.
- [x] 17/11/2026 — Pergunta sobre Tarifa Social: a IA respeitou a regra de não inventar ("não tenho dados calculados") e citou fontes reais. Ajustes: ficha com os três perfis tarifários; chave do cache inclui instruções + ficha.
- [x] 17/11/2026 — Com a ficha nova, a IA respondeu sobre Tarifa Social com os números corretos (conta R$ 94,30/mês; economia do solar R$ 853,11/ano; retorno 3,9 anos). Ela tentou calcular um valor mensal por conta própria (R$ 70,92) e o **verificador sinalizou** o número — exatamente o comportamento esperado. Ela também aplicou o cenário pessimista do perfil convencional à Tarifa Social; ajuste: o título da sensibilidade na ficha passa a dizer a qual perfil ela se refere.
- [x] 17/11/2026 — Matheus, Leonardo e Lucas, cada um no próprio computador e com o mesmo resultado: link abre em janela anônima, sem login.
- [x] 17/11/2026 — Matheus, Leonardo e Lucas: aba Assistente mostra "IA generativa ativa" e responde em menos de ~30 s.
- [x] 17/11/2026 — Matheus, Leonardo e Lucas: desligar o seletor "Usar IA generativa" → resposta aparece como "Modo cálculo" ([print](evidencias/2026-11-17_modo_calculo.png)).
- [x] 17/11/2026 — Matheus, Leonardo e Lucas: mudar a potência (7.000 → 7.500 W) altera os números da aba Comparação ([antes](evidencias/2026-11-17_potencia_7000W.jpg) · [depois](evidencias/2026-11-17_potencia_7500W.jpg)).
- [x] 17/11/2026 — Matheus, Leonardo e Lucas: perfil "Tarifa Social" com 150 kWh reduz a economia em R$ do solar.
- [x] 17/11/2026 — Testado por Matheus, Leonardo e Lucas em computadores diferentes (navegadores não anotados).
- [ ] Professor: enviar o link e anotar a data em que ele testou (se testar antes da entrega).
