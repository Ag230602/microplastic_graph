#!/usr/bin/env python3
"""Build a single self-contained dashboard app (mpkg_dashboard.html).

Combines EVERYTHING into one file that opens with no server:
  * Project overview + counts
  * Interactive knowledge graph (HostPopulation, Evidence, Study, ...)
  * Benchmark queries Q1-Q4
  * Evidence weighting / confidence scoring
  * Human vs animal evidence ranking
  * Study -> Evidence -> Observation provenance traces

Run:  python3 build_dashboard.py   ->  open mpkg_dashboard.html
"""
from __future__ import annotations

import json
import os

import mpkg_query

HERE = os.path.dirname(os.path.abspath(__file__))
GRAPH_JSON = os.path.join(HERE, "mpkg_graph_v2.json")
OUT = os.path.join(HERE, "mpkg_dashboard.html")


def main():
    g = mpkg_query.load()
    analysis = mpkg_query.export_all(g)
    with open(GRAPH_JSON, "r", encoding="utf-8") as fh:
        graph = json.load(fh)

    payload = json.dumps({"graph": graph, "analysis": analysis}, ensure_ascii=False)
    html = TEMPLATE.replace("/*__DATA__*/null", payload)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"Wrote {OUT} ({len(html)} bytes) - open it in a browser.")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Microplastics KG - Project Dashboard</title>
