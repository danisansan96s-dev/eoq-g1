# EOQ G1 · EAFIT — Streamlit Community Cloud

Herramienta independiente de apoyo a la decisión EOQ. Conserva el diseño y los cálculos HTML/JavaScript, la demanda editable, los gráficos y las tres variaciones de gerencia. Los archivos del pronosticador MotoTrak no forman parte de este proyecto.

## Publicar desde un nuevo repositorio GitHub

1. Cree un repositorio llamado **eoq-g1**.
2. Suba el contenido de esta carpeta a la raíz del repositorio. `app.py`, `embedded.py`, `requirements.txt`, `dist/` y `.streamlit/config.toml` deben conservar esta estructura; no suba la carpeta contenedora como un nivel extra.
3. En Streamlit Community Cloud elija **Create app** y conecte el repositorio.
4. Seleccione repositorio **eoq-g1**, rama **main** y archivo principal **app.py**.
5. En opciones avanzadas seleccione **Python 3.11**, versión usada en la verificación, y despliegue.

No requiere Node.js, npm, paquetes del sistema, secretos, Excel, Word ni rutas del Mac para iniciar. El servidor usa Streamlit 1.64.0 y Plotly 7.1.0. El análisis original se calcula en el navegador; el simulador utiliza Python y Plotly.

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
├── simulator.py           # Simulador y sus cuatro vistas ejecutivas
├── decision.py            # Resumen compartido de recomendación y capacidad
├── management.py          # Sensibilidades independientes de G1
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

## Corrección del wrapper de Streamlit

Para corregir una publicación que aún solicita `presentation.js?v=1` externamente, reemplace en GitHub **app.py** y **embedded.py** por los archivos de esta carpeta y reinicie la aplicación publicada. Mantenga `dist/presentation.js` junto a los otros recursos ya incluidos en el proyecto.

El wrapper incorpora los tres scripts en su posición original: model.js, app.js y presentation.js. Los parámetros de versión se conservan como metadatos y se omiten al leer el archivo local. No queda ningún atributo src en los scripts del iframe. Si falta un recurso, se altera el orden o queda un script externo, la carga se detiene con un mensaje en lugar de mostrar una pestaña rota.

## Modo exposición

La pestaña **Modo exposición** presenta seis pantallas, una a la vez: datos y modelo, EOQ y lotes, capacidad, decisión económica, sensibilidad y puntos de equilibrio, y preguntas de gerencia.

- Use **Anterior**, **Siguiente**, los seis botones numerados o las flechas izquierda/derecha del teclado. Las flechas no cambian de pantalla mientras edita un campo.
- La pantalla y el escenario se conservan al avanzar. El nombre del escenario siempre aparece arriba.
- Cambie la demanda con el control superior y pulse **Aplicar**. Se conservan los demás parámetros activos. **Restaurar G1** recupera todos los datos originales.
- Cambie otros parámetros en **Análisis completo**; volver al modo exposición actualiza sus indicadores, curvas y conclusiones con esos datos.
- En EOQ seleccione la fuente para comparar sus curvas de pedidos, mantenimiento y TRC; la tabla conserva las tres fuentes y las curvas marcan EOQ y lote real.
- La pantalla económica muestra cinco políticas: contenedor 20 actual/adicional, contenedor 40 actual/adicional y local con EOQ. Las opciones inviables se excluyen; una capacidad adicional innecesaria no compite.
- Las curvas de precio y financiación cambian una variable desde el escenario activo; el precio recalcula EOQ, posiciones y bodega local en cada punto. Los umbrales no se presentan como viables si faltan capacidad o referencia importada.
- **Pantalla completa** amplía la pantalla actual y permite seguir navegando. El botón cambia para salir; también puede usar Escape. Depende del soporte y los permisos del navegador.
- Cada botón de gerencia empieza en G1 y modifica únicamente su parámetro. Aplicar demanda y navegar conservan el escenario; elegir una variación restaura G1 antes de aplicar esa variación.
- En portátil se muestran indicadores, gráfica/tabla y conclusión sin desplazamiento vertical. En pantallas pequeñas se apilan bloques y se habilita desplazamiento; las tablas y gráficas anchas pueden desplazarse horizontalmente para mantenerlas legibles.

