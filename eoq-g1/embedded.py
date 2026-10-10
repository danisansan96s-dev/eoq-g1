"""Documento autónomo para el iframe de Streamlit; sin scripts externos."""
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import urlsplit

ASSETS = Path(__file__).resolve().parent / "dist"
SCRIPT_ORDER = ("model.js", "app.js", "presentation.js")
SCRIPT_TAG = re.compile(r"<script\b(?P<attrs>[^>]*)>(?P<body>.*?)</script\s*>", re.I | re.S)


class ScriptReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.external = []
        self.bundled = []
        self.attributes = {}

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "script":
            return
        self.attributes = dict(attrs)
        if "src" in self.attributes:
            self.external.append(self.attributes["src"])
        if "data-eoq-source" in self.attributes:
            self.bundled.append(self.attributes["data-eoq-source"])


def assert_self_contained(document: str) -> None:
    """Impide mostrar una página parcialmente integrada en Streamlit."""
    references = ScriptReferences()
    references.feed(document)
    if references.external:
        raise ValueError("Quedan scripts externos sin integrar: " + str(references.external))
    order = tuple(urlsplit(reference).path for reference in references.bundled)
    if order != SCRIPT_ORDER:
        raise ValueError("Orden de scripts inválido; se requiere model.js, app.js, presentation.js.")


def build_document() -> str:
    document = (ASSETS / "index.html").read_text(encoding="utf-8")
    css = (ASSETS / "style.css").read_text(encoding="utf-8")
    document, count = re.subn(
        r'<link\s+rel="stylesheet"\s+href="style\.css(?:\?[^"\s]*)?"\s*>',
        lambda _: "<style>" + css + "</style>", document,
    )
    if count != 1:
        raise ValueError("La plantilla debe incluir exactamente una hoja style.css.")

    def inline_script(match):
        attributes = ScriptReferences()
        attributes.feed("<script" + match.group("attrs") + ">")
        source = attributes.attributes.get("src")
        if source is None:
            return match.group(0)
        reference = urlsplit(source)
        filename = reference.path
        if reference.scheme or reference.netloc or filename not in SCRIPT_ORDER:
            raise ValueError(f"Referencia JavaScript no admitida: {source}")
        if attributes.attributes.get("type", "text/javascript") not in ("text/javascript", "application/javascript"):
            raise ValueError(f"{filename} debe ejecutarse como script clásico en orden.")
        # ?v=... identifica la versión en HTML; no forma parte del archivo local.
        script = (ASSETS / filename).read_text(encoding="utf-8")
        script = re.sub(r"</script", r"<\\/script", script, flags=re.I)
        return f'<script data-eoq-source="{escape(source, quote=True)}">{script}</script>'

    document = SCRIPT_TAG.sub(inline_script, document)
    navigation = """<script>
    document.addEventListener('click', function (event) {
        const anchor = event.target.closest('a[href^="#"]');
        if (!anchor) return;
        const target = document.getElementById(anchor.getAttribute('href').slice(1));
        event.preventDefault();
        if (target) target.scrollIntoView({behavior: 'instant', block: 'start'});
    });
    </script>"""
    document = document.replace("</body>", navigation + "</body>")
    assert_self_contained(document)
    return document