<style>
  :root{
    --bg:#f4f6f8; --ink:#1f2933; --muted:#5f7080; --line:#d4dde6; --panel:#fff;
    --accent:#2f6f9f; --good:#238b6e; --warn:#b65f24; --bad:#c3475b;
    --study:#2f6f9f; --observation:#238b6e; --association:#b65f24; --biomarker:#8b5fbf;
    --mechanism:#c3475b; --method:#4b78c2; --polymer:#8f6a2a; --size:#5f6f89;
    --tissue:#7c6175; --host:#2a9d8f; --evidence:#c9a227; --other:#5f7080;
    --reservoir:#3a8fb7;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
       color:var(--ink);background:var(--bg);}
  header{padding:18px 24px;background:linear-gradient(120deg,#22577a,#2a9d8f);color:#fff;}
  header h1{margin:0;font-size:21px;}
  header p{margin:6px 0 0;opacity:.9;font-size:13px;}
  nav{display:flex;gap:4px;flex-wrap:wrap;padding:0 16px;background:var(--panel);
      border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5;}
  nav button{border:0;background:none;padding:13px 16px;font:inherit;font-weight:600;
      color:var(--muted);cursor:pointer;border-bottom:3px solid transparent;}
  nav button.active{color:var(--accent);border-bottom-color:var(--accent);}
  main{padding:20px 24px;max-width:1280px;margin:0 auto;}
  .tab{display:none;} .tab.active{display:block;}
  .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin:14px 0;}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px;}
  .card .n{font-size:26px;font-weight:700;color:var(--accent);}
  .card .l{font-size:12px;color:var(--muted);margin-top:2px;}
  .panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:16px;margin:14px 0;}
  .panel h3{margin:0 0 10px;font-size:15px;}
  .panel h3 .tag{font-size:11px;font-weight:600;color:#fff;background:var(--accent);
      border-radius:20px;padding:2px 9px;margin-right:8px;vertical-align:middle;}
  table{width:100%;border-collapse:collapse;font-size:13px;}
  th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top;}
  th{color:var(--muted);font-weight:600;}
  code{background:#eef2f6;border-radius:4px;padding:1px 5px;font-size:12px;}
  .pill{display:inline-block;border-radius:20px;padding:2px 10px;font-size:12px;font-weight:600;}
  .pill.low{background:#fdecea;color:#b3261e;} .pill.moderate{background:#fff4e0;color:#9a6500;}
  .pill.high{background:#e6f4ea;color:#1e7a47;} .pill.nullf{background:#eceff1;color:#5f7080;}
  .chain{font-size:12.5px;line-height:1.7;}
  .chain b{color:var(--accent);}
  .verdict{background:#fff4e0;border:1px solid #f0d9a8;border-radius:8px;padding:12px;color:#7a5300;font-size:13px;}
  .quote{border-left:3px solid var(--evidence);padding:4px 0 4px 12px;margin:6px 0;color:#444;font-style:italic;}
  .bar{height:10px;border-radius:6px;background:linear-gradient(90deg,var(--host),var(--accent));}
  /* graph */
  .glayout{display:grid;grid-template-columns:1fr 320px;gap:14px;}
  #graph{width:100%;height:620px;background:#fbfcfe;border:1px solid var(--line);border-radius:10px;}
  .gside{border:1px solid var(--line);border-radius:10px;background:var(--panel);padding:12px;overflow:auto;max-height:660px;}
  .toolbar{display:grid;gap:8px;margin-bottom:10px;}
  input,select{width:100%;border:1px solid var(--line);border-radius:6px;padding:8px;font:inherit;}
  .legend{display:grid;grid-template-columns:1fr 1fr;gap:5px;font-size:11.5px;color:var(--muted);margin-bottom:8px;}
  .legend span{display:flex;align-items:center;gap:5px;}
  .swatch{width:10px;height:10px;border-radius:50%;}
  pre{white-space:pre-wrap;word-break:break-word;background:#fafbfc;border:1px solid var(--line);
      border-radius:6px;padding:10px;font-size:11.5px;}
  .link{stroke:#9aa8b5;stroke-opacity:.5;fill:none;}
  .link-label{fill:#7d8a96;font-size:8px;pointer-events:none;}
  .node circle{stroke:#fff;stroke-width:1.5px;cursor:pointer;}
  .node text{fill:#1f2933;font-size:9px;pointer-events:none;paint-order:stroke;stroke:#fbfcfe;stroke-width:3px;stroke-linejoin:round;}
  .dim{opacity:.12;}
  .selected circle{stroke:#111;stroke-width:2.5px;}
  @media(max-width:900px){.glayout{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
  <h1>Microplastics Knowledge Graph - Project Dashboard</h1>
  <p>Evidence-Aware Environmental Health KG &middot; <em>Neurotoxicity Following Exposure to Micro and Nanoplastics</em></p>
</header>
<nav id="nav"></nav>
<main>
  <section class="tab active" id="tab-overview"></section>
  <section class="tab" id="tab-graph">
    <div class="glayout">
      <svg id="graph" role="img" aria-label="Knowledge graph"></svg>
      <div class="gside">
        <div class="toolbar">
          <input id="search" type="search" placeholder="Search nodes">
          <select id="typeFilter"><option value="">All node types</option></select>
        </div>
        <div class="legend" id="legend"></div>
        <div id="details"><b>Select a node</b><div style="color:var(--muted);font-size:12px">Click any node for details.</div></div>
      </div>
    </div>
  </section>
  <section class="tab" id="tab-queries"></section>
  <section class="tab" id="tab-weighting"></section>
  <section class="tab" id="tab-ranking"></section>
  <section class="tab" id="tab-provenance"></section>
</main>
<script>
const DATA = /*__DATA__*/null;
const colorByType = {
  Study:'var(--study)',Observation:'var(--observation)',Association:'var(--association)',
  Biomarker:'var(--biomarker)',Mechanism:'var(--mechanism)',Method:'var(--method)',
  Polymer:'var(--polymer)',ParticleSizeClass:'var(--size)',TissueOrgan:'var(--tissue)',
  Shape:'var(--other)',ExposurePathway:'var(--other)',ClinicalOutcome:'var(--mechanism)',
  HostPopulation:'var(--host)',Evidence:'var(--evidence)',EnvironmentalCompartment:'var(--reservoir)'
};
const esc = v => String(v).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

const TABS = [
  ['overview','Overview'],['graph','Graph'],['queries','Benchmark Queries'],
  ['weighting','Evidence Weighting'],['ranking','Human vs Animal'],['provenance','Provenance']
];
const nav = document.getElementById('nav');
TABS.forEach(([id,label],i)=>{
  const b=document.createElement('button');
  b.textContent=label; b.className=i===0?'active':'';
  b.onclick=()=>{
    document.querySelectorAll('nav button').forEach(x=>x.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
    b.classList.add('active');
    document.getElementById('tab-'+id).classList.add('active');
    if(id==='graph') ensureGraph();
  };
  nav.appendChild(b);
});

const A = DATA.analysis, S = A.summary;

// ---- Overview ----
(function(){
  const el=document.getElementById('tab-overview');
  const cards = [
    [S.entities,'Entities'],[S.relationships,'Relationships'],
    [S.node_types.HostPopulation||0,'Host Populations'],[S.node_types.Evidence||0,'Evidence Nodes'],
    [S.node_types.Study||0,'Studies'],[S.node_types.Biomarker||0,'Biomarkers'],
    [S.node_types.Mechanism||0,'Mechanisms'],[S.node_types.ClinicalOutcome||0,'Clinical Outcomes']
  ];
  let h='<div class="cards">'+cards.map(([n,l])=>`<div class="card"><div class="n">${n}</div><div class="l">${l}</div></div>`).join('')+'</div>';
  h+=`<div class="panel"><h3>What this project delivers</h3>
    <p style="font-size:13.5px;line-height:1.7;color:#374">An <b>evidence-aware environmental-health knowledge graph</b> that preserves the full scientific reasoning chain:
    <code>Study &rarr; Evidence &rarr; Observation &rarr; Environmental Reservoir &rarr; Agent &rarr; ExposurePathway &rarr; HostPopulation &rarr; Mechanism &rarr; Biomarker &rarr; ClinicalOutcome</code>.
    Every claim is traceable to the exact sentence in the source paper, host populations are first-class nodes, and the graph answers benchmark scientific questions.</p></div>`;
  const nt=Object.entries(S.node_types).sort((a,b)=>b[1]-a[1]);
  const rt=Object.entries(S.rel_types).sort((a,b)=>b[1]-a[1]);
  h+='<div class="panel"><h3>Node types</h3><table><tr><th>Type</th><th>Count</th></tr>'+
     nt.map(([k,v])=>`<tr><td><span class="swatch" style="display:inline-block;background:${colorByType[k]||'var(--other)'}"></span> ${k}</td><td>${v}</td></tr>`).join('')+'</table></div>';
  h+='<div class="panel"><h3>Relationship types</h3><table><tr><th>Relation</th><th>Count</th></tr>'+
     rt.map(([k,v])=>`<tr><td><code>${k}</code></td><td>${v}</td></tr>`).join('')+'</table></div>';
  el.innerHTML=h;
})();

// ---- Benchmark queries ----
(function(){
  const el=document.getElementById('tab-queries');
  let h='';
    h+='<div class="panel"><h3><span class="tag">Q1</span>Which polymers are linked to oxidative stress?</h3>';
    h+=A.q1_polymers_oxidative_stress.map(row=>
      `<div class="chain"><b>${esc(row.polymer)}</b> <span class="pill high">${row.evidence_count} evidence</span><br>${row.path.map(esc).join(' &rarr; ')}
      ${row.supporting_evidence.slice(0,2).map(ev=>`<div class="quote">&ldquo;${esc(ev.evidence)}&rdquo;<br><span style="font-style:normal;color:#667">${esc(ev.study)}</span></div>`).join('')}</div>`).join('<hr style="border:0;border-top:1px solid var(--line)">');
  h+='</div>';
    h+='<div class="panel"><h3><span class="tag">Q2</span>Which tissues/organs are most frequently affected?</h3><table><tr><th>Tissue</th><th>Evidence</th><th>Links</th><th>Studies</th></tr>'+
      A.q2_affected_tissues.map(row=>`<tr><td>${esc(row.tissue)}</td><td>${row.evidence_count}</td><td>${row.links}</td><td>${row.supporting_studies.slice(0,3).map(esc).join('<br>')||'none'}</td></tr>`).join('')+'</table></div>';
    h+='<div class="panel"><h3><span class="tag">Q3</span>Which biomarkers support inflammation?</h3>'+
      A.q3_biomarkers_inflammation.map(row=>`<div class="chain"><span class="pill high">${esc(row.biomarker)}</span> <span class="pill moderate">${row.evidence_count} evidence</span><br>${row.supporting_studies.map(esc).join(', ')||'no direct study'}${row.supporting_evidence.slice(0,1).map(ev=>`<div class="quote">&ldquo;${esc(ev.evidence)}&rdquo;</div>`).join('')}</div>`).join('')+'</div>';
  const q4=A.q4_drinking_water_human_cv;
  h+=`<div class="panel"><h3><span class="tag">Q4</span>Drinking-water MPs &rarr; human cardiovascular outcomes?</h3>
      <div class="verdict">${esc(q4.verdict)}</div>
      <table style="margin-top:10px">
      <tr><td>Human evidence</td><td>${esc(q4.human_evidence)}</td></tr>
      <tr><td>Human hosts in graph</td><td>${q4.human_hosts.map(esc).join(', ')||'none'}</td></tr>
      <tr><td>Cardiovascular outcomes</td><td>${q4.cardiovascular_outcomes_in_graph.map(esc).join(', ')||'none'}</td></tr>
      <tr><td>Drinking-water nodes</td><td>${q4.drinking_water_nodes_in_graph.map(esc).join(', ')||'none'}</td></tr>
      <tr><td>Supporting studies</td><td>${q4.supporting_studies.map(esc).join(', ')||'none'}</td></tr>
      </table></div>`;
  el.innerHTML=h;
})();

// ---- Evidence weighting ----
(function(){
  const el=document.getElementById('tab-weighting');
  const cls=t=>t==='high'?'high':t==='moderate'?'moderate':t.indexOf('null')>=0?'nullf':'low';
  let h='<div class="panel"><h3>Evidence weighting &amp; confidence scoring</h3>'+
    '<p style="font-size:12.5px;color:var(--muted)">Score = strength &times; consistency &times; causal confidence &times; host translational weight (normalised 0&ndash;1). '+
    'All claims here are <b>limited/low</b> &mdash; faithful to a conservative review.</p>'+
    '<table><tr><th>Tier</th><th>Score</th><th>Relationship</th><th>Claim</th></tr>'+
    A.evidence_weighting.map(r=>`<tr><td><span class="pill ${cls(r.tier)}">${esc(r.tier)}</span></td>
      <td>${r.score}</td><td><code>${esc(r.relationship)}</code></td><td>${esc(r.claim)}&hellip;</td></tr>`).join('')+
    '</table></div>';
  el.innerHTML=h;
})();

// ---- Human vs animal ----
(function(){
  const el=document.getElementById('tab-ranking');
  const r=A.human_vs_animal; const maxW=Math.max(...Object.values(r).map(x=>x.aggregate_translational_weight));
  let h='<div class="cards">';
  for(const [k,v] of Object.entries(r))
    h+=`<div class="card"><div class="n">${v.n_hosts}</div><div class="l">${k.toUpperCase()} hosts &middot; weight ${v.aggregate_translational_weight}</div></div>`;
  h+='</div>';
  for(const [k,v] of Object.entries(r)){
    h+=`<div class="panel"><h3>${k.toUpperCase()} evidence</h3>
      <div class="bar" style="width:${Math.round(100*v.aggregate_translational_weight/maxW)}%"></div>
      <table style="margin-top:10px">
      <tr><td style="width:160px">Hosts (${v.n_hosts})</td><td>${v.hosts.map(esc).join(', ')}</td></tr>
      <tr><td>Biomarkers</td><td>${v.biomarkers.map(b=>`<span class="pill moderate">${esc(b)}</span>`).join(' ')||'none'}</td></tr>
      <tr><td>Outcomes</td><td>${v.outcomes.map(esc).join(', ')||'none'}</td></tr>
      <tr><td>Evidence nodes</td><td>${v.evidence_nodes}</td></tr>
      <tr><td>Translational weight</td><td><b>${v.aggregate_translational_weight}</b></td></tr>
      </table></div>`;
  }
  el.innerHTML=h;
})();

// ---- Provenance ----
(function(){
  const el=document.getElementById('tab-provenance');
  let h='<div class="panel"><h3>Study &rarr; Evidence &rarr; Observation traceability</h3>'+
    '<p style="font-size:12.5px;color:var(--muted)">The professor\'s key requirement: which exact sentence supports each claim.</p></div>';
  h+=A.provenance.map(p=>`<div class="panel">
    <h3>${esc(p.study)}</h3>
    <div style="font-size:12px;color:var(--muted)">${esc(p.section)} &middot; confidence: <b>${esc(p.confidence)}</b></div>
    <div class="quote">&ldquo;${esc(p.evidence)}&rdquo;</div>
    <div style="font-size:12.5px">&rarr; supports observation <code>${esc(p.observation_id)}</code><br>
    <span style="color:#555">${esc(p.observation)}</span></div></div>`).join('');
  el.innerHTML=h;
})();

// ---- Interactive graph (lazy) ----
let graphReady=false;
function ensureGraph(){ if(graphReady) return; graphReady=true; initGraph(DATA.graph); }
function initGraph(graph){
  const svg=document.getElementById('graph'), details=document.getElementById('details');
  const search=document.getElementById('search'), typeFilter=document.getElementById('typeFilter');
  const types=[...new Set(graph.nodes.map(n=>n.type))].sort();
  const legend=document.getElementById('legend');
  for(const t of types){
    const o=document.createElement('option');o.value=t;o.textContent=t;typeFilter.appendChild(o);
    const s=document.createElement('span');
    s.innerHTML=`<i class="swatch" style="background:${colorByType[t]||'var(--other)'}"></i>${t}`;legend.appendChild(s);
  }
  const nodes=graph.nodes.map(n=>({...n}));
  const byId=new Map(nodes.map(n=>[n.id,n]));
  const links=graph.edges.filter(e=>e.valid).map(e=>({...e,source:byId.get(e.source),target:byId.get(e.target)}));
  const adj=new Map(nodes.map(n=>[n.id,new Set()]));
  links.forEach(l=>{adj.get(l.source.id).add(l.target.id);adj.get(l.target.id).add(l.source.id);});
  let selected=null, tf={x:0,y:0,scale:1};
  const W=()=>svg.clientWidth||900, H=()=>svg.clientHeight||620, ns='http://www.w3.org/2000/svg';
  svg.innerHTML='<defs><marker id="arrow" viewBox="0 -5 10 10" refX="18" refY="0" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,-5L10,0L0,5" fill="#9aa8b5"></path></marker></defs>';
  const vp=document.createElementNS(ns,'g'),eL=document.createElementNS(ns,'g'),lL=document.createElementNS(ns,'g'),nL=document.createElementNS(ns,'g');
  vp.append(eL,lL,nL);svg.appendChild(vp);
  const rad=n=>n.type==='Study'?13:(n.type==='Observation'||n.type==='Association'||n.type==='Evidence'||n.type==='HostPopulation'?9:7);
  const trunc=(v,m)=>v.length>m?v.slice(0,m-1)+'...':v;
  const edgeEls=links.map(link=>{
    const p=document.createElementNS(ns,'path');p.classList.add('link');p.setAttribute('marker-end','url(#arrow)');eL.appendChild(p);
    const t=document.createElementNS(ns,'text');t.classList.add('link-label');t.textContent=link.label;lL.appendChild(t);
    return{path:p,label:t,link};});
  const nodeEls=nodes.map(node=>{
    const grp=document.createElementNS(ns,'g');grp.classList.add('node');
    const c=document.createElementNS(ns,'circle');c.setAttribute('r',rad(node));c.setAttribute('fill',colorByType[node.type]||'var(--other)');
    const t=document.createElementNS(ns,'text');t.setAttribute('x',rad(node)+4);t.setAttribute('y',3);t.textContent=trunc(node.label,32);
    grp.append(c,t);grp.addEventListener('click',()=>sel(node));nL.appendChild(grp);return{group:grp,node};});
  seed(nodes,W(),H());layout(nodes,links,W(),H(),420);tick();
  search.oninput=filt;typeFilter.onchange=filt;
  let pan=false,last=null;
  svg.addEventListener('pointerdown',e=>{if(e.target.closest('.node'))return;pan=true;last={x:e.clientX,y:e.clientY};svg.setPointerCapture(e.pointerId);});
  svg.addEventListener('pointermove',e=>{if(!pan)return;tf.x+=e.clientX-last.x;tf.y+=e.clientY-last.y;last={x:e.clientX,y:e.clientY};upd();});
  svg.addEventListener('pointerup',()=>pan=false);
  svg.addEventListener('wheel',e=>{e.preventDefault();tf.scale=Math.max(.35,Math.min(2.4,tf.scale*(e.deltaY>0?.9:1.1)));upd();},{passive:false});
  function tick(){
    for(const{path,label,link}of edgeEls){
      const dx=link.target.x-link.source.x,dy=link.target.y-link.source.y,dr=Math.sqrt(dx*dx+dy*dy)*1.35;
      path.setAttribute('d','M'+link.source.x+','+link.source.y+'A'+dr+','+dr+' 0 0,1 '+link.target.x+','+link.target.y);
      label.setAttribute('x',(link.source.x+link.target.x)/2);label.setAttribute('y',(link.source.y+link.target.y)/2-4);}
    for(const{group,node}of nodeEls)group.setAttribute('transform','translate('+node.x+','+node.y+')');}
  function sel(node){selected=node;
    details.innerHTML='<b>'+esc(node.label)+'</b><div style="color:var(--muted);font-size:12px">'+esc(node.type)+' &middot; '+esc(node.id)+'</div><pre>'+esc(JSON.stringify(node.data,null,2))+'</pre>';filt();}
  function filt(){
    const q=search.value.trim().toLowerCase(),ty=typeFilter.value;
    const vis=new Set(nodes.filter(n=>{const t=(n.id+' '+n.label+' '+n.type).toLowerCase();return(!q||t.includes(q))&&(!ty||n.type===ty);}).map(n=>n.id));
    const rel=selected?adj.get(selected.id):null;
    for(const it of nodeEls){const f=!vis.has(it.node.id),u=selected&&it.node.id!==selected.id&&!rel.has(it.node.id);
      it.group.classList.toggle('dim',f||u);it.group.classList.toggle('selected',selected&&it.node.id===selected.id);}
    for(const it of edgeEls){const f=!vis.has(it.link.source.id)||!vis.has(it.link.target.id);
      const u=selected&&it.link.source.id!==selected.id&&it.link.target.id!==selected.id;
      it.path.classList.toggle('dim',f||u);it.label.classList.toggle('dim',f||u);}}
  function upd(){vp.setAttribute('transform','translate('+tf.x+','+tf.y+') scale('+tf.scale+')');}
  function seed(nodes,w,h){const cx=w/2,cy=h/2;nodes.forEach((n,i)=>{const a=(i/nodes.length)*Math.PI*2,r=Math.min(w,h)*(.18+(i%5)*.035);n.x=cx+Math.cos(a)*r;n.y=cy+Math.sin(a)*r;n.vx=0;n.vy=0;});}
  function layout(nodes,links,w,h,steps){const cx=w/2,cy=h/2;
    for(let s=0;s<steps;s++){const al=1-s/steps;
      for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){const a=nodes[i],b=nodes[j];let dx=b.x-a.x,dy=b.y-a.y,d=Math.sqrt(dx*dx+dy*dy)||1;const f=(720/(d*d))*al;dx/=d;dy/=d;a.vx-=dx*f;a.vy-=dy*f;b.vx+=dx*f;b.vy+=dy*f;}
      for(const l of links){const dx=l.target.x-l.source.x,dy=l.target.y-l.source.y,d=Math.sqrt(dx*dx+dy*dy)||1,f=(d-116)*.014*al;l.source.vx+=dx/d*f;l.source.vy+=dy/d*f;l.target.vx-=dx/d*f;l.target.vy-=dy/d*f;}
      for(const n of nodes){n.vx+=(cx-n.x)*.003*al;n.vy+=(cy-n.y)*.003*al;n.vx*=.82;n.vy*=.82;n.x=Math.max(36,Math.min(w-36,n.x+n.vx));n.y=Math.max(36,Math.min(h-36,n.y+n.vy));}}}
}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
