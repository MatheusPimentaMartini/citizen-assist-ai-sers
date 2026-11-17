# Metodologia

Este documento explica **o que** foi calculado, **como** e **por quê**. Todos os números do app, do README e do vídeo saem do código em `energia/` e dos dados em `dados/` (ver `docs/resultados.md`, gerado por `python scripts/gerar_resultados.py`).

## 1. Público e necessidade energética

- **Público**: famílias que moram em **casas** na Região Metropolitana de São Paulo, atendidas pela Enel SP, que aquecem a água do banho com **chuveiro elétrico** — com atenção especial às famílias de baixa renda (Tarifa Social e Desconto Social).
- **Necessidade**: banho quente diário para todos os moradores. No cenário de referência: 4 pessoas, 1 banho de 8 min por pessoa por dia, água a 40 °C.
- **Por que casas?** O aquecimento solar compacto precisa de telhado próprio com sol; em apartamentos a instalação depende do condomínio. O kit de referência do SINAPI (insumo 34472) é indicado para residências de até 120 m² e 4 a 5 banhos por dia.
- **Por que importa?** No cenário de referência o chuveiro responde por cerca de 45% do consumo da casa (89 kWh de 200 kWh/mês). A própria etiqueta INMETRO usada pelo Idec indica 88 kWh/mês para um chuveiro de 5.500 W.

## 2. Alternativas comparadas (mesma necessidade, mesmo período)

| Código | Alternativa | O que muda | Investimento |
| --- | --- | --- | --- |
| L0 | Chuveiro elétrico convencional (situação atual) | nada — potência fixa ("inverno") o ano todo | zero |
| A | Chuveiro elétrico com práticas de uso eficiente | banho de 5 min (Sabesp) e potência ajustada ao clima ("verão" quando a água chega morna) | zero |
| B | Aquecimento solar térmico + chuveiro como complemento | o sol pré-aquece a água; o chuveiro completa o que faltar | kit SINAPI 103517 |

As três alternativas são calculadas **dia a dia de 01/01/2016 a 31/12/2025** (3.653 dias) com os mesmos dados de clima e depois resumidas em um **ano típico** (média de cada mês entre os 10 anos). Isso atende ao requisito de comparar no mesmo período e para a mesma necessidade.

## 3. Equações

Notação: P = potência do chuveiro (W), η = eficiência do chuveiro (0,95), t = minutos de banho por dia (pessoas × minutos), c = 4,186 kJ/(kg·K), 1 L de água ≈ 1 kg, T_b = 40 °C, T_f = temperatura da água fria.

1. **Vazão do chuveiro** — o chuveiro precisa conseguir aquecer a água até 40 °C no mês mais frio (T_f,min = 16,1 °C, julho):
   `P·η = vazão·c·ΔT_max  →  vazão (L/min) = P·η·60 / (4186·ΔT_max)` → 3,13 L/min para 5.500 W.
2. **L0**: `E_L0 (kWh/dia) = P/1000 × t/60`. Para 4 × 8 min a 5,5 kW: 2,93 kWh/dia; 1.071,5 kWh/ano.
3. **A**: `E_A = P/1000 × min(1, ΔT_dia/ΔT_max) × t_A/60`, com t_A = 4 × 5 min. O fator de potência representa usar só a potência necessária para chegar a 40 °C em cada dia (posição "verão" nos meses quentes); nunca passa da potência nominal.
4. **Necessidade térmica (B)**, com os mesmos hábitos de L0: `Q (kWh/dia) = vazão × t × c × (T_b − T_f) / 3600`.
5. **Produção do coletor**, pelo ensaio do INMETRO (Portaria 301/2012), escalada pela irradiação do dia no plano do coletor:
   `P_sol = PMEe/30 × A × H_incl,dia / H_ref` com PMEe = 90,9 kWh/(mês·m²) (Komeco KOCS AP 2M, classe A), A = 2,0 m² (SINAPI), H_ref = 17,6 MJ/m² = 4,889 kWh/m² (dia padrão do ensaio). Energia disponível após perdas de circuito: `P_sol / 1,15` (perdas de 15%, método da ABNT NBR 15569 descrito por Ara e Sowmy, CBENS 2016).
