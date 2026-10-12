"""Simulador independiente; datos originales leídos del modelo JavaScript del taller."""
import ast
import csv
from html import escape
import io
import math
import re
from pathlib import Path

# Completar la dependencia de las tablas antes de que Plotly la consulte
# desde sesiones concurrentes durante el arranque del servidor.
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

NAMES = {'20': '20 pies', '40': '40 pies', 'local': 'Proveedor local'}
COLORS = {'20': '#087d68', '40': '#397bd5', 'local': '#bd7528'}
SCENARIOS = ['Baja', 'Base G1', 'Alta', 'Crítica']


def original_values():
    source = (Path(__file__).parent / 'dist' / 'model.js').read_text(encoding='utf-8')
    body = re.search(r'const BASE=Object.freeze\((\{[^}]+\})\)', source).group(1)
    values = ast.literal_eval(re.sub(r'([,{])\s*(\w+)\s*:', r"\1'\2':", body))
    values['vi20'] = values['vi40'] = values['vi']
    return values


def evaluate(p, demand, observed=False, partial_local=False):
    """Replica las ecuaciones EOQ originales y añade un horizonte finito explícito.

    Costos equivalentes usan D/Q y Q/2. Costos observados usan pedidos enteros,
    unidades recibidas y área exacta del inventario; no mezclamos ambos criterios.
    """
    numeric = [v for k, v in p.items() if k != 'rMode']
    if any(not math.isfinite(v) or v < 0 for v in numeric):
        raise ValueError('Los parámetros deben ser finitos y no negativos.')
    if not math.isfinite(demand) or demand <= 0:
        raise ValueError('La demanda debe ser positiva y finita.')
    rate = (p['rDirect'] if p['rMode'] == 'direct' else sum(p[k] for k in ['capital', 'insurance', 'damage', 'handling'])) / 100
    if rate <= 0 or p['p'] > 100 or any(p[k] <= 0 for k in ['vi20', 'vi40', 'vl', 'q20', 'q40', 'units']):
        raise ValueError('Revise precios, lotes, unidades por posición, tasa y aporte del molde.')
    if any(p[k] != int(p[k]) for k in ['q20', 'q40', 'units', 'positions', 'rentPositions', 'expandPositions']):
        raise ValueError('Los lotes y las posiciones deben ser enteros.')
    rows = []
    for key in NAMES:
        local = key == 'local'
        price = p['vl'] if local else p['vi' + key]
        freight = p['tl'] if local else p['f' + key]
        other = p['il'] + p['al'] if local else sum(p[c + key] for c in ['c', 't', 'a'])
        order_cost = freight + other
        if local and order_cost <= 0:
            raise ValueError('El costo por pedido local debe ser positivo para calcular el EOQ.')
        eoq = math.sqrt(2 * demand * order_cost / (price * rate))
        lot = eoq if local else p['q' + key]
        theoretical = demand / lot
        # No emitir un pedido al final exacto del año por errores de redondeo.
        nearest = round(theoretical)
        count = max(1, nearest if math.isclose(theoretical, nearest, abs_tol=1e-10, rel_tol=1e-12) else math.ceil(theoretical))
        remainder = max(0, min(lot, demand - (count - 1) * lot))
        final_lot = remainder if local and partial_local else lot
        received = (count - 1) * lot + final_lot
        actual_average = ((count - 1) * lot ** 2 / 2 + final_lot * remainder - remainder ** 2 / 2) / demand
        needed = math.ceil(lot / p['units'])
        configs = [('Actual', p['positions'], 0), ('Alquiler', p['positions'] + p['rentPositions'], p['rent']), ('Ampliación', p['positions'] + p['expandPositions'], p['expand'])]
        viable = sorted((c for c in configs if c[1] >= needed), key=lambda c: c[2])
        chosen = viable[0] if viable else None
        supply = not local or demand <= p['localCapacity']
        feasible = chosen is not None and supply
        multiplier = count if observed else theoretical
        average = actual_average if observed else lot / 2
        acquisition = price * (received if observed else demand)
        ordering = other * multiplier
        transport = freight * multiplier
        holding = price * rate * average
        capacity = chosen[2] if chosen else 0
        mold = p['mold'] * (1 - p['p'] / 100) if local else 0
        rows.append(dict(id=key, name=NAMES[key], demand=demand, eoq=eoq, Q=lot, theoretical=theoretical, count=count, cycle=365 * lot / demand, average=average, actual_average=actual_average, final_lot=final_lot, closing=max(0, received-demand), acquisition=acquisition, ordering=ordering, freight=transport, holding=holding, capacity=capacity, mold=mold, total=acquisition+ordering+transport+holding+capacity+mold, positions=needed, available=max(c[1] for c in configs), chosen=chosen[0] if chosen else 'Sin capacidad', feasible=feasible, supply=supply, current_feasible=needed <= p['positions']))
    return rows


def sawtooth(row, partial_local=False):
    """Eventos exactos; último tramo parcial sin reposición al mes 12."""
    lot, demand, count = row['Q'], row['demand'], row['count']
    if count > 20000:
        raise ValueError('Más de 20.000 pedidos: ajuste los parámetros para visualizar los eventos.')
    x, y = [0.0], [0.0]
    for index in range(count):
        start = 12 * index * lot / demand
        amount = row['final_lot'] if index == count-1 and row['id'] == 'local' and partial_local else lot
        x.append(start); y.append(amount)
        end = min(12.0, 12 * (index+1) * lot / demand)
        remaining = max(0, amount-demand*(end-start)/12)
        x.append(end); y.append(remaining)
    return x, y


def number(value, decimals=2):
    return f'{value:,.{decimals}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def money(value):
    return '$ ' + number(value, 0) + ' COP'


def millions(value):
    return '$ ' + number(value / 1_000_000)


def reset():
    defaults = original_values()
    for key, value in defaults.items():
        st.session_state['sim_' + key] = value
    # Solo Base G1 es un dato original; los otros escenarios empiezan iguales.
    for index in range(4):
        st.session_state['sim_d' + str(index)] = float(defaults['D'])
        st.session_state['sim_factor' + str(index)] = 100.0
    st.session_state['sim_partial'] = False
    st.session_state['sim_basis'] = 'Anual equivalente · modelo original'


