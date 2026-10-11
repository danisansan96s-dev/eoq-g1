"""Simulador independiente; datos originales leídos del modelo JavaScript del taller."""
import ast
import csv
import io
import math
import re
from pathlib import Path

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
    st.button('Aplicar cambios',width='stretch',help='Los cambios ya se recalculan automáticamente.')
    for key in p:
        p[key] = st.session_state['sim_'+key]
    return p


def feasibility(row):
    """Clasificación operativa; considera también el límite anual del proveedor."""
    if not row['supply'] or not row['feasible']:
        return 'No factible'
    return 'Factible actualmente' if row['current_feasible'] else 'Viable con ampliación'


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
SIMULATOR_VERSION = '2026-10-11.3'


def demonstration():
    """Configuración editable de demostración; no cambia BASE ni la demanda G1."""
    for i,factor in enumerate([70,100,130,160]):
        st.session_state['sim_d'+str(i)] = float(original_values()['D'])*factor/100
        st.session_state['sim_factor'+str(i)] = float(factor)


def inventory_chart(rows, p, partial, height=270):
    chart = go.Figure()
    for row in rows:
        x,y = sawtooth(row,partial)
        chart.add_trace(go.Scatter(x=x,y=y,mode='lines',name=row['name']+' · '+feasibility(row),line=dict(color=COLORS[row['id']],width=3),hovertemplate='%{x:.3f} meses · %{y:,.2f} unidades<extra>%{fullData.name}</extra>'))
    chart.add_hline(y=p['positions']*p['units'],line_dash='dot',annotation_text='Capacidad actual')
    chart.add_hline(y=max(p['positions']+p['rentPositions'],p['positions']+p['expandPositions'])*p['units'],line_dash='dash',annotation_text='Capacidad máxima')
    chart.update_layout(title='Inventario durante 12 meses',xaxis=dict(title='Meses',range=[0,12]),yaxis_title='Unidades',height=height,font=dict(size=14),uirevision='inventory',legend=dict(orientation='h',font=dict(size=12)),margin=dict(l=40,r=20,t=45,b=40))
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
    header=st.columns([1,3])
    exposure = header[0].toggle('Modo exposición',key='sim_exposure')
    if exposure:
        with header[1]:
            controls=st.popover('Editar parámetros')
        main=st.container(key='sim_executive')
        st.html('<style>.st-key-sim_executive [data-testid="stMetricValue"]{font-size:1.35rem}</style>')
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
        top=st.columns(2)
        selected=top[0].selectbox('Alternativa',['Comparar todas las alternativas',*NAMES.values()],key='sim_selector')
        scenario=top[1].selectbox('Escenario de inventario',SCENARIOS,key='sim_scenario')
        try:
            results={name:evaluate(p,st.session_state['sim_d'+str(i)],basis.startswith('Año observado'),partial) for i,name in enumerate(SCENARIOS)}
        except ValueError as error:
            st.error(str(error));return
        rows=results[scenario]
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
            columns=st.columns(4)
            for col,label,value in zip(columns,['Demanda · u/año','Lote · unidades','Pedidos emitidos / D÷Q','Inventario promedio'],[number(reference['demand'],0),number(reference['Q']),str(reference['count'])+' / '+number(reference['theoretical'],3),number(reference['average'])]):
                col.metric(label,value,help=reference['name'])
            st.plotly_chart(inventory_chart(visible,p,partial),key='sim_inventory',width='stretch',config={'displaylogo':False,'toImageButtonOptions':{'filename':'inventario_eoq'}})
            st.info(' · '.join(r['name']+': '+feasibility(r)+f" ({r['positions']} posiciones)" for r in visible)+'. Reposición instantánea; el último ciclo puede ser incompleto, sin emitir otro pedido al mes 12.')

        def draw_costs():
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
            economic_metrics(saving=True)
            st.plotly_chart(comparison_chart(results,saving=True,exposure=exposure,alternative=selected),key='sim_savings',width='stretch',config={'displaylogo':False})
            st.info(f"{scenario}: ahorro frente al local {short_money(gain)} ({number(percent)} %)" if percent is not None else 'No hay una recomendación factible.')
            st.caption('Puntos: ahorro potencial sujeto a ampliar capacidad. Rayas: ahorro no realizable por inviabilidad. Positivo = ahorro; negativo = sobrecosto. '+('La referencia local también es inviable.' if not local['feasible'] else ''))

        if exposure:
            tabs=st.tabs(['Inventario','Costos','Ahorro comparativo'],key='sim_exec_tab',on_change='rerun')
            for tab,draw in zip(tabs,[draw_inventory,draw_costs,draw_savings]):
                if tab.open:
                    with tab: draw()
            # Detalles y descargas se ofrecen en modo completo; no alargan la vista ejecutiva.
        else:
            draw_inventory()
            draw_costs()
            draw_savings()
            table=[]
            for name,items in results.items():
                now,expanded,_=recommendations(items)
                for r in items:
                    absolute,percentage=savings(r,items[2])
                    table.append({'Escenario':name,'Alternativa':r['name'],'Mejor con capacidad actual':'Sí' if now and r in now and abs(r['total']-now[0]['total'])<.01 else '', 'Recomendación':'Mejor considerando ampliación' if expanded and r in expanded and abs(r['total']-expanded[0]['total'])<.01 else '', 'Demanda · u/año':r['demand'],'EOQ · u':r['eoq'],'Lote · u':r['Q'],'Pedidos emitidos':r['count'],'Frecuencia D/Q':r['theoretical'],'Periodo · días':r['cycle'],'Inventario promedio · u':r['average'],'Promedio observado · u':r['actual_average'],'Último pedido · u':r['final_lot'],'Inventario final · u':r['closing'],'Adquisición · COP':r['acquisition'],'Ordenar sin flete · COP':r['ordering'],'Flete · COP':r['freight'],'Mantenimiento · COP':r['holding'],'Capacidad · COP':r['capacity'],'Molde a cargo · COP':r['mold'],'Total anual · COP':r['total'],'Posiciones requeridas':r['positions'],'Bodega':r['chosen'],'Factibilidad':feasibility(r),'Ahorro vs. local · COP':absolute,'Ahorro vs. local · %':percentage})
            import pandas as pd
            with st.expander('Tabla de los cuatro escenarios'):
                frame=pd.DataFrame(table)
                formats={c:money if 'COP' in c else number for c in frame if pd.api.types.is_numeric_dtype(frame[c])}
                st.dataframe(frame.style.format(formats).apply(lambda r:['background-color: #d8eee6' if r['Recomendación'] else '' for _ in r],axis=1),hide_index=True,width='stretch')
            with st.expander('Conclusiones de los cuatro escenarios'):
                for name,items in results.items():st.write(conclusion(name,items))
            output=io.StringIO();writer=csv.DictWriter(output,fieldnames=table[0].keys());writer.writeheader();writer.writerows(table)
            st.download_button('Descargar comparación CSV',output.getvalue().encode('utf-8-sig'),'escenarios_eoq.csv','text/csv',key='sim_download')
        st.caption('Simulador · '+SIMULATOR_VERSION+' · '+scenario+' · '+basis)
