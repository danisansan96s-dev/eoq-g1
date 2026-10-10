"""Entrada de Streamlit Community Cloud. Ejecutar: streamlit run app.py."""
import streamlit as st
from streamlit.components.v2 import component

from embedded import build_document

st.set_page_config(
    page_title="EOQ G1 · EAFIT",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# El documento conserva sus propios estilos; este ajuste solo aprovecha el
# ancho disponible en Streamlit, sin acceder al DOM del padre desde el iframe.
st.html("""<style>
    .stMainBlockContainer {max-width: none; padding: 4.5rem 1rem 0;}
</style>""")


@st.cache_resource
def eoq_component():
    return component(
        "eoq_g1_document",
        html='<iframe title="Herramienta EOQ G1" allow="fullscreen" allowfullscreen '
             'sandbox="allow-scripts allow-same-origin allow-downloads allow-modals allow-forms" '
             'style="display:block;width:100%;height:780px;border:0;border-radius:12px;" '
             '></iframe>',
        js="""
        export default function ({ parentElement, data }) {
            const frame = parentElement.querySelector('iframe');
            if (frame._eoqDocument !== data.document) {
                frame._eoqDocument = data.document;
                frame.srcdoc = data.document;
            }
            const resize = () => {
                frame.style.height = Math.max(540, window.innerHeight - 110) + 'px';
            };
            resize();
            window.addEventListener('resize', resize);
            return () => window.removeEventListener('resize', resize);
        }
        """,
    )


try:
    document = build_document()
except (OSError, ValueError) as error:
    st.error(f"No se pudo cargar la herramienta: {error}")
    st.stop()

eoq_component()(key="eoq-g1", data={"document": document}, height="content")

