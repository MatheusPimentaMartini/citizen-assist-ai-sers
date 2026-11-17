# Procedência dos dados

Coleta feita pela equipe em 16 e 17/11/2026. Nenhum dado é baixado quando o app roda: tudo está nesta pasta.

| Arquivo | Conteúdo | Origem e como foi obtido | Período | Unidade |
| --- | --- | --- | --- | --- |
| `open_meteo_irradiacao_diaria_sp_2016_2025.csv` | Irradiação solar global diária no plano horizontal | Open-Meteo Historical Weather API, `daily=shortwave_radiation_sum`, lat -23,55, lon -46,63 (ponto da grade -23,515; -46,611; 737 m), fuso America/Sao_Paulo. Convertido de MJ/m² para kWh/m² (÷ 3,6), 2 casas decimais. Reprodutível com `scripts/coletar_open_meteo.py`. | 01/01/2016 a 31/12/2025 (3.653 dias, sem falhas) | kWh/(m²·dia) |
| `open_meteo_mensal_sp_2016_2025.csv` | Médias mensais de irradiação horizontal e temperatura média do ar | Mesma API (`temperature_2m_mean`), médias por ano-mês. As médias de irradiação foram calculadas em uma primeira coleta e conferidas com a série diária (diferença ≤ 0,006). | 2016–2025 | kWh/(m²·dia); °C |
| `cresesb_sundata_sao_paulo.csv` | Irradiação média mensal no plano horizontal e em 3 inclinações | CRESESB SunData v3.0 (Atlas Brasileiro de Energia Solar, 2ª ed., 2017), busca por 23,55° S; 46,63° O; estação mais próxima: São Paulo (23,5° S; 46,649° O; 5,9 km). | média de longo prazo do Atlas | kWh/(m²·dia) |
| `aneel_tarifas_enel_sp_b1_2026.csv` | TUSD e TE da Enel SP (sigla ANEEL: ELETROPAULO), B1 convencional | ANEEL, dados abertos "Tarifas de aplicação das distribuidoras" (API CKAN, recurso `fcf2906c-7c32-4b9b-a637-054e7a5234f4`, filtro CNPJ 61695227000193, subgrupo B1). REH nº 3.596/2026. | vigência 04/07/2026 a 03/07/2027 | R$/MWh (sem tributos) |
| `mcti_fator_emissao_sin.csv` | Fator médio mensal de emissão de CO₂ do SIN (inventários) | MCTI/SIRENE, arquivo `Inventario_2026_janset.xlsx` da página de fatores de emissão. | jan/2025 a set/2026 | tCO₂/MWh (= kg/kWh) |
| `mcti_fator_emissao_sin_anual.csv` | Fator médio anual | Mesmo arquivo do MCTI. | 2021–2025 | tCO₂/MWh |
| `parametros.json` | Parâmetros do modelo, cada um com tipo e fonte | INMETRO, Idec, Komeco, SINAPI, legislação (Lei 15.235/2025; ICMS-SP), literatura (ENCAC/ENTAC, CBENS) e premissas do grupo. | — | indicada em cada campo |

**Tipos usados em `parametros.json`:** *oficial* (órgão público/regulador), *literatura* (norma, artigo, fabricante, entidade), *estimativa* (calculado pelo grupo a partir de dados públicos — ex.: PIS/COFINS de 6%) e *premissa* (escolha do grupo para o cenário de referência — ex.: família de 4 pessoas).

Links completos: [`../docs/referencias.md`](../docs/referencias.md).
