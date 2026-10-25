'use strict';
const data = window.SILICON_EYE;
const views = window.SE_VIEWS;
document.getElementById('material-drawing').innerHTML = views.materials;
document.getElementById('metal-drawing').innerHTML = views.metals;
function selectCase(name) {
  if (!['materials','devices','metals'].includes(name)) return;
  document.querySelectorAll('[data-case]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.case===name)));
  document.querySelectorAll('[role=tabpanel]').forEach(p=>p.hidden=p.id!==name);
}
document.querySelectorAll('[data-case]').forEach(b=>b.addEventListener('click',()=>{
  selectCase(b.dataset.case); history.replaceState(null,'','#'+b.dataset.case);
}));
selectCase(location.hash.slice(1));
window.addEventListener('hashchange',()=>selectCase(location.hash.slice(1)));
document.querySelectorAll('[data-material]').forEach(e=>e.addEventListener('change',()=>{
  document.querySelectorAll('#material-drawing [data-layer="'+e.dataset.material+'"]').forEach(g=>g.style.display=e.checked?'':'none');
}));
document.querySelectorAll('[data-metal]').forEach(e=>e.addEventListener('change',()=>{
  document.querySelectorAll('#metal-drawing [data-layer="'+e.dataset.metal+'"]').forEach(g=>g.style.display=e.checked?'':'none');
}));
let zoomed=false;
document.getElementById('metal-zoom').addEventListener('click',e=>{
  zoomed=!zoomed;
  document.querySelector('#metal-drawing svg').setAttribute('viewBox',zoomed?'1345 155 65 65':'1320 120 430 440');
  e.target.textContent=zoomed?'恢复整体':'放大孔组';
});
const deviceSelect=document.getElementById('device-select');
const frameSelect=document.getElementById('device-frame');
data.device_index.devices.forEach(d=>{const o=document.createElement('option');o.value=d.id;o.textContent=d.id;deviceSelect.append(o);});
const ns='http://www.w3.org/2000/svg';
function el(tag,attrs){const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);return n;}
function showDevice(){
  const windowInfo=data.device_index.windows.find(w=>w.id===frameSelect.value);
  const [x,y,w,h]=windowInfo.xywh;
  const svg=el('svg',{viewBox:[x,y,w,h].join(' '),role:'img','aria-label':'器件原生照片和检查范围'});
  svg.append(el('image',{href:'assets/device-'+windowInfo.id+'.webp',x,y,width:w,height:h}));
  let visible=0;
  windowInfo.devices.forEach((d,i)=>{
    if(deviceSelect.value!=='all'&&deviceSelect.value!==d.device_id)return;
    if(!d.polygon_native_xy)return;
    visible++;
    const color=i===0?'#75ffce':'#ffbd77';
    svg.append(el('polygon',{points:d.polygon_native_xy.map(p=>p.join(',')).join(' '),fill:color,'fill-opacity':'.13',stroke:color,'stroke-width':'1.8','stroke-dasharray':d.status==='macro_projection'?'5 3':'none','data-device-id':d.device_id}));
    const p=d.polygon_native_xy[0];
    const text=el('text',{x:p[0],y:p[1]-5,fill:color,'font-size':10,'font-family':'system-ui','paint-order':'stroke',stroke:'#0b1421','stroke-width':2});text.textContent=d.device_id;svg.append(text);
  });
  document.getElementById('device-drawing').replaceChildren(svg);
  document.getElementById('device-location').textContent=visible?(windowInfo.id==='m1'?'虚线：已审宏观投影查找范围，非精确材料边界':'实线：原生候选检查范围，非逐像素边界'):'AA保留原图上下文；尚无逐器件定位证据，不补画器件框。';
  const tbody=document.getElementById('terminal-rows');tbody.replaceChildren();
  data.device_index.devices.filter(d=>deviceSelect.value==='all'||d.id===deviceSelect.value).forEach(d=>d.terminals.forEach(t=>{
    const row=document.createElement('tr');
    [d.id,t.role,t.confirmed_net_id||'未知'].forEach((value,i)=>{const td=document.createElement('td');td.textContent=value;if(i===2)td.className=t.confirmed_net_id?'confirmed':'unknown';row.append(td);});tbody.append(row);
  }));
}
deviceSelect.addEventListener('change',showDevice);frameSelect.addEventListener('change',showDevice);showDevice();

const quality = window.SE_QUALITY;
document.getElementById('aa-history-count').textContent = quality.aa_historical_accepted_tasks + ' / 3';
document.getElementById('catalog-count').textContent = quality.catalog_tasks + ' 个';
document.getElementById('catalog-methods').textContent = quality.tasks_with_existing_machine_scorer + '个沿用机器评分器，' + quality.manual_rubric_tasks + '个提供人工rubric；本轮新模型运行0次。';
document.getElementById('failure-summary').textContent = 'POLY计数 ' + quality.poly_count.initial + '→' + quality.poly_count.human + '；V1承载由窄A改为宽B，记录1次承载纠正。';
document.getElementById('work-layer-counts').textContent = Object.entries(quality.work_layer_objects).map(([k,v])=>k+' '+v).join(' / ');
document.getElementById('unknown-scope-count').textContent = quality.unresolved_scopes;
quality.cases.forEach(c=>{
  const row=document.createElement('tr');
  [c.id+' · '+c.title,c.mode==='agent_evaluation'?'现有机器评分器':'人工rubric',c.rubric+' '+c.limit].forEach(value=>{const td=document.createElement('td');td.textContent=value;row.append(td);});
  document.getElementById('quality-task-rows').append(row);
});
