/* El modo exposición utiliza el mismo estado y modelo que el análisis. */
(function () {
  'use strict';
  const view = document.getElementById('presentation-view');
  const titles = ['Datos y modelo', 'EOQ y lotes reales', 'Capacidad',
    'Decisión económica', 'Sensibilidad y puntos de equilibrio', 'Preguntas de gerencia'];
  let active = false, step = 0, selectedSource = '20';

  const shortMoney = value => Number.isFinite(value) ? money(value / 1e6) + ' M' : '—';
  const sourceName = row => `<span class="source-tag" style="--source:${colors[['20','40','local'].indexOf(row.id)]}">${row.name}</span>`;
  const stats = values => `<div class="exposure-stats">${values.map(([label,value]) =>
    `<div><small>${label}</small><strong>${value}</strong></div>`).join('')}</div>`;
  const conclusion = text => `<p class="exposure-conclusion" aria-live="polite">${text}</p>`;

  function decisionText(model) {
    if (!model.ranked.length) return 'Ninguna alternativa atiende toda la demanda con la capacidad disponible.';
    if (model.winners.length > 1) return `Empate: ${winner(model)} tienen el menor costo anual y son físicamente factibles.`;
    const best = model.ranked[0], second = model.ranked[1];
    return `Conviene ${best.name} con ${best.chosen.name.toLowerCase()}: ${money(best.total)} al año${second ? `, ${money(second.total-best.total)} menos que ${second.name}` : '; es la única fuente factible'}.`;
  }

  function fivePolicies(model) {
    const policies = [];
    for (const row of model.rows.slice(0,2)) {
      const actual = row.configs[0];
      policies.push({...row, policy:row.name+' · actual', config:actual,
        feasible:actual.feasible, reason:actual.feasible?'Factible':`Necesita ${row.positions}; dispone de ${actual.positions}`,
        total:row.acquisition+row.trc});
      const additions = row.configs.slice(1).filter(c=>c.feasible).sort((a,b)=>a.cost-b.cost);
      const config = additions[0];
      const required = !actual.feasible;
      policies.push({...row, policy:row.name+' · adicional', config,
        feasible:required&&!!config, reason:!required?'No necesaria':config?config.name:
          `Necesita ${row.positions}; máximo ${Math.max(...row.configs.slice(1).map(c=>c.positions))}`,
        total:config?row.acquisition+row.trc+config.cost:null});
    }
    const local = model.rows[2];
    policies.push({...local,policy:'Local · EOQ',config:local.chosen,
      reason:local.feasible?local.chosen.name:!local.supply?'Capacidad anual insuficiente':'EOQ no cabe'});
    return policies;
  }

  function content(model) {
    const [a,b,local] = model.rows;
    const best = model.ranked[0], next = model.ranked[1];
    if (step === 0) {
      return stats([['Demanda constante',num(state.D,0)+' unidades/año'],
        ['Precios de compra',money(state.vi)+' import. / '+money(state.vl)+' local'],
        ['Tasa anual activa',num(model.r*100)+'%']])+
        `<div class="exposure-grid"><div class="exposure-card"><h3>Datos que determinan el EOQ</h3>${table(
          ['Fuente','A · COP/pedido','v × r · COP/unidad/año'],
          model.rows.map(row=>[sourceName(row),money(row.A),money(row.v*model.r)]))}
          <p class="exposure-assumptions">Demanda constante dentro del escenario · Una fuente de abastecimiento · Sin faltantes.</p></div>
        <div class="exposure-card"><h3>Clasificación compacta</h3><dl class="cost-classification">
          <div><dt>Adquisición</dt><dd>v × D; v también determina v × r.</dd></div>
          <div><dt>Pedidos</dt><dd>A × D/Q; costos por importación o pedido local.</dd></div>
          <div><dt>Mantenimiento</dt><dd>v × r × Q/2; r ${state.rMode==='direct'?'directa':'por componentes'}.</dd></div>
          <div><dt>Capacidad y molde</dt><dd>Costo anual completo de bodega; molde local ${money(local.mold)}.</dd></div>
          <div><dt>Fuera del comparativo</dt><dd>Precio de venta y publicidad.</dd></div></dl></div></div>`+
          conclusion(`El escenario atiende ${num(state.D,0)} unidades/año; ${model.ranked.length} de las ${model.rows.length} fuentes son físicamente factibles.`);
    }
    if (step === 1) {
      const row = model.rows.find(x=>x.id===selectedSource);
      const interpretation = row.id==='local'
        ? `El local usa su EOQ: ${num(row.eoq)} unidades; TRC mínimo ${money(row.minTRC)} al año.`
        : row.eoq>0 ? `${row.name}: el lote se desvía ${num(row.deltaPct)}% del EOQ; el TRC aumenta ${num(row.penaltyPct)}% (${money(row.penalty)} al año).`
        : `${row.name}: A es cero; el mínimo económico es un límite Q→0. Se mantiene el lote completo y su TRC es ${money(row.trc)}.`;
      return stats([['EOQ · '+row.name,num(row.eoq)+' unidades'],['Lote utilizado',num(row.Q)+' unidades'],
        ['TRC del lote',shortMoney(row.trc)+'/año']])+
        `<div class="exposure-grid"><div class="exposure-card"><h3>Óptimo económico y política real</h3>${table(
          ['Fuente','EOQ','Lote','Δ TRC'],model.rows.map(x=>[sourceName(x),num(x.eoq),num(x.Q),x.id==='local'?'Óptimo':num(x.penaltyPct)+'%']))}
          <div class="formula">Q* = √(2 × A × D / (v × r))</div>
          <p class="exposure-detail">A = ${money(row.A)} · D = ${num(state.D,0)} · v = ${money(row.v)} · r = ${num(model.r*100)}%</p></div>
          <div class="exposure-card"><div class="exposure-source-controls" aria-label="Fuente para curvas">${model.rows.map(x=>
            `<button data-exposure-source="${x.id}" aria-pressed="${x.id===selectedSource}" style="--source:${colors[model.rows.indexOf(x)]}">${x.name}</button>`).join('')}</div>
            <div id="exposure-trc" class="chart"></div></div></div>`+conclusion(interpretation);
    }
    if (step === 2) {
      return stats([['Bodega actual',num(state.positions,0)+' posiciones'],
        ['Actual + alquiler',num(state.positions+state.rentPositions,0)+' posiciones'],
        ['Actual + ampliación',num(state.positions+state.expandPositions,0)+' posiciones']])+
        `<div class="exposure-grid"><div class="exposure-card"><h3>Factibilidad sobre inventario máximo</h3>${table(
          ['Fuente','Q máximo','Posiciones','Resultado'],model.rows.map(row=>[sourceName(row),num(row.Q),num(row.positions,0),
            row.feasible?`<span class="good">${row.chosen.name}</span>`:`<span class="bad">${!row.supply?'Límite anual local':'No cabe'}</span>`]))}
          <div class="formula">Posiciones = ⌈Q / ${num(state.units,0)}⌉ · Máximo = Q</div>
          <p class="exposure-detail">Alquiler y ampliación son alternativas; sus capacidades no se suman. Local: ${num(state.localCapacity,0)} unidades/año.</p></div>
          <div class="exposure-card"><h3>Inventario y capacidad · un año</h3><div id="exposure-saw" class="chart"></div>
          <p class="exposure-detail">Posiciones equivalentes; reposiciones en tiempos exactos. Máximo ${num(10000,0)} ciclos visibles.</p></div></div>`+
        conclusion(model.rows.filter(x=>!x.feasible).length ? model.rows.filter(x=>!x.feasible).map(row=>
          `${row.name} ${!row.supply?`supera el límite anual (${num(state.D,0)} > ${num(state.localCapacity,0)})`:
            `necesita ${row.positions} posiciones y solo dispone de hasta ${Math.max(...row.configs.map(c=>c.positions))}`}`).join('; ')+'.'
          : `Las tres fuentes caben; ${best.name} usa ${best.chosen.name.toLowerCase()} con ${best.positions} posiciones requeridas.`);
    }
    if (step === 3) {
      const policies = fivePolicies(model);
      return stats([['Fuente recomendada',winner(model)],['Costo total anual',best?shortMoney(best.total):'Sin solución'],
        ['Ahorro frente a otra fuente',model.winners.length>1?'Empate · '+money(0):next?shortMoney(next.total-best.total):'Sin otra viable']])+
        `<div class="exposure-card exposure-economic"><h3>Los cinco escenarios · componentes en millones de COP/año</h3>${table(
          ['Escenario','Adquisición','Pedidos','Mantener','Capacidad','Molde','CTA viable','Estado'],
          policies.map(row=>[sourceName({...row,name:row.policy}),num(row.acquisition/1e6),num(row.ordering/1e6),num(row.holding/1e6),
            row.config?num(row.config.cost/1e6):'—',num(row.mold/1e6),row.feasible?`<strong>${shortMoney(row.total)}</strong>`:'—',
            `<span class="${row.feasible?'good':'bad'}">${row.reason}</span>`]))}
          </div>`+
          conclusion(decisionText(model));
    }
    if (step === 4) {
      const eq = equilibria(state);
      const financeViable = Number.isFinite(eq.finance)&&eq.finance<=100;
      const guidance = !eq.importation ? eq.error :
        `${eq.price?`El local puede superar a ${eq.importation.name} a un precio menor que ${money(eq.price)}`:eq.priceMessage}`+
        `${financeViable?`; con el precio activo, financiación mínima ${num(eq.finance,4)}%`:`; ${eq.financeMessage}`}. En el umbral hay empate si el costo es continuo.`;
      return stats([['Precio local máximo',eq.price?money(eq.price)+'/unidad':'Sin umbral viable'],
        ['Financiación mínima',financeViable?num(eq.finance,4)+'%':Number.isFinite(eq.finance)?'100% no basta':'Sin umbral viable'],
        ['Mejor importación viable',eq.importation?eq.importation.name+' · '+shortMoney(eq.importation.total):'Sin referencia']])+
        `<div class="exposure-grid"><div class="exposure-card"><h3>Precio local · EOQ y bodega recalculados</h3><div id="exposure-price" class="chart"></div>
          <p class="exposure-detail">${eq.priceResult?`Al umbral: EOQ ${num(eq.priceResult.eoq)} · ${eq.priceResult.positions} posiciones · ${eq.priceResult.chosen.name}.`:eq.priceMessage||eq.error}</p></div>
          <div class="exposure-card"><h3>Financiación del molde · precio activo</h3><div id="exposure-finance" class="chart"></div>
          <p class="exposure-detail">Activo: ${num(state.p)}% financiado; la empresa asume ${money(local.mold)} al año.</p></div></div>`+
          conclusion(guidance);
    }
    const baseline = calculate(BASE);
    const changes = [];
    if (state.vl!==BASE.vl) changes.push(`precio local ${money(state.vl)}`);
    if (state.f20!==BASE.f20) changes.push(`flete de 20 pies ${money(state.f20)}`);
    if (state.p!==BASE.p) changes.push(`financiación ${num(state.p)}%`);
    if (state.D!==BASE.D) changes.push(`demanda ${num(state.D,0)}`);
    const changed = winner(model)!==winner(baseline);
    const reason = !best ? decisionText(model) :
      `${changes.length?changes.join(' · ')+'. ':''}${changed?'Cambia la fuente frente a G1':'Se conserva la fuente de G1'}: ${decisionText(model)}`;
    return `<div class="exposure-variations">${['Base G1',`Precio local ${money(variation(1).vl)}`,
      `Flete 20 pies ${money(variation(2).f20)}`,`Financiación ${num(variation(3).p)}%`].map((label,n)=>
        `<button data-exposure-variation="${n}">${n?n+' · ':''}${label}</button>`).join('')}</div>`+
      stats([['Recomendación activa',winner(model)],['Costo total anual',best?shortMoney(best.total):'Sin solución'],
        ['Δ ganador frente a G1',best?shortMoney(best.total-baseline.ranked[0].total):'Sin comparación']])+
      `<div class="exposure-card"><h3>Costos comparados del escenario activo</h3>${table(
        ['Fuente','Costo total anual','Bodega / restricción','Δ CTA vs. G1'],model.rows.map((row,i)=>[sourceName(row),
          row.feasible?money(row.total):'No factible',row.feasible?row.chosen.name:!row.supply?'Capacidad anual local':'Inventario máximo no cabe',
          row.feasible&&baseline.rows[i].feasible?shortMoney(row.total-baseline.rows[i].total):'—']))}
        <p class="exposure-detail">Cada botón restaura todos los datos de G1 y modifica un único parámetro. La demanda aplicada fuera de estos botones conserva los demás parámetros activos.</p></div>`+
        conclusion(reason);
  }

  function renderExposure() {
    const model = calculate(state);
    view.innerHTML = `<div class="exposure-toolbar"><span class="pill exposure-scenario">${scenario}</span>
      <form id="exposure-demand-form"><label for="exposure-demand">Demanda · unidades/año</label>
        <input id="exposure-demand" type="number" min="0.000001" step="any" value="${Number.isFinite(state.D)?state.D:''}" required>
        <button type="submit">Aplicar</button></form>
      <button id="exposure-reset">Restaurar G1</button><button id="exposure-fullscreen">${document.fullscreenElement?'Salir de pantalla completa':'Pantalla completa'}</button>
      <span id="exposure-status" role="status"></span></div>
      <div class="exposure-heading"><div><span class="eyebrow">EOQ G1 · ${step+1} / ${titles.length}</span>
        <h1 id="exposure-title">${titles[step]}</h1></div>
        <div class="exposure-steps" aria-label="Pantallas de exposición">${titles.map((title,n)=>
          `<button data-exposure-step="${n}" aria-label="${n+1}. ${title}" ${n===step?'aria-current="step"':''}>${n+1}</button>`).join('')}</div></div>
      <article id="exposure-slide" aria-labelledby="exposure-title" data-step="${step}">
        ${model.errors.length?`<div class="note bad" role="alert">Corrija los parámetros en Análisis completo o restaure G1: ${model.errors.join(' · ')}</div>`:content(model)}</article>
      <div class="exposure-navigation"><button id="exposure-prev" ${step===0?'disabled':''}>← Anterior</button>
        <span>${step+1} / ${titles.length}</span><button id="exposure-next" ${step===titles.length-1?'disabled':''}>Siguiente →</button></div>`;
    view.querySelector('#exposure-prev').onclick=()=>go(step-1);
    view.querySelector('#exposure-next').onclick=()=>go(step+1);
    view.querySelectorAll('[data-exposure-step]').forEach(button=>button.onclick=()=>go(Number(button.dataset.exposureStep)));
    view.querySelectorAll('[data-exposure-source]').forEach(button=>button.onclick=()=>{selectedSource=button.dataset.exposureSource;renderExposure();});
    view.querySelectorAll('[data-exposure-variation]').forEach(button=>button.onclick=()=>{
      const n=Number(button.dataset.exposureVariation);state=variation(n);scenario=n?'Variación '+n+' desde G1':'Base G1';render();
    });
    view.querySelector('#exposure-demand-form').onsubmit=event=>{
      event.preventDefault();const input=view.querySelector('#exposure-demand');
      if(!input.reportValidity())return;
      state={...state,D:Number(input.value)};scenario='Demanda personalizada · '+num(state.D,0)+' unidades/año';render();
    };
    view.querySelector('#exposure-reset').onclick=()=>{state={...BASE};scenario='Base G1';render();};
    view.querySelector('#exposure-fullscreen').onclick=async()=>{
      try {if(document.fullscreenElement)await document.exitFullscreen();else await view.requestFullscreen();}
      catch(error){view.querySelector('#exposure-status').textContent='El navegador no permitió activar pantalla completa.';}
    };
    if(!model.errors.length)renderExposureCharts(model);
    tip.style.display='none';
    if(document.fullscreenElement)view.append(tip);
  }

  function go(next) {
    step=Math.max(0,Math.min(titles.length-1,next));tip.style.display='none';renderExposure();
  }

  function changeMode(exposure) {
    active=exposure;
    document.body.classList.toggle('presenting',active);
    view.hidden=!active;
    document.getElementById('analysis-view').hidden=active;
    document.getElementById('analysis-menu').hidden=active;
    document.getElementById('analysis-tab').setAttribute('aria-selected',String(!active));
    document.getElementById('presentation-tab').setAttribute('aria-selected',String(active));
    tip.style.display='none';
    if(active)renderExposure();
    window.scrollTo(0,0);
  }
  document.getElementById('analysis-tab').onclick=()=>changeMode(false);
  document.getElementById('presentation-tab').onclick=()=>changeMode(true);
  document.addEventListener('eoq:updated',()=>{if(active)renderExposure();});
  document.addEventListener('keydown',event=>{
    if(!active||event.altKey||event.ctrlKey||event.metaKey||event.target.closest('input,select,textarea,[contenteditable="true"]'))return;
    if(event.key==='ArrowRight'||event.key==='ArrowLeft'){
      event.preventDefault();go(step+(event.key==='ArrowRight'?1:-1));
    }
  });
  document.addEventListener('fullscreenchange',()=>{
    (document.fullscreenElement||document.body).append(tip);
    const button=view.querySelector('#exposure-fullscreen');
    if(button)button.textContent=document.fullscreenElement?'Salir de pantalla completa':'Pantalla completa';
  });

  function renderExposureCharts(model) {
    const common={width:760,height:290,large:true};
    if(step===1){
      const row=model.rows.find(x=>x.id===selectedSource);
      const xmin=row.eoq>0?Math.min(row.eoq,row.Q)*.4:row.Q*.1;
      const xmax=Math.max(row.eoq,row.Q)*1.6;
      const quantities=Array.from({length:181},(_,i)=>xmin+(xmax-xmin)*i/180);
      const series=[['ordering','Pedidos','#48536b'],['holding','Mantener','#89682c'],['trc','TRC',colors[model.rows.indexOf(row)]]].map(([key,name,color])=>({
        name,color,points:quantities.map(Q=>[Q,(key==='ordering'?row.A*state.D/Q:key==='holding'?row.v*model.r*Q/2:row.A*state.D/Q+row.v*model.r*Q/2)/1e6]),
        tooltip:Q=>{const ordering=row.A*state.D/Q,holding=row.v*model.r*Q/2;return `Q ${num(Q)} · ${name}: ${money(key==='ordering'?ordering:key==='holding'?holding:ordering+holding)}`;}
      }));
      lineChart('exposure-trc',series,{...common,xmin,xmax,ymax:Math.max(...series[2].points.map(p=>p[1]))*1.17,
        marks:[...(row.eoq>0?[{x:row.eoq,y:row.minTRC/1e6,name:'EOQ',color:colors[model.rows.indexOf(row)]}]:[]),
          ...(row.id!=='local'?[{x:row.Q,y:row.trc/1e6,name:'Lote real',color:'#173b32'}]:[])]});
    }
    if(step===2){
      const configs=model.rows[0].configs;
      const capacities=[];
      configs.forEach(c=>{const same=capacities.find(x=>x.positions===c.positions);if(same)same.name+=' / '+c.name;else capacities.push({...c});});
      const series=model.rows.map((row,i)=>({name:row.name,color:colors[i],points:saw(row.Q,state.D,state.units),
        tooltip:day=>`${row.name} · día ${num(day)} · ${num((row.Q-state.D/365*(day%(365*row.Q/state.D)))/state.units)} posiciones equivalentes`}));
      capacities.forEach(c=>series.push({name:c.name+' · '+num(c.positions,0)+' pos.',color:'#59625f',dash:true,
        points:[[0,c.positions],[365,c.positions]],tooltip:()=>`${c.name}: ${c.positions} posiciones`}));
      lineChart('exposure-saw',series,{...common,xmax:365,ymax:Math.max(...model.rows.map(x=>x.Q/state.units),...capacities.map(x=>x.positions))*1.12,
        xlabel:'Día del año',ylabel:'Posiciones equivalentes'});
    }
    if(step===4){
      const eq=equilibria(state);
      drawDecisionSensitivity('exposure-price','vl',
        Math.min(state.vl*.85,eq.price?eq.price*.94:state.vl*.85),
        Math.max(state.vl*1.15,eq.price?eq.price*1.06:state.vl*1.15),eq.price,common);
      drawDecisionSensitivity('exposure-finance','p',0,100,
        Number.isFinite(eq.finance)&&eq.finance<=100?eq.finance:null,common);
    }
  }

  function drawDecisionSensitivity(id,key,min,max,threshold,common) {
    const values=Array.from({length:81},(_,i)=>min+(max-min)*i/80);
    if(Number.isFinite(threshold))values.push(threshold);
    values.push(state[key]);values.sort((a,b)=>a-b);
    const scenarios=values.map(value=>calculate({...state,[key]:value}));
    const series=modelSeries(scenarios,values,key);
    const costs=series.flatMap(s=>s.points.filter(Boolean).map(p=>p[1]));
    if(!costs.length){document.getElementById(id).innerHTML='<p class="note">No hay fuentes factibles en este rango.</p>';return;}
    const minCost=Math.min(...costs),maxCost=Math.max(...costs),padding=Math.max((maxCost-minCost)*.12,maxCost*.005);
    const markers=[];
    if(Number.isFinite(threshold)){
      const local=calculate({...state,[key]:threshold}).rows[2];
      if(local.feasible)markers.push({x:threshold,y:local.total/1e6,name:'Umbral',color:colors[2]});
    }
    const current=calculate(state).rows[2];
    if(current.feasible)markers.push({x:state[key],y:current.total/1e6,name:'Activo',color:'#18332f',dy:28});
    lineChart(id,series,{...common,xmin:min,xmax:max,ymin:Math.max(0,minCost-padding),ymax:maxCost+padding,
      xlabel:key==='vl'?'Precio local (COP/unidad)':'Molde financiado por proveedor (%)',marks:markers,
      verticals:Number.isFinite(threshold)?[{x:threshold,name:'',color:colors[2]}]:[]});
  }

  function modelSeries(scenarios,values,key) {
    return ['20 pies','40 pies','Local'].map((name,i)=>({name,color:colors[i],
      points:scenarios.map((model,j)=>model.rows[i].feasible?[values[j],model.rows[i].total/1e6]:null),
      tooltip:value=>{
        const model=calculate({...state,[key]:value}),row=model.rows[i];
        return `${name}: ${row.feasible?money(row.total):'no factible'}${i===2?` · EOQ ${num(row.eoq)} · ${row.positions} posiciones`:''}`;
      }
    })).filter(series=>series.points.some(Boolean));
  }
})();