### Archivos que actualizar en GitHub

Actualizar `app.py`, `embedded.py`, `dist/index.html`, `dist/app.js`, `dist/style.css`, `README.md`, `VALIDACION.md` y `tests/test_streamlit.py`. Añadir `dist/presentation.js` y `tests/presentation.test.cjs`. `requirements.txt` y `dist/model.js` conservan sus versiones.

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

## Simulador de escenarios EOQ

Abra la pestaña **Simulador de escenarios EOQ**, junto a Aplicación EOQ G1. Esta última conserva Análisis completo y las seis pantallas de Modo exposición. Los parámetros del simulador son independientes y se conservan con `st.session_state` al navegar; modificar el simulador no cambia el análisis original.

El panel izquierdo permite editar precios, costos por pedido, mantenimiento, aporte al molde, lotes completos, bodegas y cuatro demandas. La configuración inicial de demostración es 6.300, 9.000, 11.700 y 14.400 unidades/año (70 %, 100 %, 130 % y 160 % de la demanda original G1). Estos escenarios son editables y no son pronósticos ni reemplazan BASE. Puede introducir demandas positivas o aplicar un porcentaje de G1 por escenario. Base G1 también es editable; Restablecer recupera todos los datos originales. Confirme cada campo con Enter o haciendo clic fuera: todos los resultados se recalculan automáticamente, sin botón de aplicación. Comparar escenarios activa las tres curvas. El selector de escenario controla una sola demanda en el inventario; la tabla y las barras comparan los cuatro escenarios.

`simulator.py` lee los valores originales directamente de `dist/model.js`; implementa en Python sus ecuaciones de EOQ, costo y capacidad, verificadas contra los resultados del modelo original. No modifica el motor JavaScript. Funciones principales: `original_values`, `evaluate`, `sawtooth`, `reset`, `parameters` y `render_simulator`.

Hay dos criterios económicos explícitos:

- **Anual equivalente:** reproduce G1 con D/Q pedidos, Q/2 de inventario promedio y adquisición de D unidades. Se muestran también los pedidos enteros y el inventario final del año.
- **Año observado:** inicia con inventario cero y un pedido al mes 0; recibe lotes completos importados y emite `ceil(D/Q)` pedidos, sin reposición al mes 12. Costea las unidades efectivamente recibidas y el mantenimiento mediante el área exacta del diente de sierra. Puede habilitar un último pedido local parcial; esta opción nunca fracciona contenedores. La frecuencia teórica, el número entero emitido y el promedio observado se distinguen en la tabla.

El flete se desglosa del costo por pedido y se suma una sola vez. Transporte local corresponde a `tl`. El molde es el equivalente anual original a cargo de la empresa: `mold × (1 − p/100)`. `p` es el aporte contractual del proveedor; faltan tasa financiera y plazo para calcular intereses o amortización, por lo que no se inventan. La capacidad utiliza el lote máximo y las alternativas actual/alquiler/ampliación; el proveedor local conserva su límite anual. Las barras inviables aparecen rayadas y no participan en la recomendación. En caso de empate se muestran ambas alternativas.

Plotly permite zoom, selección de curvas mediante la leyenda y exportación PNG. Descargar comparación CSV entrega las doce filas con valores numéricos; el botón de cámara de cada gráfica exporta la imagen. El modo exposición del simulador renderiza solamente la pestaña activa y recoge los parámetros en un popover; sus indicadores y conclusiones pertenecen a esa vista. Tabla, CSV y conclusiones extensas se consultan en modo completo.

Pruebas adicionales:

```sh
python -m unittest discover -s tests -p 'test_*.py'
EOQ_PLAYWRIGHT=/tmp/eoq-qa/node_modules/playwright node tests/simulator.test.cjs
```

Para publicar esta actualización, reemplace `app.py`, `requirements.txt`, `README.md` y `VALIDACION.md`; añada `simulator.py`, `tests/test_simulator.py` y `tests/simulator.test.cjs`. Los archivos de `dist` y `embedded.py` permanecen vigentes. Entrada de Community Cloud: `app.py`. Python calcula y Plotly genera las gráficas; Node.js solo se usa opcionalmente para las pruebas locales de navegador.

