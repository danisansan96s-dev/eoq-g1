"""Carga la interfaz existente como un documento autónomo para Streamlit."""
from pathlib import Path
import re

ASSETS = Path(__file__).resolve().parent / "dist"


def build_document() -> str:
    """Incorpora CSS y JS: el iframe no solicita archivos relativos al servidor."""
    document = (ASSETS / "index.html").read_text(encoding="utf-8")
    css = (ASSETS / "style.css").read_text(encoding="utf-8")
    document, count = re.subn(
        r'<link\s+rel="stylesheet"\s+href="style\.css"\s*>',
        lambda _: "<style>" + css + "</style>",
        document,
    )
    if count != 1:
        raise ValueError("La plantilla debe incluir exactamente una hoja style.css.")
    for filename in ("model.js", "app.js", "presentation.js"):
        script = (ASSETS / filename).read_text(encoding="utf-8")
        script = re.sub(r"</script", r"<\\/script", script, flags=re.IGNORECASE)
        document, count = re.subn(
            rf'<script\s+src="{re.escape(filename)}(?:\?[^"\s]*)?"\s*></script>',
            lambda _: "<script>" + script + "</script>",
            document,
        )
        if count != 1:
            raise ValueError(f"La plantilla debe incluir exactamente una vez {filename}.")
    # En srcdoc, los enlaces relativos heredan la URL de Streamlit. Interceptar
    # anclas evita cargar Streamlit dentro de su propio iframe.
    navigation = """<script>
    document.addEventListener('click', function (event) {
        const anchor = event.target.closest('a[href^="#"]');
        if (!anchor) return;
        const target = document.getElementById(anchor.getAttribute('href').slice(1));
        event.preventDefault();
        if (target) target.scrollIntoView({behavior: 'instant', block: 'start'});
    });
    </script>"""
    return document.replace("</body>", navigation + "</body>")
