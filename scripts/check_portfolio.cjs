// Purpose: exercise the static portfolio without a server. Requires Playwright + Chromium.
// Run with NODE_PATH and PLAYWRIGHT_BROWSERS_PATH pointing to installed runtimes.
const {chromium}=require('playwright');
const fs=require('fs');
const assert=require('assert/strict');
(async()=>{
 const root=require('path').resolve(__dirname,'..');
 const out=root+'/runs/portfolio-browser-check';fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 const checks=[];function record(name){checks.push(name)}
 await page.goto('file://'+root+'/site/index.html');await page.waitForFunction(()=>document.querySelector('#material-drawing svg'));
 await page.screenshot({path:out+'/desktop.png',fullPage:true});await page.screenshot({path:out+'/desktop-top.png'});record('desktop render');
 await page.locator('[data-material="CT"]').uncheck();assert.equal(await page.locator('#material-drawing [data-layer="CT"]').evaluate(e=>e.style.display),'none');
 await page.locator('[data-material="CT"]').check();record('material layer toggle');
 await page.locator('[data-case="devices"]').click();assert.equal(await page.locator('#devices').isVisible(),true);
 for(const id of ['R2_Q1','R2_Q2']){await page.locator('#device-select').selectOption(id);assert.equal(await page.locator('#device-drawing polygon').count(),1);assert.equal(await page.locator('#terminal-rows tr').count(),4);}
 await page.locator('#device-frame').selectOption('m1');assert.equal(await page.locator('#device-drawing polygon').getAttribute('stroke-dasharray'),'5 3');
 await page.screenshot({path:out+'/devices.png'});
 await page.locator('#device-frame').selectOption('aa');assert.equal(await page.locator('#device-drawing polygon').count(),0);assert.match(await page.locator('#device-location').innerText(),/尚无逐器件定位证据/);
 await page.locator('#devices summary').click();await page.locator('.schematic').scrollIntoViewIfNeeded();await page.waitForFunction(()=>document.querySelector('.schematic').complete&&document.querySelector('.schematic').naturalWidth>0);record('device IDs, terminal table, source frames and schematic');
 await page.locator('[data-case="metals"]').click();await page.locator('[data-metal="V2"]').uncheck();assert.equal(await page.locator('#metal-drawing [data-layer="V2"]').first().evaluate(e=>e.style.display),'none');await page.locator('[data-metal="V2"]').check();
 const initial=await page.locator('#metal-drawing svg').getAttribute('viewBox');await page.locator('#metal-zoom').click();assert.notEqual(await page.locator('#metal-drawing svg').getAttribute('viewBox'),initial);await page.screenshot({path:out+'/via-zoom.png'});await page.locator('#metal-zoom').click();assert.equal(await page.locator('#metal-drawing svg').getAttribute('viewBox'),initial);record('metal layer toggle and via zoom');
 await page.setViewportSize({width:390,height:844});
 for(const name of ['materials','devices','metals']){await page.locator('[data-case="'+name+'"]').click();assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);await page.locator('#demo').scrollIntoViewIfNeeded();await page.screenshot({path:out+'/mobile-'+name+'.png',fullPage:name==='materials'});}
 record('mobile 390px all panels without horizontal overflow');
 await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:out+'/mobile-top.png'});
 const images=await page.locator('img').evaluateAll(es=>es.filter(e=>!e.complete||e.naturalWidth===0).map(e=>e.src));assert.deepEqual(images,[]);assert.deepEqual(errors,[]);record('all images loaded and no browser errors');
 await page.goto('file://'+root+'/site/index.html#devices');await page.locator('#devices').waitFor({state:'visible'});assert.equal(await page.locator('#devices').isVisible(),true);record('direct case deep link');
 const result={date:'2026-10-25',browser:'Playwright Chromium headless shell 151',viewports:[[1440,1000],[390,844]],checks,errors,screenshots_dir:'runs/portfolio-browser-check'};
 fs.writeFileSync(root+'/benchmarks/portfolio-v1/browser-verification.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