6. **Reservatório (modelo de "balde")**: a cada dia, `estoque = min(capacidade, estoque × (1 − k) + disponível)`; os banhos retiram `min(estoque, Q)`.
   - Capacidade: `200 L × c × (60 °C − T_f) / 3600` (limite de armazenamento adotado: 60 °C).
   - Perda diária k: o INMETRO limita a perda específica de reservatórios de 100–300 L a **0,27 kWh/(L·mês)**, medida com água a 50 °C e ar a 21 °C (ΔT = 29 K). Pela lei de resfriamento de Newton, a fração do calor perdida por dia é `k = 0,27 × 3600 / (30 × 29 × 4,186) = 0,267`. Usamos o **limite máximo permitido** (cenário conservador).
7. **Fração solar** `f = Q_sol,usado / Q`; **consumo elétrico de B** `E_B = E_L0 × (1 − f)` — a parte que o sol não cobre continua no chuveiro, nas mesmas condições de uso de L0.
8. **Conta de energia (mês a mês)**: `conta = valor_sem_tributos / ((1 − PIS/COFINS) × (1 − ICMS))`.
   - Tarifa sem tributos (ANEEL, REH 3.596/2026, Enel SP, B1): residencial 0,78938 R$/kWh; Baixa Renda 0,62309 R$/kWh; Desconto Social faixa 01 0,63366 R$/kWh.
   - Tarifa Social (Lei 15.235/2025): desconto de 100% até 80 kWh/mês e 0% acima. Desconto Social: até 120 kWh/mês na faixa 01.
   - ICMS-SP pela faixa de consumo **total** do mês: isento até 90 kWh, 12% até 200 kWh, 18% acima. Por isso a economia é `conta(consumo atual) − conta(consumo com a alternativa)`, e não kWh × preço fixo: quando o consumo cai abaixo de 200 kWh a alíquota de todo o mês muda.
   - PIS/COFINS efetivo de 6,0%: estimado pelo grupo a partir de faturas públicas da Enel SP de 2026 (`tarifa_unitária = preço_com_tributos × (1 − PIS/COFINS) × (1 − ICMS)`): cinco faturas deram entre 6,0% e 6,05% e uma deu 4,3%, o que mostra que o valor muda de mês para mês.
   - O "consumo total" é informado pelo usuário (vem da conta); a parte que não é chuveiro é mantida constante.
9. **Retorno simples** = investimento ÷ economia anual (sem juros, inflação, reajustes ou manutenção).
10. **CO₂** = kWh do mês × fator médio mensal do SIN de 2025 (MCTI). **Água** = vazão × minutos de banho.

## 4. Dados de clima: duas fontes, cada uma no que faz melhor

| Fonte | O que fornece | Como usamos |
| --- | --- | --- |
| Open-Meteo (reanálise), 2016–2025 | irradiação **diária** horizontal e temperatura média | variação dia a dia (dias nublados) e temperatura da água fria |
| CRESESB SunData v3.0 (Atlas Brasileiro de Energia Solar, 2017) | irradiação média mensal no **plano inclinado** | nível médio mensal no coletor a 34° |

O Open-Meteo dá, em média, **9% a mais** de irradiação horizontal que o Atlas/CRESESB no mesmo ponto (4,85 × 4,45 kWh/m²·dia; até 21% a mais em julho). Como o Atlas foi feito com 17 anos de imagens de satélite para o Brasil, ancoramos o **nível** nele e usamos o Open-Meteo só para a **forma** da série:

`H_incl,dia = GHI_OpenMeteo,dia × (H_CRESESB,34°,mês / média GHI_OpenMeteo,mês)`

Assim a média de cada mês fica igual à do CRESESB (teste automatizado `test_media_mensal_no_plano_inclinado_igual_ao_cresesb`). A inclinação de 34° é a de "maior mínimo mensal" calculada pelo SunData: privilegia o inverno, quando a água chega mais fria.

A temperatura da água fria foi aproximada pela temperatura média mensal do ar (mesma aproximação usada por Vaz, Rodrigues e Ghisi para chuveiros em São Paulo).

## 5. Validação

- **Contas à mão** em testes automatizados (`tests/`): vazão, energia térmica, linha de base P×t, faixas de ICMS (90/90,5/200/200,1 kWh), gratuidade da Tarifa Social (79/80/81 kWh), Desconto Social (120/121 kWh) e três dias do reservatório calculados passo a passo.
- **Coerência com fontes**: L0 de 5.500 W com 32 min/dia dá 88 kWh em 30 dias — o mesmo valor da etiqueta INMETRO citada pelo Idec. A média anual de 2025 dos fatores do MCTI (0,0461 t/MWh) é reproduzida pelo código.
- **Transcrição dos dados**: as 120 médias mensais recalculadas a partir dos 3.653 dias baixados bateram com as médias de uma coleta independente anterior (diferença ≤ 0,006 kWh/m²·dia, arredondamento).

