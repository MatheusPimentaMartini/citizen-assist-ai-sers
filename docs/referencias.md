# Referências

Acessos entre 16 e 17/11/2026. Entre colchetes, onde cada fonte é usada no projeto.

## Dados

1. **Open-Meteo** — Historical Weather API (reanálise). Irradiação diária `shortwave_radiation_sum` e `temperature_2m_mean`, ponto -23,515; -46,611 (737 m), 2016-01-01 a 2025-12-31. https://open-meteo.com/en/docs/historical-weather-api — script de coleta: `scripts/coletar_open_meteo.py`. [clima diário, água fria]
2. **CRESESB/CEPEL** — SunData v3.0, base do Atlas Brasileiro de Energia Solar, 2ª ed. (2017). Busca por 23,55° S; 46,63° O; estação São Paulo (23,5° S; 46,649° O; 5,9 km). https://cresesb.cepel.br/index.php?section=sundata [irradiação no plano inclinado]
3. **ANEEL** — Dados abertos: Tarifas de aplicação das distribuidoras de energia elétrica (REH nº 3.596, de 3/7/2026; ELETROPAULO/Enel SP; B1 convencional; vigência 04/07/2026 a 03/07/2027). https://dadosabertos.aneel.gov.br/dataset/tarifas-distribuidoras-energia-eletrica [tarifas]
4. **MCTI/SIRENE** — Fatores de emissão de CO₂ do SIN, fator médio para inventários (arquivo `Inventario_2026_janset.xlsx`). https://www.gov.br/mcti/pt-br/acompanhe-o-mcti/sirene/dados-e-ferramentas/fatores-de-emissao [CO₂]
5. **SINAPI** (Caixa/IBGE), composição 103517 — aquecedor solar compacto, kit com 1 coletor em vidro temperado e serpentina de cobre, reservatório inox 200 L, fornecimento e instalação; insumo 34472 (residências até 120 m², 4 a 5 banhos/dia). Consulta via Orçamentor: https://orcamentor.com/composicao/103517/ e https://orcamentor.com/insumo/34472/ [investimento]
6. **Komeco** — Datasheet dos coletores Princess Prime/linha AP: KOCS AP 2M, classe A INMETRO, 1,96 m², 178 kWh/mês, 90,9 kWh/(mês·m²), registro 001004/2024. https://www.komeco.com.br/arquivos/datasheet/aquecimento-solar/coletor-solar/datasheet-coletor-solar-linha-princess-prime.pdf [PMEe do coletor]

## Normas e legislação

7. **INMETRO** — Portaria nº 301, de 14/06/2012: RTQ para equipamentos de aquecimento solar de água (dia padrão de 17,6 MJ/m²; PMEe; classes A–E; perda específica máxima de reservatórios de 0,27 kWh/(L·mês) para 100–300 L). Cópia: https://solarthermalworld.org/sites/default/files/inmetro%20regulations%20for%20Brazil.pdf [coletor e reservatório]
8. **ABNT NBR 15569** — Sistema de aquecimento solar de água em circuito direto: requisitos de projeto e instalação. https://www.target.com.br/produtos/normas-tecnicas/40628/nbr15569-sistema-de-aquecimento-solar-de-agua-em-circuito-direto-requisitos-de-projeto-e-instalacao [perdas de 15%, instalação]
9. **Lei nº 15.235/2025** (conversão da MP 1.300/2025) — Tarifa Social: desconto de 100% até 80 kWh/mês e 0% acima. https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/l15235.htm [perfis tarifários]
10. **ICMS-SP** — isenção até 90 kWh (Lei 12.185/2006; RICMS, Anexo I, art. 29): https://legislacao.fazenda.sp.gov.br/Paginas/an1art029.aspx e https://www.al.sp.gov.br/repositorio/legislacao/lei/2006/lei-12185-05.01.2006.html · 12% até 200 kWh (Lei 6.374/1989, art. 34, citado em proposição da ALESP): https://www.al.sp.gov.br/spl/2025/07/Propositura/76316_1000764686_Propositura.pdf · 18% acima de 200 kWh após a LC 194/2022: https://teletime.com.br/27/06/2022/sao-paulo-reduz-icms-sobre-telecom-energia-e-combustiveis-para-18/ [ICMS]

