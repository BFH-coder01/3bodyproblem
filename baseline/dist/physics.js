/* SI units: each body has GM=9.80665 m³/s², so one body causes 1g at 1m.
   Newtonian point masses; close encounters are stopped, never softened. */
(function(root){
const MU=9.80665, LIMIT=6, CLOSE=0.015;
function acc(p){const a=Array(6).fill(0);for(let i=0;i<3;i++)for(let j=i+1;j<3;j++){let x=p[j*2]-p[i*2],y=p[j*2+1]-p[i*2+1],r=Math.hypot(x,y);if(r<CLOSE)return null;let f=MU/(r*r*r);a[2*i]+=f*x;a[2*i+1]+=f*y;a[2*j]-=f*x;a[2*j+1]-=f*y;}return a;}
function energy(p,v){let e=v.reduce((s,x)=>s+x*x/2,0);for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)e-=MU/Math.hypot(p[2*i]-p[2*j],p[2*i+1]-p[2*j+1]);return e;}
function preset(type){if(type==='triangle'){let p=[],v=[],r=2,w=Math.sqrt(MU/(Math.sqrt(3)*r*r*r));for(let i=0;i<3;i++){let t=i*2*Math.PI/3;p.push(r*Math.cos(t),r*Math.sin(t));v.push(-w*r*Math.sin(t),w*r*Math.cos(t));}return {p,v,name:'Lagrange triangle'};}let s=2,k=Math.sqrt(MU/s);return {p:[-.97000436*s,.24308753*s,.97000436*s,-.24308753*s,0,0],v:[.466203685*k,.43236573*k,.466203685*k,.43236573*k,-.93240737*k,-.86473146*k],name:'Figure eight'};}
function* grid(n){let pts=[];for(let y=0;y<n;y++)for(let x=0;x<n;x++)pts.push([-3+6*x/(n-1),-3+6*y/(n-1)]);for(let a=0;a<pts.length-2;a++)for(let b=a+1;b<pts.length-1;b++)for(let c=b+1;c<pts.length;c++)yield {p:[...pts[a],...pts[b],...pts[c]],v:Array(6).fill(0),name:`Grid ${a+1}/${b+1}/${c+1}`};}
function rng(seed){let a=seed>>>0;return ()=>{a+=0x6D2B79F5;let t=a;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return ((t^t>>>14)>>>0)/4294967296;};}
function randomState(random,scale){let p;do{p=Array.from({length:6},()=> (random()-.5)*6);}while(!acc(p));let v=Array.from({length:6},()=> (random()-.5)*2*scale);for(let axis=0;axis<2;axis++){let mean=(v[axis]+v[axis+2]+v[axis+4])/3;for(let i=axis;i<6;i+=2)v[i]-=mean;}return {p,v,name:'Seeded positions · at rest'};}
function create(initial,options={}){let p=initial.p.slice(),v=initial.v.slice(),t=0,steps=0,frames=[[0,...p]],velocityFrames=[v.slice()],end=null,e0=energy(p,v),err=0,min=Infinity;let duration=options.duration||20,dt=options.dt||.002,sampleGap=Math.min(duration/600,.001),next=sampleGap;
function advance(budget=1200){for(let z=0;z<budget&&!end;z++){
let a=acc(p);if(!a){end='Close encounter';break;}let d=Infinity;for(let i=0;i<3;i++)for(let j=i+1;j<3;j++)d=Math.min(d,Math.hypot(p[2*i]-p[2*j],p[2*i+1]-p[2*j+1]));min=Math.min(min,d);
let h=Math.min(dt,.002*Math.sqrt(d*d*d/MU),duration-t);if(h<1e-10||steps>2000000){end='Unresolved';break;}
for(let i=0;i<6;i++){v[i]+=a[i]*h/2;p[i]+=v[i]*h;}let b=acc(p);t+=h;steps++;if(!b){end='Close encounter';break;}for(let i=0;i<6;i++)v[i]+=b[i]*h/2;
if(p.some(x=>!Number.isFinite(x))||v.some(x=>!Number.isFinite(x))){end='Numerical error';break;}
let drift=Math.abs(energy(p,v)-e0)/Math.max(Math.abs(e0),MU);err=Math.max(err,drift);
if(p.some(x=>Math.abs(x)>LIMIT)){end='Escaped';break;}
if(err>.01){end='Numerical error';break;}
if(t>=next){frames.push([t,...p]);velocityFrames.push(v.slice());next+=sampleGap;if(frames.length>=1200){frames=frames.filter((_,i)=>i%2===0);velocityFrames=velocityFrames.filter((_,i)=>i%2===0);sampleGap*=2;next=t+sampleGap;}}if(t>=duration-1e-10)end='Bounded';
}if(end&&frames[frames.length-1][0]!==t){frames.push([t,...p]);velocityFrames.push(v.slice());}return !!end;}
return {advance,get result(){return {engineVersion:2,initial:structuredClone(initial),frames,velocityFrames,outcome:end,time:t,energyError:err,minSeparation:min,steps,options:{duration,dt,mu:MU,boundary:LIMIT,close:CLOSE},finalVelocity:v.slice()};}};}
const api={MU,LIMIT,CLOSE,acc,energy,preset,grid,rng,randomState,create};if(typeof module!=='undefined')module.exports=api;else root.Physics=api;
})(typeof window!=='undefined'?window:globalThis);
