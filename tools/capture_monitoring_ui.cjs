// Solo servidor temporal de tools/preview_monitoring_ui.py. Nunca producción.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const base = 'http://127.0.0.1:5290';
const output = path.resolve(__dirname,'../docs/evidence');

(async () => {
  const browser = await chromium.launch({headless:true,channel:'chrome'});
  const errors=[],facts=[];
  try {
    const context=await browser.newContext({viewport:{width:1440,height:1000}});
    const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
    await page.goto(base+'/login');await page.getByLabel('Usuario',{exact:true}).fill('dom');
    await page.getByLabel('Contraseña',{exact:true}).fill('local-ui-evidence-only');
    await page.getByRole('button',{name:'Iniciar sesión'}).click();
    await page.waitForFunction(()=>document.querySelector('[data-open-count]').textContent==='45');
    assert.equal(await page.locator('.notification-toast').count(),0);
    facts.push('Login DOM: 45 abiertas, sin notificar las históricas.');
    await page.goto(base+'/alerts?status=Activa');
    await page.getByRole('link',{name:'Siguiente',exact:true}).click();
    assert.match(page.url(),/status=Activa/);assert.match(page.url(),/page=2/);
    await page.screenshot({path:path.join(output,'EV3_UI_ALERTAS.png'),fullPage:true});
    facts.push('Alertas: Siguiente conserva estado y muestra página 2.');
    await page.goto(base+'/measurements/1');
    assert.ok(await page.getByRole('heading',{name:'Alertas asociadas'}).isVisible());
    await page.screenshot({path:path.join(output,'EV3_UI_MEDICION.png'),fullPage:true});
    await page.goto(base+'/rules');await page.locator('.rule-history summary').click();
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:path.join(output,'EV3_UI_REGLAS.png'),fullPage:true});
    await page.goto(base+'/audit?page=2');
    assert.equal(await page.locator('[data-audit-id]').count(),20);
    await page.screenshot({path:path.join(output,'EV3_UI_HISTORIAL.png'),fullPage:true});
    // Un registro a través del formulario real de esta base temporal genera un aviso real.
    await page.goto(base+'/measurements');
    await page.waitForFunction(()=>document.querySelector('[data-open-count]').textContent==='45');
    const csrf=await page.locator('form[action="/logout"] [name=csrf]').inputValue();
    const response=await context.request.post(base+'/measurements',{form:{csrf,sensor_code:'S1',value:'2',unit:'m/s²',
      status:'valido',measured_at:'2026-01-04T13:00:00+00:00',external_id:'browser-notification-only'}});
    assert.equal(response.status(),200);
    // El retorno a visible solicita la misma consulta periódica sin esperar 30 s.
    await page.evaluate(()=>document.dispatchEvent(new Event('visibilitychange')));
    await page.waitForFunction(()=>document.querySelector('[data-open-count]').textContent==='46');
    await page.waitForSelector('.notification-toast a[href="/alerts/46"]');
    const toast=page.locator('.notification-toast').first();
    await toast.getByRole('button',{name:'Cerrar aviso'}).click();
    await page.evaluate(()=>document.dispatchEvent(new Event('visibilitychange')));
    await page.waitForFunction(()=>document.querySelector('[data-notification-status]').textContent.startsWith('Actualizado.'));
    assert.equal(await page.locator('.notification-toast').count(),0);
    await page.locator('.notification-bell summary').click();
    await page.screenshot({path:path.join(output,'EV3_UI_CAMPANA.png')});
    facts.push('Alerta nueva #46: contador 46, aviso con enlace directo, sin repetición tras otra consulta.');
    await page.goto(base+'/alerts');await page.goBack();
    await page.waitForFunction(()=>document.querySelector('[data-open-count]').textContent==='46');
    await Promise.all([
      page.waitForResponse(r=>r.url().includes('/api/v1/alert-notifications?after=46')),
      page.evaluate(()=>document.dispatchEvent(new Event('visibilitychange')))
    ]);
    facts.push('Atrás/Adelante: la página restaurada conserva las consultas de la campana.');
    await page.setViewportSize({width:390,height:844});await page.goto(base+'/alerts');
    await page.screenshot({path:path.join(output,'EV3_UI_MOVIL.png'),fullPage:true});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    facts.push('Viewport móvil 390px: sin desbordamiento horizontal de la página.');
    await context.close();
    for (const [name,role] of [['inspector','Inspector'],['mantencion','Mantención']]) {
      const c=await browser.newContext();const p=await c.newPage();
      await p.goto(base+'/login');await p.getByLabel('Usuario',{exact:true}).fill(name);
      await p.getByLabel('Contraseña',{exact:true}).fill('local-ui-evidence-only');
      await p.getByRole('button',{name:'Iniciar sesión'}).click();
      await p.waitForFunction(()=>document.querySelector('[data-open-count]').textContent==='46');
      assert.equal(await p.locator('.notification-toast').count(),0);
      assert.equal(await p.locator('nav a[href="/rules"]').count(),0);
      assert.equal((await c.request.get(base+'/rules')).status(),403);
      assert.equal((await c.request.get(base+'/maintenance')).status(),404);
      facts.push(role+': campana disponible, históricos silenciosos, reglas 403 y mantenimiento 404.');
      await c.close();
    }
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(output,'EV3_UI_BROWSER_RESULTS.json'),JSON.stringify({
      captured_at:new Date().toISOString(),environment:'Chrome headless; SQLite temporal de laboratorio; sin datos productivos',
      passed:true,facts,page_errors:errors},null,2));
    console.log(facts.join('\n'));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