def parameters():
    p = original_values()
    if 'sim_D' not in st.session_state:
        reset()
        st.session_state.setdefault('sim_scenario', 'Base G1')
    st.caption('Confirma cada valor con Enter o haciendo clic fuera del campo. Los resultados se actualizan automáticamente; no necesitas un botón para aplicar.')
    def inputs(fields):
        for key, label in fields:
            integer = key in ['q20', 'q40', 'units', 'positions', 'rentPositions', 'expandPositions']
            if integer:
                st.number_input(label, min_value=1 if key in ['q20', 'q40', 'units'] else 0, step=1, key='sim_'+key)
            else:
                # Inicialización homogénea de los widgets flotantes.
                st.session_state['sim_'+key] = float(st.session_state['sim_'+key])
                st.number_input(label, min_value=0.0, step=1.0, key='sim_'+key)
    with st.expander('Precios y pedidos', expanded=False):
        inputs([('vi20','Precio 20 pies · COP/unidad'),('vi40','Precio 40 pies · COP/unidad'),('vl','Precio local · COP/unidad')])
        for key in ['20','40']:
            st.caption(NAMES[key] + ' · COP/pedido')
            inputs([(c+key,label) for c,label in [('f','Flete '+key),('c','Nacionalización '+key),('t','Transporte terrestre '+key),('a','Administración '+key)]])
        inputs([('tl','Transporte local · COP/pedido'),('il','Inspección local · COP/pedido'),('al','Administración local · COP/pedido')])
    with st.expander('Mantenimiento y molde'):
        st.selectbox('Cálculo de tasa', ['components','direct'], format_func=lambda v:'Suma de componentes' if v=='components' else 'Tasa directa', key='sim_rMode')
        inputs([('capital','Capital · % anual'),('insurance','Seguro · % anual'),('damage','Deterioro · % anual'),('handling','Manejo · % anual'),('rDirect','Tasa directa · % anual'),('mold','Molde · equivalente anual COP'),('p','Aporte del proveedor al molde · %')])
        st.caption('El porcentaje es el aporte contractual del proveedor, no una tasa de interés. El modelo no contiene tasa financiera, plazo ni amortización. Molde a cargo de la empresa = molde × (1 − aporte/100).')
    with st.expander('Lotes y capacidad'):
        inputs([('q20','Lote completo 20 pies · unidades'),('q40','Lote completo 40 pies · unidades'),('units','Unidades por posición'),('positions','Posiciones actuales'),('rentPositions','Posiciones adicionales por alquiler'),('expandPositions','Posiciones adicionales por ampliación'),('rent','Alquiler · COP/año'),('expand','Ampliación · COP/año'),('localCapacity','Capacidad proveedor local · unidades/año')])
        st.caption('El lote local se calcula por EOQ; nunca se recorta para aparentar factibilidad. Se elige la bodega factible de menor costo.')
    with st.expander('Cuatro demandas independientes', expanded=True):
        st.caption('Demostración editable: 70 %, 100 %, 130 % y 160 % de G1. La demanda original G1 sigue siendo 9.000.')
        for i,name in enumerate(SCENARIOS):
            st.number_input(name+' · unidades/año',min_value=0.01,step=100.0,key='sim_d'+str(i))
            if i != 1:
                st.number_input(name+' · % de G1', min_value=0.01,step=10.0,key='sim_factor'+str(i))
                def factor(index=i):
                    st.session_state['sim_d'+str(index)] = float(original_values()['D'])*st.session_state['sim_factor'+str(index)]/100
                st.button('Usar porcentaje · '+name,on_click=factor,key='factor_'+str(i))
    st.button('Restablecer valores originales',on_click=reset,width='stretch')
    for key in p:
        p[key] = st.session_state['sim_'+key]
    return p


def feasibility(row):
    """Clasificación operativa; considera también el límite anual del proveedor."""
    if not row['supply'] or not row['feasible']:
        return 'No factible'
    return 'Factible actualmente' if row['current_feasible'] else 'Viable con ampliación'


def relevant_costs(rows):
    """TRC original: ordenar incluye todo costo por pedido, incluido transporte.

    Se utilizan los componentes del criterio temporal ya evaluado. La marca
    del mínimo es matemática; la factibilidad se informa independientemente.
    """
    costs = [dict(id=row['id'], name=row['name'],
                  ordering=row['ordering'] + row['freight'],
                  holding=row['holding'],
                  trc=row['ordering'] + row['freight'] + row['holding'],
                  status=feasibility(row)) for row in rows]
    minimum = min((item['trc'] for item in costs), default=None)
    for item in costs:
        item['minimum'] = abs(item['trc'] - minimum) < .01
    return costs


