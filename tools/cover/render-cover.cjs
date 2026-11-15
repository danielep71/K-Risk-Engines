// Renders assets/K-Risk-Engines-social-preview-v4.jpg, the nine-project cover
// (1774 x 887), with headless Chromium and Playwright. From the repository root:
//   node tools/cover/render-cover.cjs
// The page loads the Oswald and JetBrains Mono fonts (SIL OFL 1.1) from Google
// Fonts, so the run needs network access; it stops if either font is missing.
//
// This Source Code Form is subject to the terms of the Mozilla Public License,
// v. 2.0. If a copy of the MPL was not distributed with this file, You can
// obtain one at https://mozilla.org/MPL/2.0/.
const { chromium } = require('playwright');

const OUTPUT = 'assets/K-Risk-Engines-social-preview-v4.jpg';
const SHELL = [
  '<!doctype html><html><head><meta charset="utf-8">',
  '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=JetBrains+Mono:wght@400;500;700&display=block">',
  '<style>html,body{margin:0;background:#050f22}svg{display:block}</style></head><body>',
  '<svg id="s" xmlns="http://www.w3.org/2000/svg" width="1774" height="887" viewBox="0 0 1774 887"></svg>',
  '</body></html>',
].join('');

// Runs in the page: draws the cover into the <svg id="s">.
function draw() {
  const C='#22e6ff', C2='#1aa7ff', INK='#e9f6ff', MUT='#9fc3dd';
  const s = document.getElementById('s');
    let o = '';
  o+=`<defs>
  <radialGradient id="bg" cx="25%" cy="45%" r="85%"><stop offset="0" stop-color="#0b2147"/><stop offset=".55" stop-color="#071834"/><stop offset="1" stop-color="#040c1c"/></radialGradient>
  <linearGradient id="tile" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c2344" stop-opacity=".95"/><stop offset="1" stop-color="#081a35" stop-opacity=".95"/></linearGradient>
  <linearGradient id="bar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${C}" stop-opacity=".95"/><stop offset="1" stop-color="${C2}" stop-opacity=".15"/></linearGradient>
  <filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="9"/></filter>
  <pattern id="grid" width="44" height="44" patternUnits="userSpaceOnUse"><path d="M44 0H0V44" fill="none" stroke="#1d3d6b" stroke-opacity=".35" stroke-width="1"/></pattern>
  </defs>
  <rect width="1774" height="887" fill="url(#bg)"/><rect width="1774" height="887" fill="url(#grid)"/>`;
  // left block
  o+=`<g filter="url(#glow)"><rect x="92" y="118" width="122" height="122" rx="20" fill="#071a38" stroke="${C}" stroke-width="5"/></g>
  <text x="110" y="210" font-family="Oswald" font-weight="700" font-size="92" fill="${INK}">K</text>
  <g fill="${C}" filter="url(#glow)"><rect x="164" y="150" width="32" height="11" rx="4"/><rect x="164" y="173" width="32" height="11" rx="4"/><rect x="164" y="196" width="32" height="11" rx="4" fill="${C2}"/></g>
  <text x="86" y="420" font-family="Oswald" font-weight="700" font-size="134" letter-spacing="1" fill="${INK}">K-RISK</text>
  <text x="86" y="560" font-family="Oswald" font-weight="700" font-size="134" letter-spacing="1" fill="${INK}">ENGINES</text>
  <text x="90" y="628" font-family="Oswald" font-weight="600" font-size="36" letter-spacing="4.5" fill="${C}" filter="url(#glow)">FINANCIAL RISK MODELS</text>
  <text x="90" y="684" font-family="JetBrains Mono" font-weight="400" font-size="19" fill="${MUT}">Transparent methods. Traceable results.</text>`;
  // right block
  const X0=600, CW=318, TX=964, TW=772, RY=[34,248,462,676], RH=184, G=18;
  const rows=[
   ['COUNTERPARTY','CREDIT RISK',[['K-SACCR','Derivatives exposure','saccr'],['K-SFTs','Securities financing','sfts']]],
   ['MARKET RISK','',[['K-FRTB-SA','Standardised approach','frtb'],['K-FRTB-SSA','Simplified approach','ssa'],['K-CVA','CVA risk','cva']]],
   ['IRRBB','',[['K-IRRBB NMDs','Non-maturity deposits','nmd'],['K-IRRBB Prepayment','Loan prepayments','prep']]],
   ['LIQUIDITY RISK','',[['K-LCR','Liquidity Coverage Ratio','lcr'],['K-NSFR','Net Stable Funding Ratio','nsfr']]]];
  function icon(k,x,y,w,h){ // area x,y,w,h
   let g='', st=`fill="none" stroke="${C}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"`;
   const cx=x+w/2;
   if(k==='saccr'){let d='';for(let i=0;i<=60;i++){const t=i/60,xx=x+w*t,yy=y+h-6-(h-16)*Math.exp(-((t-.5)**2)/.025);d+=(i?'L':'M')+xx.toFixed(1)+' '+yy.toFixed(1);} g+=`<path d="${d}" ${st}/>`;for(let i=1;i<8;i++){const xx=x+w*i/8;g+=`<line x1="${xx}" y1="${y+h}" x2="${xx}" y2="${y+h-6-(h-16)*Math.exp(-((i/8-.5)**2)/.025)}" stroke="${C2}" stroke-opacity=".45" stroke-width="1.5"/>`;} g+=`<line x1="${x}" y1="${y+h}" x2="${x+w}" y2="${y+h}" stroke="${C2}" stroke-opacity=".6" stroke-width="1.5"/>`;}
   if(k==='sfts'){for(let i=0;i<3;i++){g+=`<rect x="${x+w*.08+i*10}" y="${y+8+i*9}" width="${w*.34}" height="${h*.62}" rx="4" fill="#0a2246" ${st} stroke-opacity="${.5+i*.25}"/>`;} const dx=x+w*.12+20, dy=y+26;for(let j=0;j<3;j++) g+=`<line x1="${dx+8}" y1="${dy+14+j*12}" x2="${dx+w*.24}" y2="${dy+14+j*12}" stroke="${C2}" stroke-width="2"/>`;
    g+=`<path d="M${x+w*.5} ${y+h*.3} Q ${x+w*.62} ${y+h*.02} ${x+w*.74} ${y+h*.3}" ${st}/><path d="M${x+w*.69} ${y+h*.25} L${x+w*.74} ${y+h*.3} L${x+w*.755} ${y+h*.22}" ${st}/><path d="M${x+w*.74} ${y+h*.5} Q ${x+w*.62} ${y+h*.78} ${x+w*.5} ${y+h*.5}" ${st} stroke-opacity=".6"/>`;
    for(let i=0;i<4;i++) g+=`<ellipse cx="${x+w*.82}" cy="${y+h*.86-i*11}" rx="${w*.11}" ry="7" fill="#0a2246" ${st}/>`;}
   if(k==='frtb'){const sk=w*.18; for(let i=0;i<=5;i++){const yy=y+h*.25+i*h*.13;g+=`<line x1="${x+sk*(1-i/5)}" y1="${yy}" x2="${x+w-sk*(i/5)}" y2="${yy}" stroke="${C2}" stroke-opacity=".4" stroke-width="1.3"/>`;} for(let i=0;i<=7;i++){g+=`<line x1="${x+sk+i*(w-2*sk)/7}" y1="${y+h*.25}" x2="${x+i*(w-2*sk)/7+ (i/7)*sk*0}" y2="${y+h*.9}" stroke="${C2}" stroke-opacity=".3" stroke-width="1.2"/>`;}
    let d='',pts=[.62,.55,.66,.48,.52,.36,.4,.22,.28,.12];pts.forEach((p,i)=>{d+=(i?'L':'M')+(x+w*(.05+i*.1)).toFixed(1)+' '+(y+h*p).toFixed(1);});g+=`<path d="${d}" ${st}/>`;pts.forEach((p,i)=>{if(i%3==0)g+=`<circle cx="${x+w*(.05+i*.1)}" cy="${y+h*p}" r="3.5" fill="${C}"/>`;});}
   if(k==='ssa'){const hs=[.55,.75,.4,.62];const bw=w*.1;hs.forEach((v,i)=>{const bx=x+w*.04+i*(bw+w*.05);g+=`<rect x="${bx}" y="${y+h*(1-v)}" width="${bw}" height="${h*v}" rx="3" fill="url(#bar)" stroke="${C}" stroke-width="1.6"/>`;});
    g+=`<text x="${x+w*.66}" y="${y+h*.72}" font-family="Oswald" font-weight="600" font-size="${h*.62}" fill="${C}" filter="url(#glow)">Σ</text>`;}
   if(k==='cva'){for(let i=0;i<3;i++){const yy=y+h*.28+i*h*.22;g+=`<path d="M${cx} ${yy-h*.2} L${cx+w*.36} ${yy} L${cx} ${yy+h*.2} L${cx-w*.36} ${yy} Z" fill="#0a2246" fill-opacity=".85" ${st} stroke-opacity="${1-i*.2}"/>`;}}
   if(k==='nmd'){for(let i=0;i<9;i++){const y0=y+h*(.1+i*.1);g+=`<path d="M${x} ${y0} C ${x+w*.45} ${y0}, ${x+w*.5} ${y+h*.55}, ${x+w*.88} ${y+h*.55}" fill="none" stroke="${C2}" stroke-opacity="${.35+i*.07}" stroke-width="1.8"/>`;} g+=`<line x1="${x+w*.88}" y1="${y+h*.55}" x2="${x+w}" y2="${y+h*.55}" ${st}/><circle cx="${x+w*.9}" cy="${y+h*.55}" r="5" fill="${C}" filter="url(#glow)"/>`;}
   if(k==='prep'){for(let i=0;i<9;i++){const y1=y+h*(.12+i*.075);g+=`<path d="M${x} ${y+h*.92} C ${x+w*.5} ${y+h*.9}, ${x+w*.55} ${y1}, ${x+w*.96} ${y1}" fill="none" stroke="${C2}" stroke-opacity="${.3+i*.08}" stroke-width="1.8"/>`;} g+=`<circle cx="${x+w*.96}" cy="${y+h*.12}" r="5" fill="${C}" filter="url(#glow)"/>`;}
   if(k==='lcr'){const n=7;for(let i=0;i<n;i++){const v=.18+i*.12,bw=w*.09;const bx=x+w*.06+i*w*.13;g+=`<rect x="${bx}" y="${y+h*(1-v)}" width="${bw}" height="${h*v}" rx="2" fill="url(#bar)" stroke="${C}" stroke-opacity=".8" stroke-width="1.3"/>`;} let d='';for(let i=0;i<n;i++){d+=(i?'L':'M')+(x+w*.105+i*w*.13).toFixed(1)+' '+(y+h*(1-(.18+i*.12))-8).toFixed(1);} g+=`<path d="${d}" ${st}/>`;}
   if(k==='nsfr'){const vs=[.25,.35,.3,.45,.55,.62,.8];vs.forEach((v,i)=>{const bw=w*.09,bx=x+w*.06+i*w*.13;g+=`<rect x="${bx}" y="${y+h*(1-v)}" width="${bw}" height="${h*v}" rx="2" fill="url(#bar)" stroke="${C}" stroke-opacity=".8" stroke-width="1.3"/>`;});
    g+=`<path d="M${x+w*.02} ${y+h*.85} C ${x+w*.45} ${y+h*.8}, ${x+w*.65} ${y+h*.45}, ${x+w*.98} ${y+h*.05}" ${st}/>`;}
   return `<g filter="url(#glow)">${g}</g>`;
  }
  rows.forEach(([a,b,tiles],r)=>{const y=RY[r];
   o+=`<rect x="${X0}" y="${y}" width="${CW}" height="${RH}" rx="12" fill="url(#tile)" stroke="${C}" stroke-opacity=".75" stroke-width="2"/>`;
   o+=`<rect x="${X0+26}" y="${y+46}" width="6" height="${RH-92}" rx="3" fill="${C}" filter="url(#glow)"/>`;
   if(b){o+=`<text x="${X0+52}" y="${y+RH/2-6}" font-family="Oswald" font-weight="600" font-size="34" letter-spacing="1.5" fill="${C}">${a}</text><text x="${X0+52}" y="${y+RH/2+36}" font-family="Oswald" font-weight="600" font-size="34" letter-spacing="1.5" fill="${C}">${b}</text>`;}
   else o+=`<text x="${X0+52}" y="${y+RH/2+13}" font-family="Oswald" font-weight="600" font-size="36" letter-spacing="1.5" fill="${C}">${a}</text>`;
   const n=tiles.length, tw=(TW-(n-1)*G)/n;
   o+=`<line x1="${X0+CW}" y1="${y+RH/2}" x2="${TX}" y2="${y+RH/2}" stroke="${C}" stroke-opacity=".7" stroke-width="2"/><circle cx="${X0+CW}" cy="${y+RH/2}" r="4" fill="${C}"/><circle cx="${TX}" cy="${y+RH/2}" r="4" fill="${C}"/>`;
   tiles.forEach(([name,sub,k],i)=>{const x=TX+i*(tw+G);
    o+=`<rect x="${x}" y="${y}" width="${tw}" height="${RH}" rx="12" fill="url(#tile)" stroke="${C}" stroke-opacity=".55" stroke-width="1.6"/>`;
    o+=icon(k,x+22,y+16,tw-44,RH*.48);
    const fs = name.length>14 ? 25 : 28;
    o+=`<text x="${x+22}" y="${y+RH-48}" font-family="JetBrains Mono" font-weight="700" font-size="${fs}" fill="${INK}">${name}</text>`;
    o+=`<text x="${x+22}" y="${y+RH-20}" font-family="JetBrains Mono" font-weight="400" font-size="${n>2?15:17}" fill="${MUT}">${sub}</text>`;
   });
  });
  s.innerHTML=o;
}

(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 1774, height: 887 }, deviceScaleFactor: 1 });
    await page.setContent(SHELL, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.evaluate(draw);
    await page.evaluate(() => document.fonts.ready);
    const loaded = await page.evaluate(() => [...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family));
    for (const family of ['Oswald', 'JetBrains Mono']) {
      if (!loaded.includes(family)) throw new Error(`Font not loaded: ${family}`);
    }
    await page.locator('#s').screenshot({ path: OUTPUT, type: 'jpeg', quality: 92 });
    console.log(`Wrote ${OUTPUT}`);
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
