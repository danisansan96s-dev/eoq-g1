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

## Modo exposición

- Seis pantallas vinculadas al mismo escenario y modelo del análisis completo. No se duplicaron fórmulas EOQ ni se fijaron resultados.
- **134 comprobaciones en Streamlit + Chromium** y **134 en HTML local + Chromium**, sin errores JavaScript.
- Navegación Anterior/Siguiente, seis accesos numerados y flechas de teclado; las flechas no cambian de pantalla al editar demanda.
- Demanda se aplica explícitamente; se verificaron cambios a 12.000, 15.000 y 21.000, actualización de EOQ, indicadores, curvas, posiciones, umbrales y conclusiones, y conservación de la pantalla activa.
- Se verificaron las tres variaciones independientes, restauración de G1 y actualización al modificar parámetros desde Análisis completo.
- Pantalla completa real: entrada, navegación y salida.
- Las seis pantallas caben sin desplazamiento ni solapamientos en portátiles 1280×720, 1366×768 y 1440×900, tanto en Streamlit como en HTML local. Capturas revisadas.
- Adaptación móvil de 390×844 sin desbordamiento horizontal de la página: bloques apilados y tablas/gráficas anchas con desplazamiento propio.
- El análisis completo conserva sus **54 comprobaciones de navegador**, incluidas descargas, además de **41 controles del modelo** y **2 pruebas Python de empaquetado y arranque**.
- El componente Streamlit incorpora el nuevo recurso presentation.js y permite formularios y pantalla completa. No se añadieron dependencias de servidor.

## Corrección del wrapper

5 pruebas Python superadas: documento autónomo, arranque Streamlit, orden de scripts y referencias con versión, atributos alternativos/comillas y rechazo de integración incompleta.

138 comprobaciones de navegador sobre el servidor iniciado desde publicacion/eoq-g1: apertura de Modo exposición, seis pantallas, demanda editable y gráficas actualizadas, regreso a Análisis completo, pantalla completa y adaptación de tamaños. No hubo errores JavaScript ni mensajes de error en consola. El iframe contiene cero scripts con src y los tres scripts incorporados en orden, con sus versiones. No se solicitó presentation.js a una ruta externa.

La aplicación pública no se modificó en esta sesión; la corrección se entrega para reemplazar app.py y embedded.py en GitHub.

## Simulador de escenarios EOQ · 11 de octubre de 2026

- 11 pruebas Python superadas en el proyecto y en la copia de publicación: las 5 del wrapper existente y 6 del simulador. Comprueban resultados G1 y las tres variaciones independientes, separación del flete, EOQ, capacidad, demanda y precio editables, cierre exacto del horizonte, contenedores completos, último pedido local parcial, validación y restauración de sesión.
- Paridad del criterio anual equivalente con `dist/model.js`: 84 combinaciones de demanda (100 a 21.000), precio local y aporte al molde; 2.772 comprobaciones de lotes, EOQ, componentes económicos, costo total, inventario, periodo y factibilidad superadas. Tolerancia monetaria: 0,01 COP. Los valores originales se leen del archivo, sin mantener otra copia fija de sus datos.
- 41 controles del motor JavaScript original superados.
- Regresión en Streamlit/Chromium: 54 comprobaciones del análisis original y 138 de sus seis pantallas de exposición superadas. Cero errores de JavaScript o consola; el wrapper sigue incorporando los tres scripts y sus versiones.
- 23 comprobaciones del simulador ejecutadas contra el servidor iniciado con `publicacion/eoq-g1/app.py`: tres curvas como máximo, eventos hasta el mes 12, demanda editable, EOQ local y barras recalculadas, aislamiento entre escenarios, leyenda que oculta curvas, los cuatro selectores, PNG válido descargado, CSV de doce filas, costos del año observado con pedidos enteros, modo exposición, restauración G1 y regreso al análisis original conservando su demanda de 11.000. Cero errores de JavaScript o consola.
- Captura de escritorio revisada: los indicadores monetarios muestran millones de COP sin recortarse. Los importes completos se conservan en las ayudas, conclusión, tabla y CSV. Colores iguales al análisis original: verde 20 pies, azul 40 pies, naranja local.
- El costo del año observado incluye las existencias recibidas que quedan al cierre. Se diferencia del criterio anual equivalente; no se mezclan sus costos al recomendar. El molde conserva el equivalente anual y el aporte contractual originales: no se calculan intereses sin condiciones financieras.
- Se añadió Plotly 7.1.0; Streamlit conserva la versión 1.64.0. Node/Playwright solo se utilizaron temporalmente para pruebas. El servidor no requiere Node.js ni rutas del equipo local.

