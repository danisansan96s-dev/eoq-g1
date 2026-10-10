/* Prueba opcional de navegador: Streamlit debe estar ejecutándose. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.EOQ_PLAYWRIGHT||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true});
 try {
  const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(process.env.EOQ_TEST_URL||'http://127.0.0.1:8511');
  const iframe=page.locator('iframe[title="Herramienta EOQ G1"]');
  await iframe.waitFor({timeout:30000});
  const frame=await (await iframe.elementHandle()).contentFrame();
  await frame.locator('#resumen').waitFor();
  let checks=0;const ok=(v,message)=>{assert(v,message);checks++;};
  ok(await frame.locator('section').count()===11);
  ok(await frame.locator('svg').count()===6);
  ok((await frame.locator('#resumen').innerText()).includes('20 pies'));
  ok(!/Guion ejecutivo|sin cortes|integrantes|video/i.test(await frame.locator('body').innerText()));
  for(const id of ['datos','eoq','robustez','capacidad','molde','comparacion','graficas','sensibilidad','equilibrio','gerencia','resumen']){
   await frame.locator(`nav a[href="#${id}"]`).click();
   const position=await frame.locator('#'+id).evaluate(el=>({top:el.getBoundingClientRect().top, bottom:el.getBoundingClientRect().bottom, height:window.innerHeight, scroll:window.scrollY}));
   ok(position.top>=0 && position.top<position.height && position.bottom>0, `Navegación ${id}: ${JSON.stringify(position)}`);
   ok(page.frames().length===2);
  }
  await frame.locator('nav a[href="#datos"]').click();
  const trcBefore=await frame.locator('#trc-20 svg').innerHTML();
  const sawBefore=await frame.locator('#sawChart svg').innerHTML();
  await frame.locator('[data-key="D"]').fill('12000');
  ok(await frame.locator('#trc-20 svg').innerHTML()!==trcBefore);
  ok(await frame.locator('#sawChart svg').innerHTML()!==sawBefore);
  ok((await frame.locator('#scenario').innerText()).includes('personalizado'));
  const downloadEvent=page.waitForEvent('download');
  await frame.locator('#export').click();
  const download=await downloadEvent;
  ok(download.suggestedFilename()==='EOQ-G1-escenario.json');
  const json=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
  ok(json.parameters.D===12000);
  ok(json.model.rows[0].orders===12000/1900);
  ok(json.model.rows[0].total===12000*97000+12830000*12000/1900+97000*.22*1900/2+13000000);
  const saved=process.env.EOQ_TEST_DOWNLOAD;
  if(saved)await download.saveAs(saved);
  await frame.locator('nav a[href="#graficas"]').click();
  const capacityBefore=await frame.locator('#sawChart').innerHTML();
  await frame.locator('#graphCapacity').selectOption('0');
  ok(await frame.locator('#sawChart').innerHTML()!==capacityBefore);
  ok((await frame.locator('#sawChart').innerText()).includes('SUPERA CAPACIDAD'));
  await frame.locator('#trc-20 [data-hover]').hover();
  ok(await frame.locator('.tooltip').isVisible());
  await frame.locator('nav a[href="#sensibilidad"]').click();
  const sensitivityBefore=await frame.locator('#sensitivityChart').innerHTML();
  await frame.locator('#sensitivityKey').selectOption('p');
  ok(await frame.locator('#sensitivityChart').innerHTML()!==sensitivityBefore);
  for(const n of [1,2,3]){
   await frame.locator('nav a[href="#gerencia"]').click();
   await frame.locator(`[data-variation="${n}"]`).click();
   ok((await frame.locator('#resumen').innerText()).includes('Local'));
   ok(await frame.locator('[data-key="D"]').inputValue()==='9000');
   ok(await frame.locator('[data-key="vl"]').inputValue()===(n===1?'99000':'103000'));
  }
  await frame.locator('#reset').click();
  await frame.locator('nav a[href="#datos"]').click();
  await frame.locator('[data-key="D"]').fill('21000');
  ok((await frame.locator('#capacidad').innerText()).includes('Capacidad anual local insuficiente'));
  await frame.locator('[data-key="D"]').fill('');
  ok(await frame.locator('#resumen').count()===0);
  ok((await frame.locator('#errors').innerText()).includes('válido'));
  await frame.locator('#reset').click();
  // La impresión debe seguir disponible dentro del iframe.
  await frame.evaluate(()=>{window.print=()=>{window.__printRequested=true;};});
  await frame.getByRole('button',{name:'Imprimir informe'}).click();
  ok(await frame.evaluate(()=>window.__printRequested===true));
  await frame.locator('nav a[href="#resumen"]').click();
  if(process.env.EOQ_TEST_SCREENSHOT)await page.screenshot({path:process.env.EOQ_TEST_SCREENSHOT,fullPage:true});
  // Comprueba que el tamaño del iframe y la navegación se adaptan al móvil.
  await page.setViewportSize({width:390,height:844});
  await page.waitForTimeout(250);
  ok(await iframe.evaluate(el=>el.clientWidth<=390));
  await frame.locator('.brand').click();
  ok((await frame.locator('#resumen').innerText()).includes('20 pies'));
  const mobileDownloadEvent=page.waitForEvent('download');
  await frame.locator('#export').click();
  const mobileDownload=await mobileDownloadEvent;
  ok(JSON.parse(fs.readFileSync(await mobileDownload.path(),'utf8')).parameters.D===9000);
  ok(errors.length===0);
  console.log(JSON.stringify({checks,errors,status:'PASS',runtime:'Streamlit + Chromium',downloadDemand:json.parameters.D},null,2));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
