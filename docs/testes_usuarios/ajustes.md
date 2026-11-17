# Ajustes realizados a partir dos testes

Preencha uma linha por problema encontrado nos testes com usuários (ver `roteiro.md` e `registros.csv`).

| # | Participante(s) | Problema observado | Ajuste feito | Arquivo/commit | Status |
| --- | --- | --- | --- | --- | --- |
| 1 |  |  |  |  |  |

## Ajustes anteriores, vindos de testes técnicos da equipe (não são testes com usuários)

| # | Origem | Problema | Ajuste |
| --- | --- | --- | --- |
| T1 | Teste do modelo | Com perdas só proporcionais à produção, o solar cobria 100% em todos os dias, o que é irreal | Incluída a perda diária do reservatório pelo limite do INMETRO (0,27 kWh/L·mês) |
| T2 | Revisão da análise | Resultado do solar dependia de premissas incertas | Criada a análise de sensibilidade com valores com fonte (coletor mínimo INMETRO, vazão do estudo da USP) |
| T3 | Teste do assistente | Resposta sobre "inverno" citava o mês errado (índice do mês deslocado) | Corrigido o índice e trocada a base para o consumo da alternativa A |
| T4 | Revisão de fontes | PMEe usado (90,8) diferia do datasheet (90,9) | Ajustado para o valor publicado pelo fabricante |
| T5 | Teste do app publicado | Ollama Cloud respondeu HTTP 402 para `gpt-oss:120b` (fora do plano gratuito); a mensagem era genérica | Modelo padrão `gpt-oss:20b` (baixo uso) e mensagem específica para o erro 402 |
