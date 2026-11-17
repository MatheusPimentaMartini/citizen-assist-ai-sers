# Testes com usuários — roteiro

Objetivo: verificar se pessoas do público (ou próximas dele) **entendem** a comparação, **conseguem usar** o simulador e o assistente e **confiam** nas respostas, e registrar os ajustes feitos a partir disso.

## Quem convidar (mínimo 5 pessoas)

- Moradores de casas na Grande SP que usam chuveiro elétrico (familiares, vizinhos, colegas).
- Se possível, ao menos 1 pessoa de família com Tarifa Social ou renda baixa e ao menos 1 pessoa com pouca familiaridade com tecnologia.
- Professor/colegas também podem testar, mas registre separadamente (perfil "avaliador técnico").

## Cuidados (sem dados pessoais)

- Não registrar nome, CPF, endereço, número de cliente, foto ou valor exato da conta de terceiros. Use códigos: P1, P2, P3...
- Explique antes: "é um protótipo acadêmico; os valores são estimativas". Peça permissão para anotar comentários.
- Se a pessoa usar dados reais da conta, anote só a faixa (ex.: "150–200 kWh"), nunca o documento.

## Tarefas (10 a 15 minutos por pessoa)

Abrir o link do app (celular ou computador) e, sem ajuda:

1. Dizer, com as próprias palavras, **para quem é o app e o que ele compara**.
2. Preencher os dados da casa (pessoas, tempo de banho, potência, consumo da conta) e dizer **quanto o chuveiro gasta por mês**.
3. Dizer **qual alternativa economiza mais** e **qual não exige investimento**.
4. Na aba Assistente, perguntar: *"O aquecedor solar vale a pena para mim?"* e uma pergunta livre. Comentar se a resposta foi clara e se mostrou limitações.
5. Encontrar **de onde vêm os dados** (aba Método).

## Perguntas finais (notas de 1 a 5)

- Clareza: "Entendi os resultados." 
- Utilidade: "Isso me ajudaria a decidir o que fazer em casa."
- Confiança: "Confio nos números, sabendo que são estimativas."
- Facilidade: "Foi fácil usar."
- Aberta: "O que você mudaria?" e "O que mais gostou?"

## Como registrar

- Uma linha por participante em `registros.csv` (pode editar no Excel/Google Planilhas e exportar CSV).
- Cada problema relevante vira uma linha em `ajustes.md`, com o que foi mudado e o commit/arquivo correspondente.
- Se um ajuste não for feito (prazo, fora do escopo), registre o motivo — isso também conta como análise.
