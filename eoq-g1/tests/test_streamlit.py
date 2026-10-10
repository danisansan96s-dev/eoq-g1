"""Pruebas Python de empaquetado y arranque; sin Node.js ni rutas externas."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from embedded import build_document
from streamlit.testing.v1 import AppTest


class StreamlitTests(unittest.TestCase):
    def test_document_is_self_contained(self):
        html = build_document()
        self.assertNotIn('<script src=', html)
        self.assertNotIn('href="style.css"', html)
        self.assertIn('root.EOQ=', html)
        self.assertIn('function render()', html)
        self.assertIn('scrollIntoView', html)
        self.assertIn('Descargar escenario', html)
        self.assertIn('Preguntas de gerencia', html)
        self.assertNotIn('Guion ejecutivo', html)
        self.assertNotIn('/Users/', html)
        self.assertNotIn('node_modules', html)

    def test_app_starts(self):
        app = AppTest.from_file(str(ROOT / 'app.py')).run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.error), 0)
        self.assertEqual(len(app.get('bidi_component')), 1)


if __name__ == '__main__':
    unittest.main()