No se modificó la aplicación pública ni se subieron archivos a GitHub en esta sesión.

## Ajustes de interpretación y exposición · 11 de octubre de 2026

- Datos originales, funciones `original_values`, `evaluate` y `sawtooth` intactos: comparación de sus árboles sintácticos con la versión previamente validada. No se editaron los recursos de `dist`, el wrapper, la entrada ni las dependencias.
- 13 pruebas Python superadas. Se añadieron verificaciones de los tres estados operativos, recomendaciones separadas, capacidad modificada, límite anual local, ahorro absoluto/porcentual positivo, negativo y cero, conclusiones dinámicas y representación de alternativas inviables.
- 37 comprobaciones del simulador en Streamlit/Chromium superadas, sin errores de JavaScript ni de consola. Incluyen las cuatro demandas de prueba 6.300, 9.000, 11.700 y 14.400: clasificación actual/ampliación/no factible, ahorro frente al local, etiquetas horizontales en millones y cursor en COP, actualización de inventario y costos, selección de alternativas, CSV/PNG, modo exposición, navegación Inventario/Costos/Ahorro comparativo y conservación de demandas al desactivarlo.
- Las seis pantallas anteriores superaron nuevamente sus 138 comprobaciones sobre el servidor con la versión final: navegación, demanda, gráficas, gestión, retorno al análisis completo y wrapper autónomo.
- Capturas revisadas de las tres vistas ejecutivas. El panel de parámetros se recoge y el contenido ocupa el ancho; las conclusiones ejecutivas son breves. Las tablas detalladas y los parámetros permanecen accesibles sin sustituir las herramientas originales.
- La tabla distingue la mejor opción con capacidad actual de la recomendación considerando capacidad adicional. El límite anual del proveedor también puede causar la clasificación No factible aunque exista espacio en bodega.
- “Diferencia reducida” utiliza un umbral interpretativo explícito del 2 %; no modifica costos ni rankings. Las opciones de ampliación incluyen el alquiler cuando sea la alternativa factible de menor costo del modelo original.
- Las demandas de prueba no se incorporaron como datos iniciales ni resultados fijos. Se mantienen los valores originales al restablecer y los cuatro campos independientes editables.

Cambios locales sincronizados en `publicacion/eoq-g1`. No se publicó ni se subió esta revisión a GitHub. Para revisión visual se inició Streamlit desde `eoq-g1`, puerto 8511.

## Panel ejecutivo definitivo · versión 2026-10-11.3 · puerto 8501

- Se comprobó que el proceso previo del puerto 8501 ejecutaba `../../.venv/bin/python -m streamlit run app.py` desde `publicacion/eoq-g1`. Se sincronizó el módulo y se reinició ese proceso, cargando la versión nueva. La prueba de navegador confirma `http://127.0.0.1:8501/` y la versión visible `2026-10-11.3`.
- 15 pruebas Python superadas en la carpeta de publicación: modelo y costos originales, estados de capacidad, ahorro, horizonte y pedidos, cuatro demandas iniciales de demostración, edición y persistencia al alternar las pestañas, un único gráfico ejecutivo por pestaña, composición individual y etiquetas monetarias con dos decimales.
- 39 comprobaciones Chromium contra el puerto 8501 superadas, cero errores JavaScript o consola: inicialización 6.300/9.000/11.700/14.400; etiquetas `$967,05 M` horizontales y COP completos en tooltip; capacidad actual frente a capacidad adicional; CSV de doce filas; BASE.D de 9.000 intacto; tres pestañas con un único gráfico visible/renderizado por vez; selectores principales visibles y secundarios recogidos; ahorro calculado; composición sin adquisición dominante y selección individual de Transporte; demanda editada de 6.500 conservada al cambiar de pestaña y volver a modo completo; inventario recalculado con esa demanda.
- Las seis pantallas originales superaron 138 comprobaciones sobre ese mismo servidor de publicación, sin errores ni scripts externos en el wrapper.
- Capturas revisadas a 1366×768: Costos con indicadores, etiquetas compactas y conclusión; composición individual con tres barras de Transporte en una escala propia; Inventario y Ahorro comparativo. Los controles se recogen en un popover y las tablas/descargas extensas se consultan en modo completo, sin añadirlas a la vista ejecutiva.
- Comparación sintáctica confirma que `original_values`, `evaluate` y `sawtooth` no cambiaron respecto a la versión anterior. No se modificaron `dist`, las fórmulas JavaScript, `app.py`, `embedded.py` ni las dependencias.
- Los valores de demostración son demandas editables derivadas de los factores solicitados, no resultados fijos; la demanda original G1 sigue en 9.000. Las sesiones existentes conservan sus ediciones al navegar. Un reinicio del servidor elimina la sesión anterior y carga la configuración inicial.

