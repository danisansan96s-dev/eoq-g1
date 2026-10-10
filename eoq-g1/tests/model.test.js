(function(){
const {BASE:B,calculate:c,equilibria:e,variation:v,saw}=EOQ;let count=0;
function assert(b,msg){count++;if(!b)throw Error(msg)}function near(a,b,t=.05){assert(Math.abs(a-b)<t,`${a} != ${b}`)}
const base=c(B);assert(!base.errors.length,'Base válida');const [a,b,l]=base.rows;
near(a.A,12830000);near(b.A,15600000);near(l.A,631000);near(base.r,.22);assert(a.positions===76&&b.positions===168,'posiciones G1');assert(a.chosen.positions===165&&a.chosen.name==='Ampliación','ampliación G1');assert(!b.feasible,'40 no cabe');near(a.total,967046684.2105263);near(l.total,979042826.379,.2);assert(base.winners[0].id==='20','ganador base');
const eq=e(B);near(eq.price,101678.57,.01);near(eq.finance,46.6581,.0001);near(eq.priceResult.total,a.total,.01);near(c({...B,p:eq.finance}).rows[2].total,a.total,.01);
assert(c(v(1)).winners[0].id==='local','variación 1');assert(c(v(2)).winners[0].id==='local','variación 2');assert(c(v(3)).winners[0].id==='local','variación 3');
assert(v(2).vl===B.vl&&v(3).f20===B.f20,'variaciones independientes');assert(!c({...B,D:21000}).rows[2].supply,'capacidad anual local');assert(c({...B,q20:1875}).rows[0].chosen.name==='Actual','75 posiciones');assert(c({...B,q20:1876}).rows[0].chosen.name==='Ampliación','76 posiciones');assert(c({...B,rent:12000000}).rows[0].chosen.name==='Alquiler','alquiler barato');
for(const k of ['D','vi','vl','rDirect'])assert(c({...B,[k]:0,...(k==='rDirect'?{rMode:'direct'}:{})}).errors.length,'positivo '+k);
assert(c({...B,D:NaN}).errors.length,'vacío');assert(c({...B,p:101}).errors.length,'p inválido');assert(c({...B,positions:0,rentPositions:0,expandPositions:0}).winners.length===0,'sin alternativas');assert(!c({...B,rent:0,capital:0}).errors.length,'ceros permitidos');assert(e({...B,positions:200}).importation,'referencia importada');assert(e({...B,D:21000}).price===null,'umbral local no viable');assert(e({...B,p:0,vl:110000}).finance>100,'más de 100%');
const tie=c({...B,vl:eq.price});assert(tie.winners.length===2,'empate económico');
const points=saw(a.Q,B.D,B.units);near(points[1][0],365*a.Q/B.D);near(points[1][1],0);near(points[2][1],76);assert(points.at(-1)[0]===365,'horizonte');assert(saw(a.Q,12000,B.units)[1][0]!==points[1][0],'eventos dinámicos');
const changed=c({...B,f20:10000000});assert(changed.rows[0].eoq!==a.eoq&&changed.rows[0].trc!==a.trc,'marcadores cambian');
return JSON.stringify({tests:count,base:base.rows.map(x=>({fuente:x.name,EOQ:x.eoq,CTA:x.total,factible:x.feasible})),equilibrio:{precio:eq.price,financiacion:eq.finance},variaciones:[1,2,3].map(n=>({n,ganador:c(v(n)).winners[0].name,CTA:c(v(n)).ranked[0].total}))},null,2);
})()