def render_relevant_costs(rows, scenario, observed):
    """Tabla compacta accesible; siempre compara las tres fuentes del escenario."""
    body = []
    for item, row in zip(relevant_costs(rows), rows):
        cells = []
        for key, label in [('ordering', 'Ordenar'), ('holding', 'Almacenar'), ('trc', 'TRC')]:
            badge = '<span class="eoq-trc-badge">Menor TRC</span>' if key == 'trc' and item['minimum'] else ''
            amount = '$ ' + number(item[key], 0)
            cells.append(f'<td class="eoq-trc-amount eoq-trc-{key}" data-label="{label} · COP/año" data-value="{item[key]}">{amount}{badge}</td>')
        state = 'current' if item['status'] == 'Factible actualmente' else 'expanded' if row['feasible'] else 'excluded'
        capacity = f"{row['positions']} posiciones · " + (row['chosen'] if row['feasible'] else 'fuera de los límites disponibles')
        body.append(f'<tr data-alternative="{item["id"]}" data-minimum="{str(item["minimum"]).lower()}">'
                    f'<th scope="row" style="border-left:4px solid {COLORS[item["id"]]}">{escape(item["name"])}</th>'
                    + ''.join(cells)
                    + f'<td data-label="Factibilidad" class="eoq-trc-status {state}" title="{escape(capacity)}">{escape(item["status"])}</td></tr>')
    criterion = ('Año observado: pedidos enteros e inventario promedio de los 12 meses.' if observed
                 else 'Anual equivalente: ordenar = A × D/Q; almacenar = v × r × Q/2.')
    st.html('''<style>
      .eoq-trc{color:#18332f;font-size:14px;line-height:1.4}
      .eoq-trc table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #d9e3dc;border-radius:6px}
      .eoq-trc caption{text-align:left;font-size:16px;font-weight:650;color:#18332f;padding:0 0 3px}
      .eoq-trc th,.eoq-trc td{padding:4px 10px;border-bottom:1px solid #e3e9e4;vertical-align:middle}
      .eoq-trc thead th{background:#edf3ed;font-weight:600;text-align:right;font-size:13px}
      .eoq-trc thead th:first-child,.eoq-trc thead th:last-child{text-align:left}
      .eoq-trc tbody th{text-align:left;font-weight:600;width:18%}
      .eoq-trc-amount{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
      .eoq-trc-trc{font-weight:700}
      .eoq-trc tr[data-minimum="true"] .eoq-trc-trc{background:#d8eee6;color:#084d3e}
      .eoq-trc-badge{display:inline-block;margin-left:6px;font-size:11px;line-height:1.2;font-weight:600}
      .eoq-trc-status{font-size:13px;font-weight:600}
      .eoq-trc-status.current{color:#08634f}.eoq-trc-status.expanded{color:#875000}.eoq-trc-status.excluded{color:#5c6260}
      .eoq-trc-note{margin:6px 0 0;font-size:12px;line-height:1.4;color:#344a40}
      @media(max-width:760px){
        .eoq-trc thead{display:none}.eoq-trc table,.eoq-trc tbody,.eoq-trc tr,.eoq-trc th,.eoq-trc td{display:block}
        .eoq-trc caption{display:block;width:100%;box-sizing:border-box;padding:6px 10px}
        .eoq-trc tr{border-bottom:2px solid #d9e3dc}.eoq-trc tbody th{width:auto;background:#edf3ed}
        .eoq-trc td{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;text-align:right}
        .eoq-trc td:before{content:attr(data-label);font-weight:500;text-align:left}
        .eoq-trc-badge{width:100%}
      }
    </style><section class="eoq-trc" aria-label="Comparación de costos EOQ">
      <table><caption>Costos EOQ · ''' + escape(scenario) + ' · ' + number(rows[0]['demand'], 0) + ''' u/año</caption>
        <thead><tr><th scope="col">Alternativa</th><th scope="col">Ordenar · COP/año</th>
          <th scope="col">Almacenar · COP/año</th><th scope="col">TRC · COP/año</th><th scope="col">Factibilidad</th></tr></thead>
        <tbody>''' + ''.join(body) + '''</tbody></table>
      <p class="eoq-trc-note"><b>TRC = ordenar + almacenar.</b> Ordenar incluye fletes y transportes por pedido, una sola vez.
        El TRC excluye adquisición, capacidad y molde; su mínimo matemático no determina la mejor opción integral.<br>'''
      + escape(criterion) + '</p></section>')


def recommendations(rows):
    current = sorted((r for r in rows if r['feasible'] and r['current_feasible']), key=lambda r:r['total'])
    expanded = sorted((r for r in rows if r['feasible']), key=lambda r:r['total'])
    return current, expanded, [r for r in rows if not r['feasible']]


def savings(row, local):
    absolute = local['total'] - row['total']
    return absolute, absolute / local['total'] * 100 if local['total'] else None


def conclusion(name, rows, compact=False):
    current, expanded, excluded = recommendations(rows)
    local = next(r for r in rows if r['id']=='local')
    text = f"{name} · {number(local['demand'],0)} unidades/año. "
    text += 'Con capacidad actual: ' + (' / '.join(r['name'] for r in current if abs(r['total']-current[0]['total'])<.01) if current else 'ninguna alternativa factible') + '. '
    if expanded:
        best = expanded[0]
        absolute, percent = savings(best, local)
        text += f"Considerando ampliación: {' / '.join(r['name'] for r in expanded if abs(r['total']-best['total'])<.01)} ({money(best['total'])}); ahorro frente al local {money(absolute)} ({number(percent)} %)" if percent is not None else f"Considerando ampliación: {best['name']}; porcentaje no definido porque el costo local es cero"
        text += f". {feasibility(best)}: {best['positions']} posiciones, bodega {best['chosen'].lower()}. "
        if best['id'] != 'local' and percent is not None and abs(percent)<2:
            text += 'Diferencia económica reducida (menos de 2 %); considere otros factores operativos. '
        if not best['current_feasible']:
            text += 'Ahorro potencial, condicionado a habilitar la capacidad adicional; su costo ya está incluido. '
    else:
        text += 'Ni con ampliación hay una alternativa factible. '
    if excluded:
        text += 'Excluidas: ' + '; '.join(r['name'] + (f" requiere {r['positions']} posiciones y el máximo es {r['available']}" if r['positions']>r['available'] else ' supera la capacidad anual del proveedor') for r in excluded) + '. '
    if not local['feasible']:
        text += 'El proveedor local es una referencia económica inviable, no una opción realizable.'
    if compact and expanded:
        best = expanded[0]
        absolute, percent = savings(best, local)
        text = f"{name} · {number(local['demand'],0)} u/año. Actual: " + (' / '.join(r['name'] for r in current if abs(r['total']-current[0]['total'])<.01) if current else 'ninguna')
        text += f". Con ampliación: {' / '.join(r['name'] for r in expanded if abs(r['total']-best['total'])<.01)} ({money(best['total'])}). Ahorro " + ('potencial' if not best['current_feasible'] else 'frente al local') + f": {short_money(absolute)} ({number(percent)} %). "
        if best['id'] != 'local' and percent is not None and abs(percent)<2:
            text += 'Diferencia reducida; valore otros factores operativos. '
        text += 'Excluidas: ' + ('; '.join(r['name'] + (f" ({r['positions']} > {r['available']} posiciones)" if r['positions']>r['available'] else ' (límite anual local)') for r in excluded) or 'ninguna') + '.'
        if not local['feasible']:
            text += ' Referencia local inviable.'
    return text