## Literatura técnica

11. **ARA, P. J. S.; SOWMY, D. S.** Análise da utilização da razão entre a demanda de energia térmica e a produção mensal específica de energia do coletor como prática de dimensionamento da área coletora de sistemas de aquecimento solar de água. VI CBENS, 2016. https://anaiscbens.emnuvens.com.br/cbens/article/download/1924/1910 [método NBR 15569, perdas]
12. **VAZ, I. C. M. et al.** Artigo do ENCAC (ANTAC) sobre o consumo de eletricidade de chuveiros elétricos no estado de São Paulo, com banho diário de 8 min e cenários de clima futuro. https://eventos.antac.org.br/index.php/encac/article/download/7083/5799/33783 [8 min, 40 °C, água fria ≈ ar]
13. **VAZ, I. C. M.; SANTOS, V. C.; GIGLIO, T. G. F.; GHISI, E.** Aquecimento solar de água em edificações residenciais brasileiras. ENTAC, 2024. https://eventos.antac.org.br/index.php/entac/article/download/5728/4792/21959 [40 °C em SP, 4 habitantes, 40 L/hab/dia de água quente]
14. **Idec** — Chuveiro elétrico: consumo pela etiqueta INMETRO (4.500 W → 72 kWh/mês; 5.500 W → 88 kWh/mês), eficiência acima de 95%, estudo da USP sobre vazões. https://idec.org.br/print/24493 [eficiência, validação de L0]
15. **USP / ABINEE** — Material DuchaFlex (e-Disciplinas USP) citando estudo da USP: chuveiro elétrico 4,2 L/min; aquecedor solar 8,4 L/min. https://edisciplinas.usp.br/pluginfile.php/5515219/mod_resource/content/0/DuchaFlex.pdf [efeito rebote]
16. **MCTI** — Nota técnica de junho/2025 sobre a ampliação da base de usinas no cálculo dos fatores de emissão (cópia): https://cenarioenergia.com.br/wp-content/uploads/2025/06/NT_FE_jun25.pdf [contexto do fator de 2025]

## Contexto e comportamento

17. **Sabesp** — recomendação de banhos de até 5 minutos, conforme reportagens: DGABC (07/04/2026) https://www.dgabc.com.br/Noticia/4293516/confira-cinco-dicas-da-sabesp-para-economizar-na-conta-de-agua e Gazeta SP https://www.gazetasp.com.br/estilo-de-vida/conta-de-agua-mais-barata-veja-como-ter-esse-beneficio-em-5-passos/ [alternativa A]
18. **ANEEL** aprova reajuste da Enel SP (efeito médio 10,18%, a partir de 04/07/2026) — Cenário Energia: https://cenarioenergia.com.br/2026/06/30/aneel-aprova-reajuste-da-enel-sao-paulo-com-efeito-medio-de-1018/ [contexto tarifário]
19. **Faturas públicas da Enel SP (2026)** usadas para estimar PIS/COFINS — portais de transparência: Câmara dos Deputados (cota parlamentar) https://www.camara.leg.br/cota-parlamentar/documentos/publ/1699/2026/8059766.pdf, https://www.camara.leg.br/cota-parlamentar/documentos/publ/993/2026/8067819.pdf, https://www.camara.leg.br/cota-parlamentar/documentos/publ/993/2026/8067830.pdf, https://www.camara.leg.br/cota-parlamentar/documentos/publ/3283/2026/8055087.pdf, https://www.camara.leg.br/cota-parlamentar/documentos/publ/1963/2026/8117935.pdf; Senado (CEAPS) https://www6g.senado.leg.br/transparencia/sen/download/ceaps/documento/282651 [PIS/COFINS]

## Ferramentas

20. **Ollama** — Cloud API (`POST https://ollama.com/api/chat`, autenticação `Authorization: Bearer`). https://docs.ollama.com/cloud [assistente com IA generativa]
21. **Streamlit Community Cloud** — hospedagem gratuita e gerenciamento de segredos (Secrets). https://docs.streamlit.io/deploy/streamlit-community-cloud [publicação do app]
