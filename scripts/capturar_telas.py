"""Captura telas do app (celular e computador) para conferir o layout e ilustrar a documentação.

Uso (opcional; precisa do app rodando e do Playwright):
    pip install playwright && playwright install chromium
    streamlit run app.py --server.port 8599
    python scripts/capturar_telas.py --url http://localhost:8599 --saida docs/img

O script faz o caminho de uma pessoa: abre o app, calcula com os valores de exemplo, abre o assistente,
toca numa pergunta sugerida e abre as fontes. Também confere três itens de usabilidade e imprime o resultado:
  - não existe rolagem horizontal (nada "vaza" da tela);
  - os botões têm pelo menos 44 px de altura (alvo de toque);
  - não houve erro de JavaScript na página.
Sem chave de IA configurada, o assistente responde no modo cálculo (o que aparece nas capturas).
"""
from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

TELAS = {"celular": (390, 844, True), "computador": (1280, 900, False)}


def esperar(page, ms: int = 1500) -> None:
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=60000)
    page.wait_for_function("() => !document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=60000)
    page.wait_for_timeout(ms)


def conferir(page) -> dict:
    return page.evaluate("""() => ({
        rolagem_horizontal: document.documentElement.scrollWidth > window.innerWidth,
        botoes_menores_que_44px: [...document.querySelectorAll('button')]
            .filter(b => b.offsetParent && b.innerText.trim() && b.getBoundingClientRect().height < 44)
            .map(b => b.innerText.trim().slice(0, 40)),
    })""")


def capturar(url: str, saida: Path, nome: str, executavel: str | None) -> None:
    largura, altura, movel = TELAS[nome]
    with sync_playwright() as p:
        navegador = p.chromium.launch(executable_path=executavel, args=["--no-sandbox"]) if executavel \
            else p.chromium.launch()
        page = navegador.new_context(viewport={"width": largura, "height": altura}, is_mobile=movel,
                                     has_touch=movel, locale="pt-BR").new_page()
        erros: list[str] = []
        page.on("pageerror", lambda e: erros.append(str(e)))
        page.goto(url)
        esperar(page)
        page.screenshot(path=str(saida / f"{nome}_1_inicio.png"))
        print(nome, "início:", conferir(page))

        page.get_by_role("button", name="Calcular minha economia").click()
        esperar(page, 2500)  # o app rola sozinho até o resultado
        page.screenshot(path=str(saida / f"{nome}_2_resultado.png"))
        page.get_by_text("Compare as opções").evaluate("e => e.scrollIntoView({block: 'start'})")
        page.wait_for_timeout(600)
        page.screenshot(path=str(saida / f"{nome}_3_cartoes.png"))
        print(nome, "resultado:", conferir(page))

        page.get_by_role("button", name="Tirar dúvidas com o assistente").click()
        esperar(page)
        page.screenshot(path=str(saida / f"{nome}_4_assistente.png"))
        page.get_by_role("radio", name="Quanto o chuveiro pesa na minha conta?").click()
        esperar(page, 2500)
        page.screenshot(path=str(saida / f"{nome}_5_resposta.png"))
        print(nome, "assistente:", conferir(page))

        page.get_by_role("radio", name="Fontes").click()
        esperar(page)
        page.screenshot(path=str(saida / f"{nome}_6_fontes.png"))
        print(nome, "fontes:", conferir(page), "| erros de JavaScript:", erros or "nenhum")
        navegador.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8599")
    ap.add_argument("--saida", default="docs/img")
    ap.add_argument("--chrome", default=None, help="caminho de um Chrome já instalado (opcional)")
    args = ap.parse_args()
    pasta = Path(args.saida)
    pasta.mkdir(parents=True, exist_ok=True)
    for tela in TELAS:
        capturar(args.url, pasta, tela, args.chrome)