def short_money(value):
    return '$' + number(value/1_000_000,2) + ' M'


def comparison_chart(results, saving=False, exposure=False, alternative="Comparar todas las alternativas"):
    chart = go.Figure()
    for key in NAMES:
        if alternative != 'Comparar todas las alternativas' and NAMES[key] != alternative:
            continue
        items = [next(r for r in rows if r['id']==key) for rows in results.values()]
        locals_ = [next(r for r in rows if r['id']=='local') for rows in results.values()]
        amounts = [savings(r,l)[0] if saving else r['total'] for r,l in zip(items,locals_)]
        details = []
        for r,l,amount in zip(items,locals_,amounts):
            percent = savings(r,l)[1]
            status = feasibility(r)
            qualification = 'No realizable' if not r['feasible'] else 'Potencial; requiere capacidad adicional' if not r['current_feasible'] else 'Realizable con capacidad actual'
            details.append([money(amount), status, number(percent)+' %' if percent is not None else 'Porcentaje no definido', qualification, 'Referencia local inviable' if not l['feasible'] else 'Referencia local viable'])
        chart.add_trace(go.Bar(name=NAMES[key],x=list(results),y=[v/1_000_000 for v in amounts],marker=dict(color=COLORS[key],pattern_shape=['/' if not r['feasible'] else '.' if not r['current_feasible'] else '' for r in items],opacity=[.45 if not r['feasible'] else 1 for r in items]),text=[short_money(v) for v in amounts],textangle=0,textfont=dict(size=12),textposition='outside',cliponaxis=False,customdata=details,hovertemplate='%{x}<br>%{customdata[0]}<br>%{customdata[1]}<br>%{customdata[3]}'+('<br>Ahorro: %{customdata[2]}<br>%{customdata[4]}' if saving else '')+'<extra>%{fullData.name}</extra>'))
    chart.update_layout(font=dict(size=16 if exposure else 13),title='Ahorro (+) / sobrecosto (−) frente al local' if saving else 'Costo anual por escenario',barmode='group',yaxis_title='Millones de COP/año',height=230 if exposure else 390,legend=dict(orientation='h'),margin=dict(l=40,r=25,t=70,b=60),uniformtext=dict(minsize=11,mode='hide'))
    chart.add_hline(y=0,line_width=1,line_color='#18332f')
    return chart


COMPONENTS = {'acquisition':'Adquisición', 'ordering':'Pedidos sin flete', 'freight':'Transporte', 'holding':'Mantenimiento', 'capacity':'Capacidad', 'mold':'Molde a cargo'}
SIMULATOR_VERSION = '2026-10-11.6'


def render_decision(rows, p, scenario, basis, academic=False):
    """Franja común: utiliza exactamente las filas de la vista activa."""
    from decision import decision_summary, decision_conclusion
    context = 'Pregunta académica · G1 independiente' if academic else 'Simulador editable'
    summary = decision_summary(rows, p, scenario, basis, context=context)
    best = summary['best']
    def names(items):
        return ' / '.join(row['name'] for row in items) or 'Ninguna'
    def ids(items):
        return ','.join(row['id'] for row in items)
    total = best['total'] if best else None
    saving, percent = summary['saving'], summary['saving_percent']
    capacity = (f"{best['positions']} / {summary['chosen_capacity']} posiciones · "
                f"{p['positions']} actuales") if best else 'Sin opción operativa'
    cards = [
        ('current', 'Mejor con capacidad actual', names(summary['current_winners']), '',
         f'data-id="{summary["current_winners"][0]["id"] if summary["current_winners"] else ""}" data-ids="{ids(summary["current_winners"])}"'),
        ('winner', 'Mejor considerando ampliación', names(summary['winners']), '',
         f'data-id="{best["id"] if best else ""}" data-ids="{ids(summary["winners"])}"'),
        ('total', 'Costo integral · COP/año', short_money(total) if total is not None else '—', '',
         f'data-value="{total if total is not None else ""}" title="{money(total) if total is not None else "No hay una recomendación factible"}"'),
        ('saving', 'Ahorro (+) / sobrecosto (−) vs. local', short_money(saving) if saving is not None else '—',
         number(percent) + ' %' if percent is not None else 'Porcentaje no definido',
         f'data-value="{saving if saving is not None else ""}" data-percent="{percent if percent is not None else ""}" data-reference-id="local" title="{money(saving) if saving is not None else "Sin comparación"}"'),
        ('capacity', 'Factibilidad y capacidad', summary['status'], capacity,
         f'data-positions="{best["positions"] if best else ""}" data-available="{summary["chosen_capacity"] if best else ""}"')]
    body = ''.join(f'<div class="eoq-decision-item" data-field="{key}" {attributes}>'
                   f'<span class="eoq-decision-label">{escape(label)}</span>'
                   f'<strong>{escape(value)}</strong><small>{escape(detail)}</small></div>'
                   for key, label, value, detail, attributes in cards)
    hint = ('Las preguntas parten de G1; tus ediciones manuales se consultan por separado.' if academic
            else 'Confirma con Enter o clic fuera del campo; el cálculo es automático.')
    note = summary['condition'] + ' Decisión por costo integral; el menor TRC se distingue en la tabla.'
    if summary['local'] is not None and not summary['local_reference_feasible']:
        note += ' La referencia local no es viable.'
    color = COLORS[best['id']] if best else '#5c6260'
    st.html('''<style>
      .eoq-decision{background:#f5faf7;border:1px solid #d1e1d7;border-left:4px solid #087d68;border-radius:6px;padding:7px 10px;color:#18332f}
      .eoq-decision-head{display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;font-size:12px;line-height:1.3;margin-bottom:5px}
      .eoq-decision-head b{font-weight:650}.eoq-decision-head span{color:#344a40}
      .eoq-decision-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}
      .eoq-decision-item{min-width:0}.eoq-decision-label{display:block;font-size:11px;line-height:1.3;margin-bottom:2px}
      .eoq-decision-item strong{display:block;font-size:17px;line-height:1.25;overflow-wrap:anywhere}
      .eoq-decision-item small{display:block;font-size:11px;line-height:1.3}
      .eoq-decision-item[data-field="capacity"] strong{font-size:14px}
      .eoq-decision-foot{font-size:11px;line-height:1.3;margin:5px 0 0}
      [data-testid="stLayoutWrapper"]:has(> .st-key-sim_decision){position:sticky;top:3.6rem;z-index:20}
      @media(max-width:760px){.eoq-decision-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.eoq-decision-item strong{font-size:15px}.eoq-decision-head{font-size:11px}[data-testid="stLayoutWrapper"]:has(> .st-key-sim_decision){position:static}}
    </style><section class="eoq-decision" aria-label="Recomendación de abastecimiento" data-context="'''
        + ('academic' if academic else 'editable') + '" style="border-left-color:' + color + '" data-scenario="' + escape(scenario)
        + '" data-basis="' + escape(basis) + f'" data-demand="{summary["demand"]}">'
        + '<div class="eoq-decision-head"><b>' + escape(context + ' · ' + scenario + ' · '
          + number(summary['demand'], 0) + ' u/año · ' + basis) + '</b><span>' + escape(hint) + '</span></div>'
        + '<div class="eoq-decision-grid">' + body + '</div><p class="eoq-decision-foot" title="'
        + escape(decision_conclusion(summary)) + '">' + escape(note) + '</p></section>')