### Factibilidad y lectura ejecutiva

El simulador distingue **Factible actualmente**, **Viable con ampliación** y **No factible**, usando la capacidad actual, las opciones reales de capacidad adicional y el límite anual del proveedor. “Viable con ampliación” incluye la opción de alquiler cuando resulte la bodega de menor costo; la conclusión indica cuál se selecciona. Se muestran por separado la recomendación con capacidad actual, la que considera capacidad adicional y las alternativas excluidas. En G1 corresponden a local, 20 pies y 40 pies, respectivamente.

Las barras muestran millones de COP con etiquetas horizontales; el cursor conserva el importe completo. Puntos indican que se requiere capacidad adicional; rayas y un tono atenuado señalan alternativas no factibles. La gráfica de ahorro usa `costo local − costo alternativa`; positivo significa ahorro y negativo sobrecosto. El cursor incluye el porcentaje respecto al costo local. Las alternativas inviables tienen ahorro no realizable; si el local es inviable también se señala que la referencia es solo económica. Los ahorros con ampliación están condicionados a habilitar la bodega, cuyo costo ya estaba incluido en el modelo.

Las conclusiones se generan para cada escenario y describen ambas recomendaciones, ahorro, porcentaje y restricciones. Una diferencia menor al 2 % se describe como reducida: es un criterio de interpretación explícito y no cambia ninguna ecuación ni ranking.

En **Modo exposición**, el panel editable se recoge en el botón **Editar parámetros** y el contenido principal ocupa todo el ancho. Use las pestañas **Inventario**, **Costos**, **Ahorro comparativo** y **Preguntas de gerencia** para presentar una gráfica a la vez, conservando el selector, los indicadores y la conclusión. Al desactivarlo vuelve el panel lateral sin perder los parámetros. La composición se consulta dentro de Costos. La tabla detallada, CSV y conclusiones de los cuatro escenarios se consultan desactivando Modo exposición; la tabla compacta de TRC también está disponible en Inventario durante la exposición.

Para revisar la copia de publicación, ejecute desde `publicacion/eoq-g1`: `streamlit run app.py --server.port 8501`, luego abra `http://localhost:8501` y seleccione Simulador de escenarios EOQ. Puede probar 6.300, 9.000, 11.700 y 14.400 unidades/año; estos son valores de prueba editables, no nuevos datos originales ni resultados fijos. No se publicó esta revisión en GitHub.


### Versión ejecutiva 2026-10-11.6 · revisión en puerto 8501

La vista ejecutiva usa cuatro pestañas con estado y ejecución condicional: **Inventario**, **Costos**, **Ahorro comparativo** y **Preguntas de gerencia**. Solo la pestaña activa genera un gráfico, sus indicadores y su conclusión; no se dejan gráficos ocultos ni tablas extensas debajo. Escenario y alternativa permanecen visibles en las tres vistas de demandas; en Preguntas de gerencia se conservan en el popover Demandas del simulador porque las preguntas usan el G1 original. Los campos económicos y las cuatro demandas se siguen montando dentro del popover de parámetros, para que Streamlit no elimine sus valores al navegar.

En **Costos**, alterne **Costo total** y **Composición**. La composición muestra los componentes elegidos como barras agrupadas con colores por alternativa, no como una pila dominada por adquisición. Inicialmente excluye adquisición; puede añadirla, retirar otros componentes o seleccionar solo Transporte, Mantenimiento, Pedidos, Capacidad o Molde. La escala se ajusta a la selección. Las etiquetas de barras son horizontales y muestran dos decimales, como `$967,05 M`; el valor completo en COP queda en el tooltip.

Los indicadores distinguen **Factible con capacidad actual**, **Mejor permitiendo ampliar** y **Condición de esa opción**. En G1, Local es factible actualmente y 20 pies es la opción más económica permitiendo ampliar. 40 pies permanece excluido.

La demostración inicial usa los factores 70/100/130/160 % sobre la demanda original del modelo, sin escribir resultados fijos. **Configurar demostración** recupera estas cuatro demandas sin modificar precios ni costos. **Restablecer valores originales** recupera todos los valores G1. El valor original `BASE.D` permanece en 9.000.

