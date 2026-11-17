# Resultados

> Gerado automaticamente por `python scripts/gerar_resultados.py` a partir de `dados/`. Valores são **estimativas** para um ano típico (clima 2016-2025), não garantias.

## 1. Cenário de referência

Família de 4 pessoas, banho de 8 min, chuveiro de 5.500 W, conta de 200 kWh/mês, tarifa residencial convencional da Enel SP. O chuveiro representa 89,3 kWh/mês (45% do consumo) e a parcela de energia da conta é R$ 199,07/mês. Vazão estimada: 3,13 L/min.

| Alternativa | Chuveiro (kWh/ano) | Redução | Conta de energia (R$/mês) | Economia (R$/ano) | Investimento | Retorno simples | CO₂ (kg/ano) | Água (m³/ano) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L0 · Chuveiro elétrico convencional (situação atual) | 1.072 | 0,0% | R$ 199,07 | R$ 0,00 | R$ 0,00 | - | 49,5 | 36,6 |
| A · Chuveiro elétrico com práticas de uso eficiente | 572 | 46,6% | R$ 151,17 | R$ 574,84 | R$ 0,00 | - | 26,9 | 22,9 |
| B · Aquecimento solar térmico + chuveiro como complemento | 1 | 99,9% | R$ 105,74 | R$ 1.119,89 | R$ 3.359,57 | 3,0 anos | 0,1 | 36,6 |

**Recomendações geradas pelo código:**

- Comece pelas práticas eficientes (A): custo zero, economia estimada de R$ 574,84 por ano (499 kWh/ano) e 13,7 mil litros de água a menos por ano.
- O aquecimento solar (B) reduz até 100% do consumo do chuveiro (economia estimada de R$ 1.119,89/ano), mas exige cerca de R$ 3.360. Retorno simples estimado: 3,0 anos (sem juros e sem reajustes de tarifa). No cenário pessimista (coletor de pior desempenho aceito e ducha com o dobro da vazão) a economia cai para R$ 714,93/ano e o retorno vai para 4,7 anos.
- O chuveiro solar precisa mais do complemento elétrico em junho (o sol cobre 99% da necessidade nesse mês, em média) e em sequências de dias nublados (cerca de 2 dias por ano).
- Se optar pelo solar, escolha coletor e reservatório com etiqueta INMETRO e instalação por profissional seguindo a ABNT NBR 15569. As práticas de A continuam valendo junto com o solar.

## 2. Mês a mês (cenário de referência)

| Mês | Água fria (°C) | Sol no coletor (kWh/m²·dia) | L0 (kWh) | A (kWh) | B (kWh) | Sol cobre (B) | Fator CO₂ 2025 (kg/kWh) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| janeiro | 22,2 | 4,37 | 90,9 | 42,3 | 0,0 | 100,0% | 0,0237 |
| fevereiro | 22,1 | 4,93 | 83,0 | 38,8 | 0,0 | 100,0% | 0,0248 |
| março | 21,7 | 4,71 | 90,9 | 43,6 | 0,0 | 100,0% | 0,0215 |
| abril | 19,8 | 4,75 | 88,0 | 46,4 | 0,0 | 100,0% | 0,0289 |
| maio | 17,8 | 4,41 | 90,9 | 52,7 | 0,0 | 100,0% | 0,0309 |
| junho | 16,6 | 4,37 | 88,0 | 53,2 | 0,6 | 99,3% | 0,0455 |
| julho | 16,1 | 4,33 | 90,9 | 55,9 | 0,1 | 99,9% | 0,0603 |
| agosto | 16,8 | 5,13 | 90,9 | 54,9 | 0,6 | 99,4% | 0,0667 |
| setembro | 19,4 | 4,45 | 88,0 | 47,4 | 0,0 | 100,0% | 0,0563 |
| outubro | 19,8 | 4,43 | 90,9 | 48,0 | 0,0 | 100,0% | 0,0680 |
| novembro | 20,0 | 4,38 | 88,0 | 46,0 | 0,0 | 100,0% | 0,0778 |
| dezembro | 21,7 | 4,63 | 90,9 | 43,3 | 0,0 | 100,0% | 0,0486 |

## 3. Sensibilidade da alternativa B