MANAGEMENT_COMPONENTS = {'Costo integral': 'total', 'Ordenar': 'ordering',
                         'Almacenar': 'holding', 'TRC': 'trc',
                         'Adquisición': 'acquisition', 'Capacidad': 'capacity',
                         'Molde': 'mold'}


def management_controls(exposure=False):
    from management import QUESTION_LABELS
    columns = st.columns([1, 1])
    question = columns[0].selectbox('Pregunta de gerencia', QUESTION_LABELS,
                                   key='sim_management_question', label_visibility='collapsed' if exposure else 'visible')
    component = columns[1].selectbox('Costo a comparar', list(MANAGEMENT_COMPONENTS),
                                    key='sim_management_component', label_visibility='collapsed' if exposure else 'visible')
    return question, component


def render_management(exposure=False, decision_area=None):
    """Sensibilidades académicas aisladas de las cuatro demandas editables."""
    from management import management_analysis, management_conclusion
    with st.container(key='sim_management_panel'):
        question, component_label = management_controls(exposure)
        analysis = management_analysis(question)
        if decision_area is not None:
            with decision_area:
                render_decision(analysis['after'], analysis['parameters'], question,
                                'Anual equivalente', academic=True)
        parameter = analysis['parameter']
        if parameter is None:
            change = 'Parámetros originales'
        else:
            unit = ' %' if parameter == 'p' else ' COP/unidad' if parameter == 'vl' else ' COP/pedido'
            change = (analysis['label'] + ': ' + number(analysis['before_parameter'], 0)
                      + ' → ' + number(analysis['after_parameter'], 0) + unit)
        st.caption(change if exposure else question + ' · G1 original · ' + number(analysis['base']['D'], 0)
                   + ' u/año · Anual equivalente · ' + change)
        costs = relevant_costs(analysis['after'])
        winners = {row['id'] for row in analysis['after_winners']}
        body, comparison_body = [], []
        for item, row, comparison in zip(costs, analysis['after'], analysis['comparison']):
            cells = []
            for field, label in [('ordering', 'Ordenar'), ('holding', 'Almacenar'),
                                 ('trc', 'TRC'), ('total', 'Integral')]:
                amount = comparison['after'][field]
                badge = '<small>Menor TRC</small>' if field == 'trc' and item['minimum'] else ''
                if field == 'total' and row['id'] in winners:
                    badge = '<small>Preferida factible</small>'
                cells.append(f'<td data-field="{field}" data-label="{label} · COP/año" '
                             f'data-value="{amount}" data-before="{comparison["before"][field]}">'
                             + '$ ' + number(amount, 0) + badge + '</td>')
            state = 'current' if row['current_feasible'] and row['feasible'] else 'expanded' if row['feasible'] else 'excluded'
            body.append(f'<tr data-alternative="{row["id"]}" data-eoq="{row["eoq"]}" data-q="{row["Q"]}">'
                        f'<th scope="row" style="border-left:4px solid {COLORS[row["id"]]}">{escape(row["name"])}</th>'
                        + ''.join(cells)
                        + f'<td data-label="Factibilidad" class="eoq-management-status {state}">'
                        + escape(feasibility(row)) + f'<small>{row["positions"]} posiciones</small></td></tr>')
            component = MANAGEMENT_COMPONENTS[component_label]
            delta, percent = comparison['delta'][component], comparison['percent'][component]
            values = [('before', 'Antes', comparison['before'][component]),
                      ('after', 'Después', comparison['after'][component]),
                      ('delta', 'Diferencia', delta), ('percent', 'Variación', percent)]
            comparison_cells = []
            for field, label, value in values:
                displayed = ('—' if value is None else number(value) + ' %') if field == 'percent' else '$ ' + number(value, 0)
                comparison_cells.append(f'<td data-field="{field}" data-label="{label}" data-value="{value if value is not None else ""}">' + displayed + '</td>')
            comparison_body.append(f'<tr data-alternative="{row["id"]}"><th scope="row" '
                                   f'style="border-left:4px solid {COLORS[row["id"]]}">{escape(row["name"])}</th>'
                                   + ''.join(comparison_cells) + '</tr>')
        table_html = '''<style>
          .eoq-management,.eoq-management-comparison{font-size:13px;line-height:1.25;color:#18332f}
          .eoq-management table,.eoq-management-comparison table{width:100%;border-collapse:collapse;background:white;border:1px solid #d9e3dc}
          .eoq-management-comparison table{table-layout:fixed}
          .eoq-management-comparison td,.eoq-management-comparison th{white-space:normal;overflow-wrap:anywhere}
          .eoq-management-comparison th:first-child{width:20%}
          .eoq-management caption,.eoq-management-comparison caption{text-align:left;font-size:15px;font-weight:650;padding-bottom:3px;color:#18332f}
          .eoq-management th,.eoq-management td,.eoq-management-comparison th,.eoq-management-comparison td{padding:3px 8px;border-bottom:1px solid #e3e9e4}
          .eoq-management thead,.eoq-management-comparison thead{background:#edf3ed;font-size:12px}
          .eoq-management th,.eoq-management-comparison th{text-align:left}
          .eoq-management td,.eoq-management-comparison td{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
          .eoq-management-comparison td{white-space:normal}
          .eoq-management small{display:block;font-size:10px;line-height:1.2;font-weight:600}
          .eoq-management td[data-field="trc"]:has(small),.eoq-management td[data-field="total"]:has(small){background:#d8eee6;color:#084d3e;font-weight:650}
          .eoq-management .eoq-management-status{text-align:left;white-space:normal;font-size:12px;font-weight:600}
          .eoq-management-status.current{color:#08634f}.eoq-management-status.expanded{color:#875000}.eoq-management-status.excluded{color:#5c6260}
          .eoq-management-note{font-size:11px;line-height:1.35;margin:4px 0;color:#344a40}
          .eoq-management-conclusion{color:#18332f;background:#edf3ed;border-left:4px solid #087d68;font-size:13px;line-height:1.4;padding:7px 10px;margin:0}
          @media(max-width:760px){
            .eoq-management thead,.eoq-management-comparison thead{display:none}
            .eoq-management table,.eoq-management tbody,.eoq-management tr,.eoq-management th,.eoq-management td,
            .eoq-management-comparison table,.eoq-management-comparison tbody,.eoq-management-comparison tr,.eoq-management-comparison th,.eoq-management-comparison td{display:block}
            .eoq-management caption,.eoq-management-comparison caption{display:block;width:100%;box-sizing:border-box;padding:6px 8px}
            .eoq-management-comparison th:first-child{width:auto}
            .eoq-management tbody th,.eoq-management-comparison tbody th{background:#edf3ed}
            .eoq-management tr,.eoq-management-comparison tr{border-bottom:2px solid #d9e3dc}
            .eoq-management td,.eoq-management-comparison td{display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;white-space:normal}
            .eoq-management td:before,.eoq-management-comparison td:before{content:attr(data-label);text-align:left;font-weight:500}
            .eoq-management small{width:100%;text-align:right}
          }
        </style><section class="eoq-management" aria-label="Costos de preguntas de gerencia">
          <table class="eoq-management-costs"><caption>Costos anuales · ''' + escape(question) + ''' · COP/año</caption>
            <thead><tr><th>Alternativa</th><th>Ordenar</th><th>Almacenar</th><th>TRC</th><th>Costo integral</th><th>Factibilidad</th></tr></thead>
            <tbody>''' + ''.join(body) + '''</tbody></table>
          <p class="eoq-management-note"><b>TRC = ordenar + almacenar.</b> Ordenar incluye fletes una sola vez.
          Integral = adquisición + TRC + capacidad + molde; incluye la ampliación completa cuando se necesita.</p>
        </section>'''
        comparison_html = ('<section class="eoq-management-comparison" aria-label="Antes y después">'
                '<table><caption>Antes G1 vs. Después · ' + escape(component_label) + ' · COP/año</caption>'
                '<thead><tr><th>Alternativa</th><th>Antes · G1</th><th>Después</th><th>Diferencia</th><th>Variación</th></tr></thead>'
                '<tbody>' + ''.join(comparison_body) + '</tbody></table>'
                '<p class="eoq-management-note">Diferencia = después − antes; porcentaje respecto a G1. — indica costo base cero.</p></section>')
        st.html(table_html.split('</style>', 1)[0] + '</style>')
        def draw_question_inventory():
            chart = inventory_chart(analysis['after'], analysis['parameters'], False,
                                    height=190 if exposure else 270)
            if exposure:
                chart.update_layout(margin=dict(l=40, r=20, t=35, b=60))
            st.plotly_chart(chart,
                            key='sim_management_inventory', width='stretch',
                            config={'displaylogo': False,
                                    'toImageButtonOptions': {'filename': 'gerencia_eoq'}})
        if exposure:
            inventory, comparison_view = st.columns(2, gap='medium')
            with inventory:
                draw_question_inventory()
            with comparison_view:
                st.html(comparison_html)
            st.html(table_html)
        else:
            draw_question_inventory()
            st.html(table_html)
            st.html(comparison_html)
        st.html('<p class="eoq-management-conclusion">' + escape(management_conclusion(analysis, compact=exposure)) + '</p>')