## 6. Sensibilidade (por que o solar dá perto de 100%)

O kit SINAPI (2 m², 200 L) foi feito para 4–5 banhos por dia com aquecedor solar, enquanto a família de referência usa só ~100 L/dia a 40 °C (vazão baixa, típica de chuveiro elétrico). Por isso, no cenário de referência, o sol cobre quase toda a necessidade — e tratamos esse valor como **limite superior**. Para mostrar até onde o resultado pode cair, recalculamos B com valores que têm fonte:

| Caso | Mudança | Fonte |
| --- | --- | --- |
| Coletor mínimo | PMEe 52,3 kWh/(mês·m²) | INMETRO, limite inferior da classe E |
| Ducha de maior vazão | o dobro da água quente | estudo da USP: chuveiro elétrico 4,2 L/min × aquecedor solar 8,4 L/min |
| Pessimista | os dois juntos | — |

No pessimista, o sol cobre cerca de 59% e o retorno passa de ~3 para ~4,7 anos; o consumo de água do banho dobra. Esse é o **efeito rebote**: o solar economiza energia, mas pode aumentar o uso de água se a família trocar o chuveiro por uma ducha de maior vazão.

## 7. Viabilidade e impactos ambientais

- **Viabilidade econômica**: A tem custo zero e retorno imediato. B exige ~R$ 3,4 mil (SINAPI, sem conexões/válvulas) e se paga em ~3 anos no cenário de referência e em ~4,7 anos no pessimista. Para famílias na Tarifa Social, a economia em reais é menor porque os primeiros 80 kWh já são gratuitos.
- **Viabilidade técnica**: B exige telhado com boa orientação (norte), estrutura para o reservatório, instalação por profissional (ABNT NBR 15569) e equipamentos com etiqueta INMETRO. A exige apenas mudança de hábito (e, para o ajuste fino de potência, chuveiro com controle de temperatura).
- **CO₂**: a eletricidade do SIN é majoritariamente renovável, então as emissões evitadas são pequenas (dezenas de kg CO₂/ano). Em anos de seca o fator sobe (MCTI: 0,1263 t/MWh em 2021, quase 3× o de 2025).
- **Água**: A reduz o volume do banho (≈14 m³/ano no cenário de referência); B mantém o volume se a vazão não mudar, mas pode dobrá-lo no caso de efeito rebote.
- **Materiais**: o solar térmico usa vidro, cobre/inox, alumínio e isolante; tem impacto de fabricação e descarte que não foi quantificado aqui.

## 8. Limitações

1. São estimativas para um ano típico (clima 2016–2025), não garantia de economia.
2. Conta = energia + PIS/COFINS + ICMS. Não inclui bandeiras tarifárias, iluminação pública (COSIP) nem reajustes futuros. PIS/COFINS foi estimado e varia mês a mês.
3. Água fria ≈ temperatura média do ar do mês.
4. O coletor foi modelado pelo ensaio INMETRO (fluido perto da temperatura ambiente); em operação real ele trabalha mais quente e rende menos. A perda do reservatório usa o limite máximo do INMETRO, o que compensa parte desse otimismo. A sensibilidade mostra a faixa de resultados.
5. O investimento do SINAPI é média nacional e não inclui conexões, bomba, válvulas nem eventual troca do chuveiro por modelo compatível com água pré-aquecida.
6. Na alternativa A, o ajuste fino de potência supõe chuveiro com controle de temperatura; com chuveiro de 2 posições a economia de potência pode ser menor (a parte do tempo de banho continua valendo).
7. Retorno simples, sem juros, inflação e manutenção.
8. Fator de emissão médio (inventário). Para emissões **evitadas** na margem, o MCTI publica o fator de margem de operação, que tende a ser maior; não foi usado.
9. Consumo total da casa é informado pelo usuário; o padrão de 200 kWh/mês é apenas um exemplo.
10. A IA generativa pode reescrever um número correto com o sentido errado (ex.: trocar consumo por economia). O verificador só confere se o número existe nos cálculos; por isso a ficha usa rótulos explícitos e a tabela da aba Comparação é sempre a referência.
