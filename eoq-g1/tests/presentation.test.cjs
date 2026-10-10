const assert=require('node:assert/strict'),path=require('node:path');
const {chromium}=require(process.env.EOQ_PLAYWRIGHT||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true});
 try {
  const page=await browser.newPage({viewport:{width:1366,height:768}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const url=process.env.EOQ_TEST_URL||'http://127.0.0.1:8511';
  await page.goto(url);
  let frame;
  if(url.startsWith('file:'))frame=page.mainFrame();
  else{const iframe=page.locator('iframe[title="Herramienta EOQ G1"]');await iframe.waitFor();frame=await(await iframe.elementHandle()).contentFrame();}
  await frame.locator('#resumen').waitFor();
  await frame.locator('#presentation-tab').click();
  let count=0;const ok=(value,msg)=>{assert(value,msg);count++;};
  const choose=async n=>frame.locator(`[data-exposure-step="${n}"]`).click();
  const apply=async value=>{await frame.locator('#exposure-demand').fill(String(value));await frame.getByRole('button',{name:'Aplicar',exact:true}).click();};
  const fit=async label=>{
   const layout=await frame.evaluate(()=>{
    const v=document.querySelector('#presentation-view'),s=document.querySelector('#exposure-slide');
    const cards=[...s.querySelectorAll('.exposure-card')].map(el=>el.getBoundingClientRect().bottom);
    const conclusion=s.querySelector('.exposure-conclusion').getBoundingClientRect();
    return {viewHeight:v.clientHeight,viewScroll:v.scrollHeight,slideHeight:s.clientHeight,slideScroll:s.scrollHeight,
      cardsBottom:Math.max(...cards),conclusionTop:conclusion.top,navigationBottom:document.querySelector('.exposure-navigation').getBoundingClientRect().bottom,viewport:innerHeight};
   });
   if(process.env.EOQ_TEST_SCREENSHOTS)await page.screenshot({path:path.join(process.env.EOQ_TEST_SCREENSHOTS,`exposure-${label}.png`)});
   ok(layout.viewScroll<=layout.viewHeight+2,`Desbordamiento ${label}: ${JSON.stringify(layout)}`);
   ok(layout.slideScroll<=layout.slideHeight+2,`Pantalla ${label}: ${JSON.stringify(layout)}`);
   ok(layout.cardsBottom<=layout.conclusionTop+1,`Superposición ${label}: ${JSON.stringify(layout)}`);
   ok(layout.navigationBottom<=layout.viewport+2,`Navegación fuera de pantalla ${label}: ${JSON.stringify(layout)}`);
  };
  ok(await frame.locator('#analysis-view').isHidden());
  ok(await frame.locator('#exposure-slide').getAttribute('data-step')==='0');
  ok(await frame.locator('#exposure-prev').isDisabled());
  for(let n=0;n<6;n++){await choose(n);await fit('laptop-'+n);ok(await frame.locator('#exposure-slide').count()===1);}
  ok(await frame.locator('#exposure-next').isDisabled());
  await frame.locator('#exposure-prev').click();ok(await frame.locator('#exposure-slide').getAttribute('data-step')==='4');
  await frame.locator('#exposure-next').click();ok(await frame.locator('#exposure-slide').getAttribute('data-step')==='5');
  await page.keyboard.press('ArrowLeft');ok(await frame.locator('#exposure-slide').getAttribute('data-step')==='4');
  await page.keyboard.press('ArrowRight');ok(await frame.locator('#exposure-slide').getAttribute('data-step')==='5');
  await frame.locator('#exposure-demand').focus();await page.keyboard.press('ArrowLeft');ok(await frame.locator('#exposure-slide').getAttribute('data-step')==='5');
  await choose(1);const eoqBefore=await frame.locator('#exposure-trc svg').innerHTML();
  await frame.locator('#exposure-demand').fill('12000');
  ok(await frame.locator('#exposure-trc svg').innerHTML()===eoqBefore,'Aplicación explícita');
  await frame.getByRole('button',{name:'Aplicar',exact:true}).click();
  ok(await frame.locator('#exposure-trc svg').innerHTML()!==eoqBefore,JSON.stringify(await frame.evaluate(()=>({demand:state.D,scenario,input:document.querySelector('#exposure-demand').value,valid:document.querySelector('#exposure-demand').validity.valid})))+' errors: '+errors.join('; '));
  ok((await frame.locator('.exposure-scenario').innerText()).includes('12.000'));
  ok(await frame.locator('#exposure-slide').getAttribute('data-step')==='1');
  const expected=await frame.evaluate(()=>EOQ.calculate({...EOQ.BASE,D:12000}).rows[0].eoq);
  const eoqLabel=await frame.locator('.exposure-stats').innerText();
  ok(eoqLabel.includes(new Intl.NumberFormat('es-CO',{maximumFractionDigits:2}).format(expected)));
  await frame.locator('[data-exposure-source="40"]').click();
  ok((await frame.locator('.exposure-stats').innerText()).includes('40 pies'));
  await choose(2);const sawBefore=await frame.locator('#exposure-saw svg').innerHTML();
  await apply(15000);ok(await frame.locator('#exposure-saw svg').innerHTML()!==sawBefore);
  await choose(3);ok(await frame.locator('.exposure-economic tbody tr').count()===5);
  ok(await frame.locator('.exposure-economic tbody tr').nth(0).innerText().then(x=>x.includes('Necesita')));
  await choose(4);const priceBefore=await frame.locator('#exposure-price svg').innerHTML(),financeBefore=await frame.locator('#exposure-finance svg').innerHTML();
  await apply(9000);
  ok(await frame.locator('#exposure-price svg').innerHTML()!==priceBefore);
  ok(await frame.locator('#exposure-finance svg').innerHTML()!==financeBefore);
  const thresholds=await frame.evaluate(()=>EOQ.equilibria(EOQ.BASE));
  ok((await frame.locator('.exposure-stats').innerText()).includes(new Intl.NumberFormat('es-CO',{maximumFractionDigits:4}).format(thresholds.finance)));
  await choose(5);
  for(const n of [1,2,3]){
   await frame.locator(`[data-exposure-variation="${n}"]`).click();
   ok((await frame.locator('.exposure-stats').innerText()).includes('Local'));
   const values=await frame.evaluate(()=>({D:state.D,vl:state.vl,f20:state.f20,p:state.p}));
   const expected=await frame.evaluate(n=>{const s=EOQ.variation(n);return {D:s.D,vl:s.vl,f20:s.f20,p:s.p};},n);
   ok(JSON.stringify(values)===JSON.stringify(expected),'Variaciones independientes');
   ok(await frame.locator('#exposure-slide').getAttribute('data-step')==='5');
  }
  await frame.locator('#exposure-reset').click();await choose(4);await apply(21000);
  ok((await frame.locator('.exposure-conclusion').innerText()).includes('capacidad anual'));
  ok((await frame.locator('.exposure-stats').innerText()).includes('Sin umbral viable'));
  await frame.locator('#exposure-reset').click();await choose(0);
  await frame.locator('#exposure-fullscreen').click();
  await frame.waitForFunction(()=>document.fullscreenElement?.id==='presentation-view',null,{timeout:5000});
  ok(await frame.evaluate(()=>document.fullscreenElement?.id==='presentation-view'),'Pantalla completa real');
  ok(await frame.locator('#exposure-fullscreen').innerText()==='Salir de pantalla completa');
  await frame.locator('#exposure-next').click();ok(await frame.locator('#exposure-slide').getAttribute('data-step')==='1');
  await frame.locator('#exposure-fullscreen').click();await frame.waitForFunction(()=>!document.fullscreenElement);ok(await frame.evaluate(()=>!document.fullscreenElement));
  await frame.locator('#analysis-tab').click();
  await frame.locator('[data-key="vl"]').fill('99000');
  await frame.locator('#presentation-tab').click();await choose(3);
  ok((await frame.locator('.exposure-stats').innerText()).includes('Local'),'Actualización desde análisis');
  for(const size of [{width:1280,height:720},{width:1440,height:900}]){
   await page.setViewportSize(size);await page.waitForTimeout(150);
   for(let n=0;n<6;n++){await choose(n);await fit(size.width+'-'+n);}
  }
  await page.setViewportSize({width:390,height:844});await page.waitForTimeout(150);
  for(let n=0;n<6;n++){
   await choose(n);
   ok((await frame.locator('#exposure-title').innerText()).length>0);
   ok(await frame.locator('.exposure-conclusion').isVisible());
   const layout=await frame.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
   ok(layout.scroll<=layout.width+1,'Sin recorte horizontal móvil');
  }
  ok(errors.length===0,errors.join('; '));
  console.log(JSON.stringify({checks:count,errors,status:'PASS',runtime:url.startsWith('file:')?'HTML local + Chromium':'Streamlit + Chromium'},null,2));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exit(1);});
