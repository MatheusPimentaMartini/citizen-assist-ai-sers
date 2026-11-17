# Testes com usuários — roteiro do facilitador

**O que o PDF pede:** verificar a **compreensão** e a **utilidade** das orientações, registrando as **situações testadas**, os **comentários recebidos** e os **ajustes realizados**, sem expor dados pessoais desnecessários. O repositório deve conter os registros dos testes e dos ajustes, e o critério "Usabilidade e comunicação" (10 pontos) considera as evidências dos testes.

**O que é recomendação da equipe (não está no PDF):** testar com pelo menos 5 pessoas; incluir, se possível, 1 família de baixa renda e 1 pessoa com pouca prática em tecnologia.

## Quem convidar

- Pessoas que **não participaram do desenvolvimento**, de preferência do público do projeto: moram em casa e usam chuveiro elétrico (familiares, vizinhos, amigos).
- Meta da equipe: 5 ou mais no total (ex.: 2 + 2 + 1). Colegas de turma e o professor podem testar, mas registre como "avaliador técnico".

## Privacidade

- Nada de nome, telefone, endereço, foto do rosto, CPF ou número de cliente. Use códigos: P1, P2, P3...
- Conta de luz: anote só a **faixa** (ex.: "150–200 kWh"), nunca o valor exato ou a foto da conta.
- Peça para a pessoa **não digitar dados pessoais** no assistente (as perguntas vão para o Ollama Cloud).

## Roteiro (10 a 15 minutos)

**Antes de começar (fale assim):** "Estamos testando o aplicativo, não você. Não existe resposta errada. Vou pedir algumas tarefas; tente fazer sozinho(a) e vá falando em voz alta o que está pensando. Durante as tarefas eu não posso ajudar, porque quero ver se o app se explica sozinho. No final você pode perguntar tudo. Não vou anotar seu nome nem dados da sua conta."

**Durante:** a pessoa usa o próprio celular ou computador. Você observa e anota. Se ela perguntar algo, devolva: "O que você faria se eu não estivesse aqui?". Se travar por cerca de 2 minutos ou desistir, marque a tarefa, anote onde travou e dê a menor dica possível só para seguir para a próxima (anote que houve dica).

| # | Peça assim (sem dar a resposta) | **Sim** | **Parcial** | **Não** |
| --- | --- | --- | --- | --- |
| 1 | "Olhando esta tela, para quem é este aplicativo e o que ele faz?" | Fala de famílias/casas com chuveiro elétrico e de economizar energia no banho | Resposta vaga ("é sobre energia") | Não sabe ou responde algo errado |
| 2 | "Coloque as informações da sua casa e me diga quanto o chuveiro gasta por mês." | Abre "Sua casa" (no celular, pelo **»**), ajusta os dados e lê "Chuveiro hoje" (kWh/mês) | Lê o número sem ajustar os dados, precisou de dica, ou confunde com a conta inteira | Não encontra |
| 3 | "Qual opção economiza mais? E qual não custa nada?" | Solar (B) economiza mais **e** práticas (A) não custam nada | Acerta só uma | Não acerta nenhuma |
| 4 | "Pergunte ao assistente: 'O aquecedor solar vale a pena para mim?'. Depois faça uma pergunta sua." | Faz as duas perguntas e explica a resposta com as próprias palavras (inclui que é estimativa) | Faz só uma, ou não entende a resposta | Não encontra o assistente ou não pergunta |
| 5 | "Se quisesse saber de onde vêm esses números, onde procuraria? Me mostre." | Abre a aba Método e aponta pelo menos uma fonte (ex.: tarifa da ANEEL) | Só encontra com dica, ou só pela legenda de fontes do chat | Não encontra |

**Perguntas finais** (a própria pessoa dá a nota, de 1 = discordo totalmente a 5 = concordo totalmente):
clareza ("Entendi os resultados"), utilidade ("Isso me ajudaria a decidir algo em casa"), confiança ("Confio nos números, sabendo que são estimativas"), facilidade ("Foi fácil usar"). Depois: "O que você mudaria?" e "O que mais gostou?".

**Encerramento:** agradeça, responda às dúvidas e explique que as notas e comentários vão orientar os ajustes.

## Como registrar (logo após cada teste)

Uma linha por pessoa em `registros.csv`:

| Coluna | O que escrever |
| --- | --- |
| `codigo_participante`, `data` | P1, P2... e a data do teste |
| `perfil_geral` | Sem identificar: "mora em casa, 3 pessoas, chuveiro elétrico, conta 150–200 kWh" |
| `dispositivo` | celular ou computador |
| `modo_assistente` | o rótulo que apareceu na resposta: "IA generativa" ou "Modo cálculo" |
| `t1_...` a `t5_...` | sim / parcial / não (critérios da tabela acima) |
| `nota_..._1a5` | as notas que a **pessoa** deu |
| `comentarios` | o que a **pessoa disse** (frases dela) |
| `problemas_observados` | o que **você viu** (onde travou, o que confundiu, se precisou de dica) |
| `ajuste_relacionado` | deixe vazio; é preenchido depois com o número do ajuste em `ajustes.md` |

## Depois dos testes

1. Juntar os registros e listar os problemas que se repetiram (quantas pessoas, em qual tarefa).
2. Priorizar: o que impediu uma tarefa > o que confundiu > detalhe visual.
3. Fazer os ajustes e registrar cada um em `ajustes.md` (problema → participantes → ajuste → arquivo/commit).
4. Se possível, refazer a tarefa problemática com 1 ou 2 pessoas depois do ajuste.
5. Resumir no README: quantas pessoas, principais achados e ajustes.
