# Validación para Streamlit Community Cloud

Entorno verificado: Python 3.11, Streamlit 1.64.0 y Chromium, el 9 de octubre de 2026 (America/Bogota).

## Resultados

- **41 controles del modelo JavaScript real:** G1, las tres variaciones, capacidad local con demanda 21.000, frontera 75/76 posiciones, alquiler más barato, ceros permitidos, datos inválidos, empate, falta de alternativas factibles, puntos de equilibrio y eventos de reposición.
- **2 pruebas Python:** empaquetado autónomo del HTML/CSS/JS y arranque real mediante Streamlit AppTest sin errores.
- **54 comprobaciones en un navegador real dentro de Streamlit:** las 11 secciones, seis SVG, navegación dentro del iframe, cambio de demanda a 12.000 y actualización de curvas/marcadores, selectores de capacidad y sensibilidad, las tres variaciones independientes, demanda 21.000, invalidación de entradas vacías, restauración, invocación del botón de impresión, ancho móvil y descargas en computador y móvil. Sin errores JavaScript.
- **Descarga JSON real:** se abrió y verificó el archivo descargado, incluidos demanda 12.000, frecuencia de pedidos y CTA calculado. En móvil se verificó demanda base 9.000.
- **Inspección visual:** captura de la interfaz en Streamlit revisada; se corrigió el solapamiento del encabezado de Streamlit con el menú en pantallas pequeñas.
- **Portabilidad:** los recursos se resuelven desde el archivo Python; el servidor no invoca Node.js ni archivos de MotoTrak. El paquete de publicación excluye cachés, entorno virtual, credenciales, metadatos de Sites y pruebas exclusivas de macOS.

## Cálculos independientes

Python, usando fórmulas escalares independientes del modelo JS:

- CTA 20 pies con ampliación: 967.046.684,210526 COP.
- CTA local: 979.042.826,434266 COP.
- Financiación mínima: 46,6580938305%.

El precio local máximo competitivo calculado es 101.678,5666997 COP/unidad; al recalcular el EOQ local y su bodega, su CTA iguala el de importación (tolerancia inferior a un centavo).

La carpeta final de publicación se inició y probó nuevamente: 54 comprobaciones de navegador superadas, dos pruebas Python superadas y servidor iniciado con Node.js fuera del PATH.

## Límites de esta entrega

El despliegue remoto en Streamlit Community Cloud no se ejecutó: se entrega una carpeta lista para un nuevo repositorio GitHub. Las pruebas de impresión comprueban el botón y su invocación; no automatizan el diálogo de impresión del sistema. Los escenarios permanecen en el navegador hasta recargar. Los documentos Word y Excel EOQ no fueron adjuntados.
