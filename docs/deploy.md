# Publicação, configuração da IA e execução local

## Arquitetura escolhida (e por quê)

```
Navegador (professor, colegas, usuários)
        │  link público, sem instalar nada
        ▼
Streamlit Community Cloud  ── roda app.py + pacote energia/ (cálculos)
        │  chave OLLAMA_API_KEY guardada em Secrets (servidor)
        ▼
Ollama Cloud  (POST https://ollama.com/api/chat)  ── só redige a resposta a partir da ficha de cálculo
```

| Critério | Ollama local | Ollama Cloud via backend (escolhido) |
| --- | --- | --- |
| Quem testa precisa instalar algo? | Sim (Ollama + modelo de vários GB) | Não, só abre o link |
| Depende do computador do aluno? | Sim (RAM/GPU; no nosso caso não estava funcionando) | Não |
| Custo | Grátis, mas pesado | Créditos pré-pagos: menos de US$ 0,001 por pergunta (US$ 5 comprados) |
| Segurança da chave | Não há chave | Chave fica só no servidor (Secrets), nunca no código |
| Se a IA falhar | O app inteiro para de responder | O app continua no **modo cálculo** |

O Streamlit Community Cloud foi escolhido porque é gratuito, publica direto do repositório GitHub e tem um cofre de segredos. Os cálculos não dependem da IA: com ou sem chave, o simulador e o modo cálculo funcionam.

## Passo a passo — publicar o app (feito uma vez, pelo dono do repositório)

1. Acesse https://share.streamlit.io e entre com a conta do GitHub (`MatheusPimentaMartini`).
2. Clique em **Create app** → **Deploy a public app from GitHub**.
3. Preencha: repositório `MatheusPimentaMartini/citizen-assist-ai-sers`, branch `main`, arquivo principal `app.py`. Em **App URL**, escolha um endereço curto (ex.: `citizen-assist-sers`).
4. Abra **Advanced settings**: escolha Python 3.12 e, em **Secrets**, cole (com a sua chave):
   ```toml
   OLLAMA_API_KEY = "sua-chave-aqui"
   OLLAMA_MODEL = "gpt-oss:20b"
   ```
5. Clique em **Deploy** e aguarde a instalação (1 a 3 minutos).
6. Teste numa **janela anônima** do navegador: o aviso verde "IA generativa ativa" deve aparecer na seção Assistente. Faça uma pergunta.
7. Envie o link para Leonardo, Lucas e o professor e peça para testarem do computador/celular deles.

### Criar a chave do Ollama Cloud