La versión cargada se identifica al pie con **Simulador · 2026-10-11.6**. La copia para revisión se sincroniza en `publicacion/eoq-g1` y se comprueba en el puerto 8501. Tras un cambio Python, reinicie el servidor si conserva un módulo importado anterior. Los datos de sesión sobreviven a la navegación dentro de una ejecución; un reinicio del servidor comienza una sesión nueva.

Debajo de la gráfica de inventario, **Costos EOQ** compara las tres alternativas del escenario seleccionado, incluso si la gráfica muestra una sola. Presenta ordenar, almacenar y TRC en COP/año con separadores de miles. El menor TRC matemático se destaca independientemente de la factibilidad, que conserva los tres estados actuales; los empates se reconocen con la misma tolerancia de un centavo del proyecto.

En el modelo original, ordenar incluye flete internacional, nacionalización, transporte nacional y administración; para el local incluye transporte, inspección y administración. La tabla utiliza `ordering + freight` para reconstruir este costo completo, sin duplicar el transporte que las otras vistas desglosan. **TRC = ordenar + almacenar**; excluye adquisición, capacidad y molde. El costo integral y sus recomendaciones conservan sus fórmulas y resultados.

La tabla respeta el criterio temporal activo: **Anual equivalente** usa D/Q y Q/2; **Año observado** usa pedidos enteros e inventario promedio integrado durante los 12 meses. El criterio aparece explicado debajo de la tabla. Cambiar demanda, precios, costos por pedido, tasa o lotes actualiza las tres filas. En exposición, la gráfica usa 190 px con márgenes compactos; en pantallas pequeñas las filas se reorganizan con sus etiquetas para conservar todos los datos.

La leyenda del inventario conserva los nombres y colores de las tres alternativas; la factibilidad se consulta en la tabla y al pasar el cursor por las curvas. Esto evita superponer la leyenda y el eje de meses en pantallas pequeñas. Pandas, ya usado por las tablas detalladas, se importa al iniciar el módulo para evitar una importación parcial al abrir varias sesiones simultáneamente.

Prueba de navegador de esta copia: `EOQ_TEST_URL=http://127.0.0.1:8501 EOQ_PLAYWRIGHT=/tmp/eoq-qa/node_modules/playwright node tests/simulator.test.cjs`. No se publicó en GitHub.

### Preguntas de gerencia del simulador

Seleccione **Preguntas de gerencia** en Modo exposición, o abra la sección del mismo nombre en modo completo. Elija **Escenario original**, **Pregunta 1**, **Pregunta 2** o **Pregunta 3**. Cada selección vuelve a leer G1 desde `dist/model.js`, con demanda original de 9.000 y criterio anual equivalente; únicamente cambia precio local a 99.000, flete internacional de 20 pies a 10.000.000 o aporte del proveedor al molde a 50 %, respectivamente. Estos valores corresponden a las tres variaciones del texto original del caso. No toma ni modifica las cuatro demandas editadas, sus parámetros, el criterio observado ni la selección de alternativa del simulador.

La gráfica compara los tres inventarios durante 12 meses con sus límites de capacidad. Debajo, la tabla muestra ordenar (incluido todo flete por pedido una vez), almacenar, TRC, costo integral y factibilidad. **Costo a comparar** permite consultar adquisición, ordenar, almacenar, TRC, capacidad, molde o costo integral en **Antes G1 vs. Después**, con diferencia en COP/año y porcentaje respecto al mismo componente de G1. Un porcentaje con costo base cero se indica como no definido. La preferencia integral excluye alternativas inviables; el menor TRC es una marca matemática independiente.

El precio local recalcula su EOQ, lote y costos. El flete recalcula el EOQ de referencia de 20 pies y sus costos de ordenar; su lote real permanece completo. El aporte al molde solamente cambia molde y costo integral: `mold × (1 − p/100)`, sin intereses inventados ni cambios al EOQ. La conclusión explica el cambio de preferencia, los componentes afectados y la viabilidad. Los 20 pies incluyen el costo anual completo de ampliación; los 40 pies siguen excluidos por requerir 168 posiciones frente a 165 disponibles.

