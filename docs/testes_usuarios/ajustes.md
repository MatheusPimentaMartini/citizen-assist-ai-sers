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
| T5 | Teste do app publicado | Ollama Cloud respondeu HTTP 402 (conta sem créditos) e a mensagem era genérica | Mensagem específica para 402 com o detalhe do serviço; modelo `gpt-oss:20b` (mais barato); compra de US$ 5 de créditos |
| T6 | Teste do app publicado | Verificador marcou como "não conferidos" números corretos escritos com espaço de milhar (R$ 3 359,57) | Verificador passa a aceitar espaço como separador de milhar + teste de regressão com a resposta real |
| T7 | Teste do app publicado | Resposta da IA não citava fontes nem o cenário pessimista do solar | Instruções exigem linhas finais "Limitações:" e "Fontes:" e o cenário pessimista ao falar do solar |
| T8 | Teste do app publicado | A IA chamou de "economia" o consumo restante do chuveiro (1 kWh/ano) e citou só "ficha de cálculo" como fonte | Ficha com rótulos explícitos ("consumo do chuveiro" × "energia economizada"); legenda fixa com as fontes abaixo de toda resposta; limitação registrada na metodologia |
| T9 | Teste do app publicado | Pergunta "O solar compensa com Tarifa Social?" ficou sem números (a ficha só tinha o perfil escolhido) | A ficha passa a trazer a mesma família nos três perfis tarifários (convencional, Tarifa Social, Desconto Social) e as regras da Lei 15.235/2025 |
| T10 | Teste do app publicado | Depois de mudar as instruções, o cache devolveu uma resposta antiga | A chave do cache inclui um código das instruções e da ficha; qualquer mudança gera resposta nova |