Archivos locales modificados: `simulator.py`, `tests/test_simulator.py`, `tests/simulator.test.cjs`, `README.md` y `VALIDACION.md`, sincronizados en el proyecto y en `publicacion/eoq-g1`. No se publicó en GitHub. Servidor de revisión dejado activo en 8501.

## Preguntas de gerencia · versión 2026-10-11.5 · puerto 8501

- Se contrastaron los valores con el texto original del caso G1 y `dist/model.js`: precio local 103.000 → 99.000 COP/unidad, flete internacional de 20 pies 6.930.000 → 10.000.000 COP/pedido y aporte del proveedor al molde 20 → 50 %. Cada pregunta aplica únicamente su parámetro desde G1 original, con D = 9.000 y criterio anual equivalente; no usa ni modifica las cuatro demandas editables ni sus parámetros financieros.
- **30 pruebas Python superadas** desde la carpeta de publicación, incluidas nueve de gerencia, paridad de las doce filas con el motor JavaScript original y comprobaciones de sesión. Ordenar incluye todos los costos por pedido, incluido flete una vez; TRC = ordenar + almacenar; integral = adquisición + TRC + capacidad + molde. Los porcentajes comparan el mismo componente con G1 y se dejan sin definir cuando la base es cero.
- **419 comprobaciones en Streamlit/Chromium superadas**, cero errores de consola: cuatro opciones de gerencia, costos/EOQ/lotes contra `EOQ.calculate(EOQ.variation(n))`, tres inventarios durante 12 meses, antes/después y diferencias monetarias/porcentuales de siete indicadores, límites de capacidad, preguntas independientes, navegación por las cuatro vistas ejecutivas y persistencia de pregunta/componente. Se editaron las demandas a 6.500/9.500/12.500/15.500 y se modificaron precio local, flete y aporte del simulador; las preguntas conservaron sus resultados G1 y las ediciones sobrevivieron a la navegación y al regreso a modo completo.
- El precio local recalcula su EOQ y lote; el flete cambia el EOQ de referencia de 20 pies, pero mantiene el lote real de 1.900 y sus inventarios; el aporte al molde cambia únicamente molde y costo integral. La empresa pasa de asumir 80 % a 50 % del equivalente anual de 45.000.000, reduciendo su costo en 13.500.000 COP/año; no se aplica una tasa de interés.
- Los 20 pies requieren 76 posiciones y conservan el costo anual completo de ampliación de 13.000.000; no se cobra una posición aislada. Los 40 pies requieren 168 frente a 165 disponibles y siguen excluidos. El local es factible con capacidad actual. G1 recomienda 20 pies condicionado a ampliar; las tres preguntas recomiendan local. La viabilidad se conserva en las tres variaciones.
- **75 comprobaciones del simulador existente** superadas en el wrapper de publicación: cuatro demandas y sus ediciones, tabla TRC, costos equivalentes/observados, CSV de doce filas, composición, indicadores de factibilidad, etiquetas en millones, navegación y restauración. **138 comprobaciones de las seis pantallas originales** y **41 controles del motor JavaScript** superados. No se modificaron `evaluate`, `sawtooth`, `dist/`, `app.py`, `embedded.py` ni las dependencias.
- Capturas finales revisadas a 1366×768 y 390×844. En exposición, inventario y antes/después comparten una fila, con la tabla de costos debajo; la conclusión puede requerir un desplazamiento corto. En móvil los bloques se apilan y las tablas se convierten en tarjetas sin recorte horizontal. Solo la vista ejecutiva activa genera su gráfica. En modo completo la sección se consulta en un expander.
- Se sincronizaron proyecto y `publicacion/eoq-g1` y se reinició el servidor de esa carpeta para cargar el módulo actualizado, sin depender de una importación anterior. La versión visible es **Simulador · 2026-10-11.5**. Entrada: `app.py`; servidor local activo en `http://localhost:8501`. El servidor no requiere Node.js ni rutas propias del Mac.

Archivos de esta revisión: reemplazar `simulator.py`, `README.md`, `VALIDACION.md`, `tests/test_simulator.py` y `tests/simulator.test.cjs`; añadir `management.py`, `tests/test_management.py` y `tests/management.test.cjs` cuando se autorice la publicación. **No se publicó ni se subió esta revisión a GitHub.**