La pregunta y el componente se conservan al navegar por las cuatro vistas ejecutivas. El expander **Preguntas de gerencia · G1 independiente**, dentro de **Editar parámetros**, conserva esos selectores cuando está activa otra vista. **Demandas del simulador** mantiene los selectores de demanda y alternativa durante la vista gerencial; no altera la base de las preguntas.

Archivos de esta revisión en `publicacion/eoq-g1`: reemplazar `simulator.py`, `README.md`, `VALIDACION.md`, `tests/test_simulator.py` y `tests/simulator.test.cjs`; añadir `management.py`, `tests/test_management.py` y `tests/management.test.cjs` cuando se autorice la publicación. `app.py`, `embedded.py`, `requirements.txt` y `dist/` conservan sus archivos anteriores. La entrada sigue siendo `app.py`. Esta revisión se deja solamente en localhost.

Prueba adicional: `EOQ_TEST_URL=http://127.0.0.1:8501 EOQ_PLAYWRIGHT=/tmp/eoq-qa/node_modules/playwright node tests/management.test.cjs`.

### Confirmación y recomendación compartida · 2026-10-11.6

Los campos de Streamlit confirman su valor con **Enter** o al **hacer clic fuera del campo**. Esa confirmación recalcula el simulador; no necesita un botón de aplicación. Se retiró **Aplicar cambios**, que únicamente provocaba otra ejecución y podía dar a entender que los resultados estaban pendientes. La instrucción aparece tanto en los parámetros como en la franja del simulador. **Restablecer valores originales** recupera G1 y mantiene su comportamiento anterior sobre las cuatro demandas.

La franja muestra la mejor fuente factible con capacidad actual, la mejor considerando capacidad adicional, su costo integral anual, el ahorro/sobrecosto frente al local y la capacidad de la bodega elegida. El ahorro es `costo local − costo recomendado`: si gana el local, es cero; no se sustituye por la ventaja frente a la siguiente opción. La ampliación o el alquiler requerido se identifica expresamente e incluye su costo completo. Los importes principales se abrevian en millones y su ayuda conserva el importe en COP. El menor TRC sigue en la tabla, separado de la decisión por costo integral.

En **Inventario**, **Costos** y **Ahorro comparativo**, la franja usa exactamente las filas evaluadas de la demanda seleccionada y el criterio temporal activo. Cambiar solamente la alternativa filtra las gráficas; la recomendación sigue comparando las tres fuentes. En **Preguntas de gerencia**, la franja se identifica como **Pregunta académica · G1 independiente** y utiliza la pregunta elegida, con D original de 9.000 y criterio anual equivalente. **Decisión de mis parámetros** ofrece aparte la recomendación del simulador editable, con su propia demanda y criterio; modificar esos parámetros nunca contamina el punto de referencia de las preguntas.

Los selectores y todos los campos continúan montados al navegar para conservar su estado. En exposición se retiraron los KPI de decisión duplicados de Costos y Ahorro; los datos operativos del inventario se muestran en una línea compacta. La franja permanece encima de las cuatro vistas y se fija durante el desplazamiento en portátil. En móvil los indicadores se apilan y la franja deja de fijarse para permitir leer el contenido completo. No se añadieron gráficas ni se cambiaron las fórmulas financieras. Las conclusiones académicas usan una versión breve durante la exposición y conservan el detalle en modo completo.

Para revisar, recargue `http://localhost:8501`, seleccione Simulador de escenarios EOQ y compruebe el pie **2026-10-11.6**. Pruebe cada variación después de **Restablecer valores originales**, confirme con Enter o clic fuera y navegue por las cuatro pestañas. La copia está en `publicacion/eoq-g1`, entrada `app.py`; aún no se publica en GitHub.

Archivos de esta revisión: `simulator.py`, `management.py`, `decision.py`, `README.md`, `VALIDACION.md`, `tests/test_decision.py`, `tests/interaction.test.cjs`, `tests/simulator.test.cjs` y `tests/management.test.cjs`. `app.py`, `embedded.py`, `requirements.txt` y `dist/` conservan sus archivos anteriores.

Prueba de interacción: `EOQ_TEST_URL=http://127.0.0.1:8501 EOQ_PLAYWRIGHT=/tmp/eoq-qa/node_modules/playwright node tests/interaction.test.cjs`.
