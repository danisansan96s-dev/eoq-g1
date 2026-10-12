"""Sensibilidades independientes del caso G1, sin modificar el simulador editable."""

from simulator import (evaluate, feasibility, money, number, original_values,
                       recommendations, relevant_costs)


QUESTION_LABELS = ['Escenario original', 'Pregunta 1', 'Pregunta 2', 'Pregunta 3']
_QUESTIONS = {
    'Escenario original': ('Base G1 · parámetros originales', None, None),
    'Pregunta 1': ('Precio del proveedor local', 'vl', 99000),
    'Pregunta 2': ('Flete internacional del contenedor de 20 pies', 'f20', 10000000),
    'Pregunta 3': ('Aporte del proveedor a la financiación del molde', 'p', 50),
}
COMPONENTS = ['acquisition', 'ordering', 'holding', 'trc', 'capacity', 'mold', 'total']
_COMPONENT_LABELS = {
    'acquisition': 'adquisición', 'ordering': 'ordenar (fletes incluidos)',
    'holding': 'almacenar', 'capacity': 'capacidad', 'mold': 'molde',
}


def _components(row, relevant):
    # Ordenar incluye todos los costos por pedido del modelo original una vez.
    # TRC conserva esa misma clasificación; el total integral procede de evaluate.
    return {component: relevant[component] if component in ['ordering', 'holding', 'trc']
            else row[component] for component in COMPONENTS}


def _winners(rows):
    _, ranked, _ = recommendations(rows)
    return [row for row in ranked if abs(row['total'] - ranked[0]['total']) < .01]


def management_analysis(question):
    """Aplica una sola variación sobre G1 con el criterio anual equivalente.

    No consulta ni escribe session_state: demandas y parámetros editables de los
    cuatro escenarios son análisis separados. Cada llamada vuelve a leer G1.
    Los porcentajes comparan cada componente con el mismo componente de G1;
    si su costo base es cero el porcentaje no se define.
    """
    if question not in _QUESTIONS:
        raise ValueError('Seleccione Escenario original, Pregunta 1, Pregunta 2 o Pregunta 3.')
    label, parameter, value = _QUESTIONS[question]
    base = original_values()
    parameters = base.copy()
    if parameter is not None:
        parameters[parameter] = value
    before = evaluate(base, base['D'])
    after = evaluate(parameters, base['D'])
    comparison = []
    for before_row, after_row, before_relevant, after_relevant in zip(
            before, after, relevant_costs(before), relevant_costs(after)):
        before_costs = _components(before_row, before_relevant)
        after_costs = _components(after_row, after_relevant)
        delta = {key: after_costs[key] - before_costs[key] for key in COMPONENTS}
        percent = {key: delta[key] / before_costs[key] * 100 if before_costs[key] else None
                   for key in COMPONENTS}
        comparison.append(dict(id=before_row['id'], name=before_row['name'],
                               before=before_costs, after=after_costs, delta=delta,
                               percent=percent, before_status=feasibility(before_row),
                               after_status=feasibility(after_row)))
    return dict(question=question, label=label, parameter=parameter,
                before_parameter=base[parameter] if parameter else None,
                after_parameter=parameters[parameter] if parameter else None,
                base=base, parameters=parameters, before=before, after=after,
                comparison=comparison, before_winners=_winners(before),
                after_winners=_winners(after))


def management_conclusion(analysis):
    """Conclusión calculada: preferencia integral, restricciones y efecto del cambio."""
    before_winners = analysis['before_winners']
    after_winners = analysis['after_winners']
    before_names = ' / '.join(row['name'] for row in before_winners) or 'ninguna opción factible'
    after_names = ' / '.join(row['name'] for row in after_winners) or 'ninguna opción factible'
    changed = {row['id'] for row in before_winners} != {row['id'] for row in after_winners}
    text = ('Cambia la preferencia integral' if changed else 'Se conserva la preferencia integral')
    text += f': {before_names} → {after_names}. '
    if after_winners:
        best = after_winners[0]
        text += f"Costo integral recomendado: {money(best['total'])}/año. "
        _, ranked, _ = recommendations(analysis['after'])
        next_best = next((row for row in ranked if row not in after_winners), None)
        if next_best:
            saving = next_best['total'] - best['total']
            percent = saving / next_best['total'] * 100 if next_best['total'] else None
            text += f"Ventaja frente a {next_best['name']}: {money(saving)}/año"
            text += f' ({number(percent)} %). ' if percent is not None else '. '
        if not best['current_feasible']:
            text += 'Condicionada a ampliar capacidad; el costo completo ya está incluido. '
    changes = []
    for item in analysis['comparison']:
        affected = [label for key, label in _COMPONENT_LABELS.items() if abs(item['delta'][key]) >= .01]
        if affected:
            changes.append(item['name'] + ': ' + ', '.join(affected))
    text += 'Cambian ' + '; '.join(changes) + '. ' if changes else 'No cambia ningún costo. '
    states_changed = [item for item in analysis['comparison'] if item['before_status'] != item['after_status']]
    if states_changed:
        text += 'Viabilidad: ' + '; '.join(item['name'] + ': ' + item['before_status'] + ' → ' + item['after_status'] for item in states_changed) + '. '
    else:
        text += 'La viabilidad operativa se conserva. '
    excluded = [row for row in analysis['after'] if not row['feasible']]
    if excluded:
        text += 'Excluidas: ' + '; '.join(
            row['name'] + (f" ({row['positions']} > {row['available']} posiciones)"
                           if row['positions'] > row['available'] else ' (capacidad anual del proveedor)')
            for row in excluded) + '. '
    before_rows = {row['id']: row for row in analysis['before']}
    parameter = analysis['parameter']
    if parameter == 'vl':
        local = next(row for row in analysis['after'] if row['id'] == 'local')
        text += f"El EOQ local pasa de {number(before_rows['local']['eoq'])} a {number(local['eoq'])} unidades."
    elif parameter == 'f20':
        container = next(row for row in analysis['after'] if row['id'] == '20')
        text += f"El EOQ de referencia de 20 pies pasa de {number(before_rows['20']['eoq'])} a {number(container['eoq'])}; el lote real permanece en {number(container['Q'], 0)} unidades."
    elif parameter == 'p':
        text += 'El aporte del proveedor reduce el molde asumido por la empresa; no es interés y no cambia EOQ, inventarios ni TRC.'
    else:
        text += 'Análisis anual equivalente de los parámetros originales G1.'
    return text
