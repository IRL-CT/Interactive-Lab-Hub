// Petal atlas generator, as shipped in the Claude Design project "Petal Sheet"
// (https://claude.ai/design/p/bbb2e47b-cd05-4434-ad01-5e2dc8598e27, tools/gen-petals.js).
// Deterministic: seeded, so running it reproduces the same SVGs. Run: node gen-petals.js
function buildAll(){
const BASEY=250;
const lerpProfile=(prof,t)=>{for(let i=0;i<prof.length-1;i++){const[a,va]=prof[i],[b,vb]=prof[i+1];if(t<=b){const k=(t-a)/(b-a||1);return va+(vb-va)*k;}}return prof[prof.length-1][1];};
function cr(pts){let d=`M ${pts[0][0].toFixed(2)} ${pts[0][1].toFixed(2)}`;
  for(let i=0;i<pts.length-1;i++){const p0=pts[i-1]||pts[i],p1=pts[i],p2=pts[i+1],p3=pts[i+2]||pts[i+1];
    const c1=[p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6],c2=[p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6];
    d+=` C ${c1[0].toFixed(2)} ${c1[1].toFixed(2)} ${c2[0].toFixed(2)} ${c2[1].toFixed(2)} ${p2[0].toFixed(2)} ${p2[1].toFixed(2)}`;}
  return d;}
const rnd=s=>{let x=s;return()=>{x=(x*16807)%2147483647;return x/2147483647;};};

function geom(c){
  const N=30,tipY=c.tipY??26;
  const bend=t=>c.bend*Math.pow(t,1.5)+(c.curl||0)*Math.pow(t,5);
  const cxAt=t=>128+bend(t), yAt=t=>BASEY-t*(BASEY-tipY), wAt=t=>c.W*lerpProfile(c.profile,t);
  const asym=t=>1+(c.asym||0)*t;
  const R=[],L=[];
  for(let i=0;i<=N;i++){const t=i/N,cx=cxAt(t),w=wAt(t)/2;R.push([cx+w*asym(t),yAt(t)]);L.push([cx-w/asym(t),yAt(t)]);}
  const cxT=cxAt(1),wT=wAt(1),yT=yAt(1);let cap;
  if(c.cap==='notch')cap=[[cxT+wT*0.36,yT-12],[cxT+wT*0.16,yT-6],[cxT,yT+(c.notch??10)],[cxT-wT*0.16,yT-6],[cxT-wT*0.36,yT-12]];
  else if(c.cap==='round')cap=[[cxT+wT*0.34,yT-6],[cxT+(c.tipShift||0),yT-13],[cxT-wT*0.34,yT-6]];
  else cap=[[cxT+(c.tipShift||0)*0.5,yT-(c.point??16)]];
  return {d:cr([...R,...cap,...L.reverse()])+' Z',cxAt,yAt,wAt,bend};
}
const svg=(defs,body)=>`<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
<defs>
${defs}
</defs>
${body}
</svg>
`;
const vgrad=(id,stops)=>`<linearGradient id="${id}" gradientUnits="userSpaceOnUse" x1="0" y1="${BASEY}" x2="0" y2="8">`+
  stops.map(([o,a])=>`<stop offset="${o}" stop-color="#ffffff" stop-opacity="${a}"/>`).join('')+`</linearGradient>`;
const wc=(seed,disp,grain,amp,blur)=>`<filter id="wc" x="-24%" y="-24%" width="148%" height="148%" color-interpolation-filters="sRGB">
  <feTurbulence type="fractalNoise" baseFrequency="0.013 0.019" numOctaves="3" seed="${seed}" result="n1"/>
  <feDisplacementMap in="SourceGraphic" in2="n1" scale="${disp}" xChannelSelector="R" yChannelSelector="G" result="d"/>
  <feTurbulence type="fractalNoise" baseFrequency="${grain}" numOctaves="5" seed="${seed+41}" result="n2"/>
  <feColorMatrix in="n2" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  ${amp} ${(amp*0.7).toFixed(3)} 0 0 ${(1-amp*0.85).toFixed(3)}" result="mot"/>
  <feComposite in="d" in2="mot" operator="arithmetic" k1="1" k2="0" k3="0" k4="0" result="g"/>
  <feGaussianBlur in="g" stdDeviation="${blur}"/>
</filter>`;

const SPECIES={
 cherry:{W:156,cap:'notch',tipY:30,grad:[[0,0.18],[0.3,0.42],[0.68,0.68],[0.92,0.82],[1,0.74]],
  disp:4,grain:0.85,amp:0.26,blur:0.5,feather:2.2,rim:0.16,
  variants:[
   {v:'a',profile:[[0,0.10],[0.16,0.46],[0.38,0.82],[0.58,0.98],[0.8,0.92],[0.94,0.7],[1,0.5]],bend:5,notch:10,seed:3},
   {v:'b',profile:[[0,0.09],[0.2,0.4],[0.44,0.74],[0.66,0.95],[0.86,0.86],[1,0.44]],bend:-12,notch:7,seed:11,W:144},
   {v:'c',profile:[[0,0.13],[0.14,0.52],[0.34,0.88],[0.56,1.0],[0.8,0.94],[0.93,0.76],[1,0.58]],bend:14,notch:14,seed:23,W:162}],
  veins:5,veinAlpha:0.13,blobs:3},
 daisy:{W:48,cap:'round',tipY:28,grad:[[0,0.4],[0.35,0.62],[0.75,0.7],[1,0.56]],
  disp:3.5,grain:1.0,amp:0.2,blur:0.5,feather:2,rim:0.14,edgeFade:true,
  variants:[
   {v:'a',profile:[[0,0.16],[0.22,0.5],[0.55,0.86],[0.8,1.0],[1,0.78]],bend:4,seed:5},
   {v:'b',profile:[[0,0.12],[0.25,0.42],[0.6,0.8],[0.85,0.98],[1,0.66]],bend:-9,seed:14,W:44,tipShift:-3},
   {v:'c',profile:[[0,0.2],[0.2,0.56],[0.5,0.9],[0.82,1.0],[1,0.84]],bend:11,seed:29,W:52,tipShift:4}],
  crease:0.2,blobs:2},
 chrysanthemum:{W:62,cap:'round',tipY:26,grad:[[0,0.32],[0.4,0.56],[0.8,0.72],[1,0.62]],
  disp:3.5,grain:0.95,amp:0.22,blur:0.5,feather:2,rim:0.15,
  variants:[
   {v:'a',profile:[[0,0.28],[0.2,0.44],[0.5,0.5],[0.76,0.86],[0.92,1.0],[1,0.66]],bend:24,curl:20,asym:0.18,seed:7,tipShift:7},
   {v:'b',profile:[[0,0.32],[0.24,0.5],[0.55,0.52],[0.8,0.9],[0.94,1.0],[1,0.6]],bend:-30,curl:-24,asym:-0.2,seed:17,W:56,tipShift:-8},
   {v:'c',profile:[[0,0.24],[0.18,0.42],[0.48,0.54],[0.78,0.9],[0.95,1.0],[1,0.72]],bend:13,curl:28,asym:0.11,seed:31,W:66,tipShift:5}],
  crease:0.16,blobs:2},
 star:{W:98,cap:'point',tipY:26,grad:[[0,0.56],[0.22,0.68],[0.6,0.7],[1,0.5]],
  disp:4,grain:0.85,amp:0.22,blur:0.7,feather:3,rim:0.12,glow:true,
  variants:[
   {v:'a',profile:[[0,0.3],[0.24,0.9],[0.5,1.0],[0.78,0.52],[1,0.04]],bend:5,seed:9,point:18},
   {v:'b',profile:[[0,0.26],[0.28,0.84],[0.55,1.0],[0.82,0.44],[1,0.03]],bend:-11,seed:19,W:90,point:22,tipShift:-6},
   {v:'c',profile:[[0,0.34],[0.2,0.94],[0.48,1.0],[0.76,0.6],[1,0.06]],bend:13,seed:37,W:104,point:15,tipShift:5}],
  crease:0.13,blobs:2}
};

const files={};
for(const [name,S] of Object.entries(SPECIES)){
 for(const V of S.variants){
  const c={...S,...V},g=geom(c),r=rnd(V.seed*97+13);
  let defs=vgrad('body',S.grad)
   +`\n<filter id="fb" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="${S.feather}"/></filter>`
   +`\n<mask id="sm" maskUnits="userSpaceOnUse" x="0" y="0" width="256" height="256"><path d="${g.d}" fill="#ffffff" filter="url(#fb)"/></mask>`
   +'\n'+wc(V.seed,S.disp,S.grain,S.amp,S.blur);
  let blobs='';
  for(let i=0;i<S.blobs;i++){
   const t=0.3+r()*0.6,cx=g.cxAt(t)+(r()-0.5)*g.wAt(t)*0.3,cy=g.yAt(t),rr=(g.wAt(t)*(0.4+r()*0.35)).toFixed(1);
   defs+=`\n<radialGradient id="p${i}" gradientUnits="userSpaceOnUse" cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${rr}"><stop offset="0" stop-color="#ffffff" stop-opacity="${(0.1+r()*0.14).toFixed(2)}"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>`;
   blobs+=`<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="${rr}" fill="url(#p${i})"/>`;
  }
  const lineAt=off=>{const p=[];for(let i=0;i<=14;i++){const t=i/14;p.push([g.cxAt(t)+off*g.wAt(t)/2,g.yAt(t)-3]);}return cr(p);};
  let lines='';
  if(name==='cherry'){[-0.62,-0.32,0,0.32,0.62].forEach(o=>{lines+=`<path d="${lineAt(o)}" fill="none" stroke="#ffffff" stroke-opacity="${(S.veinAlpha*(o===0?1.5:1)).toFixed(2)}" stroke-width="${o===0?1.4:0.95}" stroke-linecap="round"/>`;});}
  else{lines+=`<path d="${lineAt(0)}" fill="none" stroke="#ffffff" stroke-opacity="${S.crease}" stroke-width="${name==='daisy'?2.2:1.6}" stroke-linecap="round"/>`;}
  defs+=`\n<filter id="vb" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.4"/></filter>`
   +`\n<filter id="rb" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="1.8"/></filter>`;
  let inner=`<rect x="0" y="0" width="256" height="256" fill="url(#body)"/>\n    ${blobs}\n    <g filter="url(#vb)">${lines}</g>`;
  const rim=`\n  <path d="${g.d}" fill="none" stroke="#ffffff" stroke-opacity="${S.rim}" stroke-width="2" filter="url(#rb)"/>`;
  let body;
  if(S.edgeFade){
   const cxm=128+g.bend(0.5),half=c.W*0.62;
   defs+=`\n<linearGradient id="ef" gradientUnits="userSpaceOnUse" x1="${(cxm-half).toFixed(1)}" y1="0" x2="${(cxm+half).toFixed(1)}" y2="0"><stop offset="0" stop-color="#5c5c5c"/><stop offset="0.32" stop-color="#ffffff"/><stop offset="0.68" stop-color="#ffffff"/><stop offset="1" stop-color="#5c5c5c"/></linearGradient>
<mask id="em" maskUnits="userSpaceOnUse" x="0" y="0" width="256" height="256"><rect width="256" height="256" fill="url(#ef)"/></mask>`;
   body=`<g filter="url(#wc)"><g mask="url(#em)"><g mask="url(#sm)">\n    ${inner}\n  </g>${rim}</g></g>`;
  } else {
   let extra='';
   if(S.glow){
    defs+=`\n<radialGradient id="gl" gradientUnits="userSpaceOnUse" cx="${(128+g.bend(0.05)).toFixed(1)}" cy="236" r="${(c.W*0.5).toFixed(1)}"><stop offset="0" stop-color="#ffffff" stop-opacity="0.55"/><stop offset="0.5" stop-color="#ffffff" stop-opacity="0.22"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>`;
    extra=`\n  <circle cx="${(128+g.bend(0.05)).toFixed(1)}" cy="236" r="${(c.W*0.5).toFixed(1)}" fill="url(#gl)"/>`;
   }
   body=`<g filter="url(#wc)"><g mask="url(#sm)">\n    ${inner}\n  </g>${rim}${extra}</g>`;
  }
  files[`${name}-${V.v}.svg`]=svg(defs,body);
 }
}

{ // cherry centre: small dark disc + stamen dots
 const r=rnd(101);let st='';
 for(let i=0;i<15;i++){const a=(i/15)*Math.PI*2+r()*0.25,len=40+r()*20;
  const x=128+Math.cos(a)*len,y=128+Math.sin(a)*len,mx=128+Math.cos(a+0.2)*len*0.55,my=128+Math.sin(a+0.2)*len*0.55;
  st+=`<path d="M 128 128 Q ${mx.toFixed(1)} ${my.toFixed(1)} ${x.toFixed(1)} ${y.toFixed(1)}" fill="none" stroke="#ffffff" stroke-opacity="0.3" stroke-width="1.1"/>`+
      `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(2.4+r()*1.5).toFixed(1)}" fill="#ffffff" fill-opacity="${(0.65+r()*0.3).toFixed(2)}"/>`;}
 const defs=wc(61,3,1.1,0.16,0.6)+
 `\n<radialGradient id="disc" gradientUnits="userSpaceOnUse" cx="128" cy="128" r="32"><stop offset="0" stop-color="#121212" stop-opacity="0.9"/><stop offset="0.6" stop-color="#2a2a2a" stop-opacity="0.72"/><stop offset="1" stop-color="#3a3a3a" stop-opacity="0"/></radialGradient>`;
 files['cherry-centre.svg']=svg(defs,`<g filter="url(#wc)">${st}<circle cx="128" cy="128" r="32" fill="url(#disc)"/></g>`);
}
{ // daisy centre: textured pollen disc
 const r=rnd(211);let dots='';
 for(let i=0;i<190;i++){const a=r()*Math.PI*2,rad=Math.sqrt(r())*54;
  dots+=`<circle cx="${(128+Math.cos(a)*rad).toFixed(1)}" cy="${(128+Math.sin(a)*rad).toFixed(1)}" r="${(0.8+r()*1.6).toFixed(1)}" fill="#ffffff" fill-opacity="${(0.14+r()*0.4).toFixed(2)}"/>`;}
 const defs=wc(71,3,1.3,0.2,0.45)+
 `\n<radialGradient id="pd" gradientUnits="userSpaceOnUse" cx="120" cy="118" r="60"><stop offset="0" stop-color="#ffffff" stop-opacity="0.72"/><stop offset="0.6" stop-color="#ffffff" stop-opacity="0.5"/><stop offset="1" stop-color="#ffffff" stop-opacity="0.08"/></radialGradient>
<filter id="fb" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2.4"/></filter>
<mask id="sm" maskUnits="userSpaceOnUse" x="0" y="0" width="256" height="256"><circle cx="128" cy="128" r="55" fill="#ffffff" filter="url(#fb)"/></mask>`;
 files['daisy-centre.svg']=svg(defs,`<g filter="url(#wc)"><g mask="url(#sm)"><rect width="256" height="256" fill="url(#pd)"/>${dots}</g></g>`);
}
{ // chrysanthemum centre: dense tiny petals
 const r=rnd(307);let p='';
 for(let i=0;i<92;i++){const a=(i/92)*360+r()*5,r0=10+r()*12,r1=r0+20+r()*32,w=2+r()*2.2;
  p+=`<g transform="translate(128,128) rotate(${a.toFixed(1)})"><path d="M ${-w.toFixed(1)} ${-r0.toFixed(1)} Q ${(-w*0.8).toFixed(1)} ${(-(r0+r1)/2).toFixed(1)} 0 ${-r1.toFixed(1)} Q ${(w*0.8).toFixed(1)} ${(-(r0+r1)/2).toFixed(1)} ${w.toFixed(1)} ${-r0.toFixed(1)} Z" fill="#ffffff" fill-opacity="${(0.18+r()*0.34).toFixed(2)}"/></g>`;}
 const defs=wc(83,3,1.0,0.18,0.6)+
 `\n<radialGradient id="cc" gradientUnits="userSpaceOnUse" cx="128" cy="128" r="26"><stop offset="0" stop-color="#ffffff" stop-opacity="0.6"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>`;
 files['chrysanthemum-centre.svg']=svg(defs,`<g filter="url(#wc)">${p}<circle cx="128" cy="128" r="26" fill="url(#cc)"/></g>`);
}
{ // star centre: warm soft heart
 const defs=wc(97,3.5,1.15,0.14,1.4)+
 `\n<radialGradient id="core" gradientUnits="userSpaceOnUse" cx="126" cy="126" r="46"><stop offset="0" stop-color="#ffffff" stop-opacity="0.9"/><stop offset="0.55" stop-color="#ffffff" stop-opacity="0.66"/><stop offset="1" stop-color="#ffffff" stop-opacity="0.24"/></radialGradient>
<radialGradient id="hb" gradientUnits="userSpaceOnUse" cx="128" cy="128" r="84"><stop offset="0" stop-color="#ffffff" stop-opacity="0.34"/><stop offset="0.42" stop-color="#ffffff" stop-opacity="0.16"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>
<filter id="fb" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="4"/></filter>
<mask id="sm" maskUnits="userSpaceOnUse" x="0" y="0" width="256" height="256"><circle cx="128" cy="128" r="46" fill="#ffffff" filter="url(#fb)"/></mask>`;
 files['star-centre.svg']=svg(defs,`<g filter="url(#wc)"><circle cx="128" cy="128" r="84" fill="url(#hb)"/><g mask="url(#sm)"><rect width="256" height="256" fill="url(#core)"/></g></g>`);
}
return files;
}
if (typeof module !== 'undefined' && require.main === module) {
  const fs = require('fs'), path = require('path');
  const files = buildAll();
  for (const [name, svg] of Object.entries(files)) fs.writeFileSync(path.join(__dirname, name), svg);
  console.log('wrote', Object.keys(files).join(' '));
}