1. Entre em https://ollama.com e faça login.
2. Vá em **Settings → Keys** (https://ollama.com/settings/keys) e crie uma chave.
3. Copie a chave **direto para o campo Secrets** do Streamlit. Não cole a chave em chat, e-mail, código, README, commits ou prints.
4. Se a chave vazar: apague-a em ollama.com/settings/keys, crie outra e atualize o Secrets (Settings → Secrets → Save). O app reinicia sozinho.

### Trocar o modelo

Usamos `gpt-oss:20b`. Em 17/11/2026 a página de preços do Ollama (https://ollama.com/pricing) já não oferecia cota gratuita na nuvem: o plano de entrada é **"Pay as you go"** (US$ 0/mês, pagamento por token com créditos). Nos testes do app publicado, sem créditos, a API respondeu **HTTP 402** ("Add usage credits or subscribe") para `gpt-oss:120b` e para `gpt-oss:20b`, e o app caiu corretamente no modo cálculo. A equipe comprou **US$ 5 de créditos** (valor mínimo), sem assinatura, e a IA passou a responder.

**Custo estimado** (tabela oficial: `gpt-oss:20b` = US$ 0,07 por milhão de tokens de entrada e US$ 0,30 por milhão de saída): cada pergunta envia cerca de 3 mil tokens (instruções + ficha de cálculo) e recebe até ~800, ou seja, **menos de US$ 0,001 por pergunta** — os US$ 5 cobrem milhares de perguntas. Os limites do app (15 por sessão, 120 por hora) impedem gasto alto se o link circular. Para trocar o modelo, edite `OLLAMA_MODEL` no Secrets (lista em https://ollama.com/search?c=cloud); `gpt-oss:120b` custa cerca do dobro por pergunta.

## Como o app lida com falhas

| Situação | O que o usuário vê |
| --- | --- |
| Sem chave configurada | Aviso azul "Modo cálculo" e respostas por regras (identificadas como "não é IA generativa") |
| Chave inválida/revogada (401/403) | "A chave da IA foi recusada…" + resposta no modo cálculo |
| Modelo fora do plano ou sem créditos (402) | "A conta do Ollama Cloud não tem plano ou créditos para o modelo…" + modo cálculo |
| Modelo indisponível (404) | "O modelo … não está disponível…" + modo cálculo |
| Limite de uso do Ollama (429) | "Limite de uso da IA atingido…" + modo cálculo |
| Serviço fora do ar (5xx) ou demora > 45 s | Mensagem de instabilidade/tempo + modo cálculo |
| Muitas perguntas | Limite de 15 perguntas à IA por sessão e 120 por hora no app (protege a cota gratuita); depois, modo cálculo |
| App "dormindo" (sem acesso por 12 h) | Página do Streamlit com o botão **"Yes, get this app back up!"** — qualquer pessoa pode clicar; volta em ~1 min |

A mesma pergunta para o mesmo cenário fica guardada em cache no servidor enquanto ele estiver ligado, economizando a cota.

## Executar localmente (Windows, macOS ou Linux)

Pré-requisito: Python 3.10 ou superior.

```bash
git clone https://github.com/MatheusPimentaMartini/citizen-assist-ai-sers.git
cd citizen-assist-ai-sers
python -m venv .venv
# Windows: .venv\Scripts\activate    |    macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
pytest                      # roda os testes automatizados
streamlit run app.py        # abre http://localhost:8501
```

Sem chave, o app abre no modo cálculo. Para usar a IA localmente, escolha **uma** opção:

- **Ollama Cloud**: copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml` e coloque a chave (esse arquivo está no `.gitignore` e nunca vai para o GitHub). Alternativa: variável de ambiente `OLLAMA_API_KEY`.
- **Ollama local** (se funcionar na máquina): instale o Ollama, rode `ollama pull gpt-oss:20b` e defina `OLLAMA_HOST = "http://localhost:11434"` e `OLLAMA_MODEL = "gpt-oss:20b"` no `secrets.toml`. Não precisa de chave.

Para regenerar as tabelas de resultados: `python scripts/gerar_resultados.py`. Para baixar de novo os dados de clima: `python scripts/coletar_open_meteo.py`.

### Pelo arquivo ZIP

No GitHub, **Code → Download ZIP** baixa todo o projeto (código, dados, documentação e testes). O ZIP **não contém nenhuma chave**: ela só existe no Secrets do Streamlit. Depois de descompactar, siga os mesmos comandos acima a partir de `python -m venv .venv`.

## Diferenças entre a versão online e a local

| Aspecto | Online (Streamlit Cloud) | Local |
| --- | --- | --- |
| Acesso | Link público, qualquer navegador | `http://localhost:8501` só no próprio computador |
| IA generativa | Ollama Cloud com a chave do Secrets | Sem chave: modo cálculo. Com `secrets.toml` ou Ollama local: IA |
| Cálculos e dados | Idênticos (mesmo código e mesmos CSV do repositório) | Idênticos |
| Disponibilidade | Pode "dormir" após 12 h sem uso; acorda com um clique | Enquanto o terminal estiver aberto |
| Limites | Créditos da conta Ollama + limites do app (15/sessão, 120/hora) | Os da conta/máquina usada |

## Segurança e privacidade

- Nenhuma chave no código, no histórico do Git ou no ZIP (`.streamlit/secrets.toml` e `.env` estão no `.gitignore`; há apenas o modelo `secrets.toml.example`).
- O app não grava conversas nem dados de quem usa. Com a IA ativa, a pergunta e a ficha de cálculo (números da simulação, sem dados pessoais) são enviadas ao Ollama Cloud. A interface pede para não digitar dados pessoais.