def demonstration():
    """Configuración editable de demostración; no cambia BASE ni la demanda G1."""
    for i,factor in enumerate([70,100,130,160]):
        st.session_state['sim_d'+str(i)] = float(original_values()['D'])*factor/100
        st.session_state['sim_factor'+str(i)] = float(factor)


def inventory_chart(rows, p, partial, height=270):
    chart = go.Figure()
    for row in rows:
        x,y = sawtooth(row,partial)
        chart.add_trace(go.Scatter(x=x,y=y,mode='lines',name=row['name'],meta=feasibility(row),line=dict(color=COLORS[row['id']],width=3),hovertemplate='%{x:.3f} meses · %{y:,.2f} unidades<br>%{meta}<extra>%{fullData.name}</extra>'))
    chart.add_hline(y=p['positions']*p['units'],line_dash='dot',annotation_text='Capacidad actual')
    chart.add_hline(y=max(p['positions']+p['rentPositions'],p['positions']+p['expandPositions'])*p['units'],line_dash='dash',annotation_text='Capacidad máxima')
    chart.update_layout(title='Inventario durante 12 meses',xaxis=dict(title='Meses',range=[0,12]),yaxis_title='Unidades',height=height,font=dict(size=14),uirevision='inventory',legend=dict(orientation='h',font=dict(size=12),yref='container',y=0,yanchor='bottom'),margin=dict(l=40,r=20,t=45,b=85))
    return chart