O cenário de referência é um **limite superior** (coletor classe A, mesma vazão do chuveiro elétrico). Os demais casos usam valores com fonte para mostrar até onde o resultado pode cair.

| Cenário | Sol cobre | Dias com complemento/ano | Economia (R$/ano) | Retorno simples | Água (m³/ano) | Fonte da variação |
| --- | --- | --- | --- | --- | --- | --- |
| Referência: coletor classe A (Komeco KOCS AP 2M) e mesma vazão do chuveiro elétrico | 99,9% | 2 | R$ 1.119,89 | 3,0 anos | 36,6 | Parâmetros de referência (dados/parametros.json). |
| Coletor com o pior desempenho aceito pelo INMETRO (PMEe 52,3 kWh/mês·m²) | 95,6% | 52 | R$ 1.079,86 | 3,1 anos | 36,6 | INMETRO, Portaria 301/2012 (limite inferior da classe E). |
| Família passa a usar ducha de maior vazão com o solar (o dobro da água quente) | 91,0% | 112 | R$ 1.034,67 | 3,2 anos | 73,2 | Estudo da USP citado pela ABINEE e pelo Idec: chuveiro elétrico 4,2 L/min; aquecedor solar 8,4 L/min. |
| Combinação pessimista: coletor de pior desempenho aceito + ducha com o dobro da vazão | 59,3% | 359 | R$ 714,93 | 4,7 anos | 73,2 | Combinação dos dois casos acima. |

## 4. Efeito da tarifa e do consumo total da casa (mesma família)

A economia em reais depende do consumo total (faixas de ICMS de SP) e do perfil tarifário. Na Tarifa Social os primeiros 80 kWh já são gratuitos, então a mesma economia em kWh vale menos em reais.

| Perfil | Conta (kWh/mês) | Conta hoje (R$/mês) | Economia A (R$/ano) | Economia B (R$/ano) | Retorno B |
| --- | --- | --- | --- | --- | --- |
| convencional | 150 | R$ 143,14 | R$ 476,28 | R$ 1.104,90 | 3,0 anos |
| convencional | 200 | R$ 199,07 | R$ 574,84 | R$ 1.119,89 | 3,0 anos |
| convencional | 250 | R$ 256,03 | R$ 525,06 | R$ 1.230,81 | 2,7 anos |
| convencional | 300 | R$ 307,23 | R$ 511,13 | R$ 1.096,07 | 3,1 anos |
| desconto social | 150 | R$ 120,55 | R$ 450,10 | R$ 954,71 | 3,5 anos |
| tarifa social | 150 | R$ 52,73 | R$ 375,95 | R$ 632,73 | 5,3 anos |

## 5. Variação: chuveiro de 7.500 W (220 V), conta de 250 kWh/mês

| Alternativa | Chuveiro (kWh/ano) | Redução | Conta de energia (R$/mês) | Economia (R$/ano) | Investimento | Retorno simples | CO₂ (kg/ano) | Água (m³/ano) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L0 · Chuveiro elétrico convencional (situação atual) | 1.461 | 0,0% | R$ 256,03 | R$ 0,00 | R$ 0,00 | - | 67,5 | 49,9 |
| A · Chuveiro elétrico com práticas de uso eficiente | 781 | 46,6% | R$ 189,15 | R$ 802,50 | R$ 0,00 | - | 36,7 | 31,2 |
| B · Aquecimento solar térmico + chuveiro como complemento | 14 | 99,0% | R$ 123,50 | R$ 1.590,33 | R$ 3.359,57 | 2,1 anos | 0,7 | 49,9 |

## 6. Alternativa B ano a ano (cenário de referência)

| Ano | Sol cobre | Dias com complemento | Chuveiro com solar (kWh/ano) |
| --- | --- | --- | --- |
| 2016 | 99,4% | 3 | 5,1 |
| 2017 | 99,5% | 7 | 4,6 |
| 2018 | 99,8% | 2 | 1,4 |
| 2019 | 100,0% | 0 | 0,0 |
| 2020 | 100,0% | 1 | 0,1 |
| 2021 | 100,0% | 0 | 0,0 |
| 2022 | 100,0% | 0 | 0,0 |
| 2023 | 99,9% | 2 | 0,9 |
| 2024 | 100,0% | 0 | 0,0 |
| 2025 | 99,9% | 1 | 0,7 |
