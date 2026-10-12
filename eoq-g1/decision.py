"""Una recomendación compartida por las vistas del simulador, sin nuevas fórmulas."""


def _tied_minimum(rows, field):
    if not rows:
        return []
    minimum = min(row[field] for row in rows)
    return [row for row in rows if abs(row[field] - minimum) < .01]


def decision_summary(rows, p, scenario, basis, context='Simulador editable'):
    """Resume las mismas filas evaluadas que utilizan gráficos y tablas.

    El ranking integral excluye opciones inviables. Los mínimos matemáticos
    conservan todas las alternativas y se informan por separado. No cambia las
    filas, parámetros, criterio temporal ni estado de la aplicación.
    """
    from simulator import feasibility, money, recommendations, relevant_costs, savings

    current, ranked, _ = recommendations(rows)
    current_winners = _tied_minimum(current, 'total')
    winners = _tied_minimum(ranked, 'total')
    best = winners[0] if winners else None
    local = next((row for row in rows if row['id'] == 'local'), None)
    saving, saving_percent = savings(best, local) if best is not None and local is not None else (None, None)
    relevant = relevant_costs(rows)
    minimum_trc = [row for row, cost in zip(rows, relevant) if cost['minimum']]
    chosen_capacity = None
    if best is None:
        status = 'No factible'
        condition = 'Sin opción factible con la capacidad y el abastecimiento disponibles.'
        capacity_text = condition
    else:
        status = feasibility(best)
        chosen_capacity = p['positions']
        if best['chosen'] == 'Alquiler':
            chosen_capacity += p['rentPositions']
        elif best['chosen'] == 'Ampliación':
            chosen_capacity += p['expandPositions']
        capacity_text = (f"{best['positions']} posiciones requeridas; {p['positions']} actuales; "
                         f"{chosen_capacity} disponibles en bodega {best['chosen'].lower()}.")
        if best['current_feasible']:
            condition = 'Operable con capacidad actual.'
        else:
            action = 'contratar el alquiler adicional' if best['chosen'] == 'Alquiler' else 'habilitar la ampliación'
            condition = (f'Condicionada a {action}; su costo completo de '
                         f"{money(best['capacity'])}/año ya está incluido.")
    return dict(current_winners=current_winners, winners=winners, best=best,
                local=local, saving=saving, saving_percent=saving_percent,
                lowest_integral=_tied_minimum(rows, 'total'), minimum_trc=minimum_trc,
                context=context, scenario=scenario, basis=basis,
                demand=rows[0]['demand'] if rows else None,
                capacity_text=capacity_text, chosen_capacity=chosen_capacity,
                status=status, condition=condition,
                local_reference_feasible=bool(local is not None and local['feasible']),
                noopts=best is None)


def decision_conclusion(summary):
    """Explica el ranking integral y las restricciones con los resultados activos."""
    if summary['noopts']:
        return ('Ninguna alternativa satisface las restricciones operativas. '
                'Los mínimos matemáticos de costo no constituyen una recomendación viable.')
    names = ' / '.join(row['name'] for row in summary['winners'])
    text = f'{names} ofrece el menor costo integral entre las alternativas factibles. '
    text += summary['condition'] + ' '
    excluded_minimum = [row for row in summary['lowest_integral'] if not row['feasible']]
    if excluded_minimum:
        excluded_names = ' / '.join(row['name'] for row in excluded_minimum)
        text += f'{excluded_names} tiene el menor costo calculado, pero se excluye por inviabilidad. '
    minimum_trc_ids = {row['id'] for row in summary['minimum_trc']}
    winner_ids = {row['id'] for row in summary['winners']}
    if minimum_trc_ids != winner_ids:
        trc_names = ' / '.join(row['name'] for row in summary['minimum_trc'])
        text += f'El menor TRC corresponde a {trc_names}; no incluye adquisición, capacidad ni molde. '
    else:
        text += 'La recomendación considera adquisición, TRC, capacidad y molde. '
    if summary['local'] is not None and not summary['local_reference_feasible']:
        text += 'La comparación con el proveedor local usa una referencia inviable, no una opción realizable. '
    return text.strip()