def composition_chart(rows, components):
    chart = go.Figure()
    for row in rows:
        amounts=[row[c] for c in components]
        chart.add_trace(go.Bar(name=row['name'],x=[COMPONENTS[c] for c in components],y=[v/1e6 for v in amounts],marker_color=COLORS[row['id']],text=[short_money(v) for v in amounts],textangle=0,textfont=dict(size=12),textposition='outside',cliponaxis=False,customdata=[[money(v),feasibility(row)] for v in amounts],hovertemplate='%{x}<br>%{customdata[0]}<br>%{customdata[1]}<extra>%{fullData.name}</extra>'))
    chart.update_layout(title='Composición · componentes seleccionados',barmode='group',yaxis_title='Millones de COP/año',height=220,font=dict(size=14),legend=dict(orientation='h'),margin=dict(l=40,r=20,t=45,b=60),uniformtext=dict(minsize=11,mode='hide'))
    return chart


def render_simulator():
    # Widgets de parámetros se montan incluso dentro del desplegable cerrado:
    # Streamlit no elimina sus valores al cambiar de pestaña ejecutiva.
    if 'sim_D' not in st.session_state:
        reset()
        demonstration()
        st.session_state.setdefault('sim_scenario','Base G1')
    header=st.columns([1,1,2])
    exposure = header[0].toggle('Modo exposición',key='sim_exposure')
    if exposure:
        with header[1]:
            controls=st.popover('Editar parámetros')
        main=st.container(key='sim_executive')
        st.html('''<style>
          .st-key-sim_executive [data-testid="stMetricValue"]{font-size:1.35rem}
          .st-key-sim_executive,.st-key-sim_executive [data-testid="stVerticalBlock"]{gap:6px}
          .st-key-sim_executive [role="tabpanel"]{padding-top:8px}
        </style>''')
    else:
        st.subheader('Simulador de escenarios EOQ')
        controls,main=st.columns([1,3],gap='large')
    with controls:
        p=parameters()
        st.button('Configurar demostración',on_click=demonstration,help='Solo las cuatro demandas: 70 %, 100 %, 130 % y 160 % de G1.')
        basis=st.radio('Criterio de costos',['Anual equivalente · modelo original','Año observado · pedidos emitidos'],key='sim_basis')
        partial=st.checkbox('Último pedido local parcial',key='sim_partial')
        st.caption('Reposición instantánea; contenedores completos. Sin cambios al modelo financiero original.')
        st.button('Comparar escenarios',on_click=lambda:st.session_state.update(sim_selector='Comparar todas las alternativas'))
    with main:
        management_active = exposure and st.session_state.get('sim_exec_tab') == 'Preguntas de gerencia'
        manual_decision = None
        if management_active:
            with header[2]:
                selector_controls, manual_controls = st.columns(2)
                selectors = selector_controls.popover('Demandas del simulador', help='Las cuatro demandas se conservan aparte. Las preguntas académicas siempre parten de G1 original.')
                manual_decision = manual_controls.popover('Decisión de mis parámetros')
        else:
            selectors = header[2] if exposure else st.container()
        with selectors:
            top=st.columns(2)
            selected=top[0].selectbox('Alternativa',['Comparar todas las alternativas',*NAMES.values()],key='sim_selector')
            scenario=top[1].selectbox('Escenario de inventario',SCENARIOS,key='sim_scenario')
        decision_area=st.container(key='sim_decision')
        try:
            results={name:evaluate(p,st.session_state['sim_d'+str(i)],basis.startswith('Año observado'),partial) for i,name in enumerate(SCENARIOS)}
            simulation_error=None
        except ValueError as error:
            simulation_error=str(error)
        if exposure:
            tabs=st.tabs(['Inventario','Costos','Ahorro comparativo','Preguntas de gerencia'],key='sim_exec_tab',on_change='rerun')
            if tabs[3].open:
                if manual_decision is not None:
                    with manual_decision:
                        st.caption('Análisis separado: usa tus parámetros y la demanda seleccionada del simulador. No modifica el G1 de las preguntas académicas.')
                        if simulation_error:
                            st.warning(simulation_error)
                        else:
                            render_decision(results[scenario],p,scenario,basis)
                with tabs[3]:
                    render_management(exposure=True,decision_area=decision_area)
                st.caption('Simulador · '+SIMULATOR_VERSION+' · '+st.session_state['sim_management_question']+' · G1 original · Anual equivalente')
                return
            # Mantener los widgets aun al navegar: Streamlit conserva la pregunta
            # y el componente seleccionado, sin alterar las demandas del simulador.
            with controls:
                with st.expander('Preguntas de gerencia · G1 independiente'):
                    management_controls()
        if simulation_error:
            with decision_area:
                st.error(simulation_error)
            return
        rows=results[scenario]
        with decision_area:
            render_decision(rows,p,scenario,basis)
        visible=rows if selected.startswith('Comparar') else [r for r in rows if r['name']==selected]
        current,ranked,excluded=recommendations(rows)
        best=ranked[0] if ranked else None
        reference=visible[0] if len(visible)==1 else best or rows[0]
        local=rows[2]
        gain,percent=savings(best,local) if best else (0,None)

        def economic_metrics(saving=False):
            columns=st.columns(4)
            columns[0].metric('Factible con capacidad actual',current[0]['name'] if current else 'Ninguna')
            columns[1].metric('Mejor permitiendo ampliar',best['name'] if best else 'Ninguna',help=feasibility(best) if best else None)
            if saving:
                columns[2].metric('Ahorro vs. local',short_money(gain) if best else '—',help=money(gain))
                columns[3].metric('Ahorro porcentual',number(percent)+' %' if percent is not None else '—')
            else:
                columns[2].metric('Costo de la mejor opción',short_money(best['total']) if best else '—',help=money(best['total']) if best else None)
                columns[3].metric('Condición de esa opción',feasibility(best) if best else 'No factible')

        def draw_inventory():
            labels=['Demanda · u/año','Lote · unidades','Pedidos emitidos / D÷Q','Inventario promedio']
            values=[number(reference['demand'],0),number(reference['Q']),str(reference['count'])+' / '+number(reference['theoretical'],3),number(reference['average'])]
            if exposure:
                st.caption(reference['name']+' · '+' · '.join(label+': '+value for label,value in zip(labels[1:],values[1:])))
            else:
                columns=st.columns(4)
                for col,label,value in zip(columns,labels,values):
                    col.metric(label,value,help=reference['name'])
            chart=inventory_chart(visible,p,partial,height=190 if exposure else 270)
            if exposure:
                chart.update_layout(margin=dict(l=40,r=20,t=35,b=60))
            st.plotly_chart(chart,key='sim_inventory',width='stretch',config={'displaylogo':False,'toImageButtonOptions':{'filename':'inventario_eoq'}})
            render_relevant_costs(rows,scenario,basis.startswith('Año observado'))
            inventory_note = 'Reposición instantánea; el último ciclo puede ser incompleto, sin emitir otro pedido al mes 12.'
            if exposure:
                st.caption(inventory_note)
            else:
                st.info(' · '.join(r['name']+': '+feasibility(r)+f" ({r['positions']} posiciones)" for r in visible)+'. '+inventory_note)

        def draw_costs():
            if not exposure:
                economic_metrics()
            view=st.radio('Visualización de costos',['Costo total','Composición'],horizontal=True,key='sim_cost_view',label_visibility='collapsed')
            if view=='Composición':
                components=st.multiselect('Componentes a analizar',list(COMPONENTS),default=[c for c in COMPONENTS if c!='acquisition'],format_func=COMPONENTS.get,key='sim_components')
                if components:
                    st.plotly_chart(composition_chart(visible,components),key='sim_composition',width='stretch',config={'displaylogo':False})
                else: st.info('Seleccione al menos un componente.')
                st.caption('La escala se ajusta a los componentes seleccionados. Adquisición se puede añadir; seleccione un único componente para analizarlo individualmente.')
            else:
                # La referencia local se mantiene para el tooltip aunque se filtre la alternativa.
                st.plotly_chart(comparison_chart(results,exposure=exposure,alternative=selected),key='sim_comparison',width='stretch',config={'displaylogo':False})
            st.caption('Capacidad actual: '+(current[0]['name'] if current else 'ninguna')+'. Con capacidad adicional: '+(best['name']+' · '+short_money(best['total'])+' · '+feasibility(best) if best else 'ninguna')+'. Excluidas: '+(', '.join(r['name'] for r in excluded) or 'ninguna')+'.')

        def draw_savings():
            if not exposure:
                economic_metrics(saving=True)
            st.plotly_chart(comparison_chart(results,saving=True,exposure=exposure,alternative=selected),key='sim_savings',width='stretch',config={'displaylogo':False})
            if not exposure:
                st.info(f"{scenario}: ahorro frente al local {short_money(gain)} ({number(percent)} %)" if percent is not None else 'No hay una recomendación factible.')
            st.caption('Puntos: ahorro potencial sujeto a ampliar capacidad. Rayas: ahorro no realizable por inviabilidad. Positivo = ahorro; negativo = sobrecosto. '+('La referencia local también es inviable.' if not local['feasible'] else ''))

        if exposure:
            for tab,draw in zip(tabs,[draw_inventory,draw_costs,draw_savings]):
                if tab.open:
                    with tab: draw()
            # Detalles y descargas se ofrecen en modo completo; no alargan la vista ejecutiva.
        else:
            draw_inventory()
            draw_costs()
            draw_savings()
            with st.expander('Preguntas de gerencia'):
                render_management()
            table=[]
            for name,items in results.items():
                now,expanded,_=recommendations(items)
                for r in items:
                    absolute,percentage=savings(r,items[2])
                    table.append({'Escenario':name,'Alternativa':r['name'],'Mejor con capacidad actual':'Sí' if now and r in now and abs(r['total']-now[0]['total'])<.01 else '', 'Recomendación':'Mejor considerando ampliación' if expanded and r in expanded and abs(r['total']-expanded[0]['total'])<.01 else '', 'Demanda · u/año':r['demand'],'EOQ · u':r['eoq'],'Lote · u':r['Q'],'Pedidos emitidos':r['count'],'Frecuencia D/Q':r['theoretical'],'Periodo · días':r['cycle'],'Inventario promedio · u':r['average'],'Promedio observado · u':r['actual_average'],'Último pedido · u':r['final_lot'],'Inventario final · u':r['closing'],'Adquisición · COP':r['acquisition'],'Ordenar sin flete · COP':r['ordering'],'Flete · COP':r['freight'],'Mantenimiento · COP':r['holding'],'Capacidad · COP':r['capacity'],'Molde a cargo · COP':r['mold'],'Total anual · COP':r['total'],'Posiciones requeridas':r['positions'],'Bodega':r['chosen'],'Factibilidad':feasibility(r),'Ahorro vs. local · COP':absolute,'Ahorro vs. local · %':percentage})
            with st.expander('Tabla de los cuatro escenarios'):
                frame=pd.DataFrame(table)
                formats={c:money if 'COP' in c else number for c in frame if pd.api.types.is_numeric_dtype(frame[c])}
                st.dataframe(frame.style.format(formats).apply(lambda r:['background-color: #d8eee6' if r['Recomendación'] else '' for _ in r],axis=1),hide_index=True,width='stretch')
            with st.expander('Conclusiones de los cuatro escenarios'):
                for name,items in results.items():st.write(conclusion(name,items))
            output=io.StringIO();writer=csv.DictWriter(output,fieldnames=table[0].keys());writer.writeheader();writer.writerows(table)
            st.download_button('Descargar comparación CSV',output.getvalue().encode('utf-8-sig'),'escenarios_eoq.csv','text/csv',key='sim_download')
        st.caption('Simulador · '+SIMULATOR_VERSION+' · '+scenario+' · '+basis)
