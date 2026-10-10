# EOQ G1 · EAFIT — Streamlit Community Cloud

Herramienta independiente de apoyo a la decisión EOQ. Conserva el diseño y los cálculos HTML/JavaScript, la demanda editable, los gráficos y las tres variaciones de gerencia. Los archivos del pronosticador MotoTrak no forman parte de este proyecto.

## Publicar desde un nuevo repositorio GitHub

1. Cree un repositorio llamado **eoq-g1**.
2. Suba el contenido de esta carpeta a la raíz del repositorio. `app.py`, `embedded.py`, `requirements.txt`, `dist/` y `.streamlit/config.toml` deben conservar esta estructura; no suba la carpeta contenedora como un nivel extra.
3. En Streamlit Community Cloud elija **Create app** y conecte el repositorio.
4. Seleccione repositorio **eoq-g1**, rama **main** y archivo principal **app.py**.
5. En opciones avanzadas seleccione **Python 3.11**, versión usada en la verificación, y despliegue.

No requiere Node.js, npm, paquetes del sistema, secretos, Excel, Word ni rutas del Mac para iniciar. La única dependencia directa del servidor es Streamlit 1.64.0. Los costos y gráficos se calculan en el navegador.

Documentación oficial: [despliegue en Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app) y [componentes v2](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component).

## Ejecutar en un equipo con Python

Desde esta carpeta:

```sh
python -m venv .venv
```

Active el entorno con `source .venv/bin/activate` en macOS/Linux o `.venv\Scripts\activate` en Windows. Después:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

También puede abrir `dist/index.html` directamente en un navegador para usar la versión estática.

## Estructura

```text
eoq-g1/
├── app.py                 # Archivo de entrada para Streamlit
├── embedded.py            # Documento HTML autónomo con CSS y JS incorporados
├── requirements.txt
├── .streamlit/config.toml
├── .gitignore
├── dist/
│   ├── index.html
│   ├── style.css
│   ├── model.js
│   └── app.js
├── tests/
├── README.md
└── VALIDACION.md
```

La integración usa un componente v2 de Streamlit con un iframe de altura adaptable. Los recursos se leen respecto al archivo Python, nunca respecto al directorio de inicio del servidor. `embedded.py` incorpora los archivos y adapta la navegación por anclas. El iframe permite ejecutar el modelo, descargar JSON e imprimir el informe; el documento mantiene su menú fijo y su propio desplazamiento.

Los escenarios no se envían al servidor ni persisten tras recargar. Descargue el JSON antes de cerrar si necesita conservar el resultado. El botón de descarga incluye los parámetros y cálculos del escenario activo. Para un informe PDF use **Imprimir informe** y la opción PDF del navegador.

## Uso por etapas

1. **Resumen:** G1 recomienda importar 20 pies con ampliación. CTA $967.046.684,21; ahorro frente al local $11.996.142,22. La ampliación aporta 90 posiciones: 165 disponibles, 76 necesarias.
2. **Datos:** cambie los campos numéricos. Seleccione suma de componentes o tasa directa. Entradas vacías o inválidas suspenden los resultados. Restaurar base G1 recupera todos los originales.
3. **EOQ:** A20 = $12.830.000, A40 = $15.600.000, ALocal = $631.000 y r = 22%. Los EOQ son 3.289,6703; 3.627,4492 y 707,9800 unidades.
4. **Robustez:** evalúe la diferencia de cantidad y la penalización TRC de los contenedores completos. TRC sirve para analizar Q; CTA sirve para seleccionar fuente.
5. **Capacidad:** 20 pies requiere 76 posiciones; 40 pies, 168. Este último no cabe en 165 y se excluye aunque su costo informativo sea menor. Cada alquiler/ampliación se cobra completo y por separado.
6. **Molde y comparación:** el local asume $36.000.000 anuales en G1. CTA local $979.042.826,43. Las tablas explican pedidos, ciclo, inventarios y componentes del costo.
7. **Gráficas:** cambie la bodega del diente de sierra; consulte valores pasando el cursor. Las reposiciones usan eventos exactos. Los límites físicos redondean posiciones; el gráfico usa posiciones equivalentes.
8. **Sensibilidad:** seleccione una variable. Cada fila modifica solo esa variable desde el escenario activo. Demanda, tasa, precio y capacidad financiera se recalculan. No confunda esta comparación con la robustez del EOQ.
9. **Equilibrios:** precio local máximo $101.678,5667 y financiación mínima 46,658094%. Se recalculan EOQ y bodega al variar precio. Un local con capacidad anual insuficiente no recibe umbral viable.
10. **Gerencia:** cada botón parte de G1. Las tres variaciones recomiendan local: precio $99.000 (CTA $942.728.230,67); flete 20 pies $10.000.000 (local CTA $979.042.826,43); financiación 50% (CTA $965.542.826,43). La tabla presenta cambios contra base.
11. Descargue el escenario JSON o imprima el informe. Los cambios viven en la sesión y no persisten tras recargar.

## Verificación y supuestos pendientes

- Fuente disponible: texto proporcionado por el usuario. No se adjuntaron Taller_EOQ.docx ni los dos libros EOQ; no fue posible contrastarlos. Se conservaron los datos originales como objeto congelado.
- Se interpreta que el molde aplica exclusivamente al proveedor local, interpretación que reproduce los controles económicos entregados.
- Cada política emplea la configuración factible de menor costo. Si no requiere capacidad adicional, actual tiene costo incremental cero. Empates en CTA se reconocen con tolerancia de un centavo; no se redondean cálculos.
- Si todos los componentes de ordenar local son cero, el EOQ positivo no tiene mínimo alcanzable (su límite es Q→0). La aplicación explica el caso y suspende la recomendación en lugar de inventar un lote.
- Para legibilidad, el diente de sierra limita 10.000 ciclos en demandas extremas; el modelo de costos sigue siendo exacto. La sensibilidad usa 21 escenarios individuales; el precio de equilibrio usa bisección y recalcula bodega en cada paso.
- No se calcula utilidad, amortización adicional, stock de seguridad, lead time ni faltantes.

## Verificación

```sh
python -m unittest discover -s tests -p "test_streamlit.py" -v
```

Estas pruebas comprueban que el documento es autónomo y que Streamlit inicia sin errores. Las pruebas opcionales JavaScript del modelo y de navegador requieren Node.js solo en el equipo de pruebas, no en el servidor ni en Community Cloud:

```sh
node tests/run-node.cjs
npm install --prefix /tmp/eoq-qa playwright
npx --prefix /tmp/eoq-qa playwright install chromium
EOQ_PLAYWRIGHT=/tmp/eoq-qa/node_modules/playwright node tests/browser.test.cjs
```

Para la prueba de navegador, inicie antes `streamlit run app.py --server.port 8511`; la URL de pruebas por defecto es `http://127.0.0.1:8511`. Puede cambiarla con `EOQ_TEST_URL`. `VALIDACION.md` resume los resultados reales.

La carpeta está lista para subir a GitHub. No se creó el repositorio ni se desplegó en Community Cloud en esta sesión.
