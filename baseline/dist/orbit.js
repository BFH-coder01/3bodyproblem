(function(root){
/* A finite recurrence screen, not a proof of Lyapunov/Floquet stability.
   Compare centre-of-mass-relative positions AND velocities over 3 cycles. */
function analyze(r){let none={detected:false,reason:'No repeating orbit detected',cycles:0,tolerance:.02};if(r.outcome!=='Bounded'||r.energyError>.001||!r.velocityFrames||r.frames.length<100)return none;
const F=r.frames,V=r.velocityFrames,N=F.length;function centered(p){let a=p.slice();for(let q=0;q<2;q++){let mean=(a[q]+a[q+2]+a[q+4])/3;for(let i=q;i<6;i+=2)a[i]-=mean;}return a;}
let p0=centered(F[0].slice(1)),v0=centered(V[0]),R=Math.max(.01,Math.sqrt(p0.reduce((s,x)=>s+x*x,0)/3)),S=Math.max(Math.sqrt(r.options.mu/R),Math.sqrt(v0.reduce((s,x)=>s+x*x,0)/3)),states=F.map((f,i)=>[...centered(f.slice(1)).map(x=>x/R),...centered(V[i]).map(x=>x/S)]);
function at(t){let lo=0,hi=N-1;while(lo+1<hi){let m=(lo+hi)>>1;if(F[m][0]<=t)lo=m;else hi=m;}let f=Math.max(0,Math.min(1,(t-F[lo][0])/(F[hi][0]-F[lo][0]||1)));return states[lo].map((x,i)=>x+(states[hi][i]-x)*f);}
function error(a,b){return Math.max(...a.map((x,i)=>Math.abs(x-b[i])));}
let excursion=0;for(let s of states)excursion=Math.max(excursion,error(s.slice(0,6),states[0].slice(0,6)));if(excursion<.1)return {...none,reason:'Insufficient motion to identify an orbit'};
for(let k=20;k<N/3;k++){let e=error(states[k],states[0]);if(e>.12||e>error(states[k-1],states[0])||e>error(states[k+1],states[0]))continue;let lo=F[k-1][0],hi=F[k+1][0];for(let j=0;j<24;j++){let a=lo+(hi-lo)/3,b=hi-(hi-lo)/3;if(error(at(a),states[0])<error(at(b),states[0]))hi=b;else lo=a;}let T=(lo+hi)/2;if(T<.1||3*T>r.time)continue;let worst=0;for(let cycle=1;cycle<=3;cycle++)worst=Math.max(worst,error(at(cycle*T),states[0]));for(let phase=0;phase<=24&&worst<=.02;phase++){let ref=at(T*phase/24);for(let cycle=1;cycle<=2;cycle++)worst=Math.max(worst,error(at(T*(cycle+phase/24)),ref));}if(worst<=.02)return {detected:true,reason:'Full relative state repeats across 3 observed cycles',period:T,cycles:3,maxNormalizedError:worst,tolerance:.02};}
return none;}
const api={analyze};if(typeof module!=='undefined')module.exports=api;else root.Orbit=api;
})(typeof window!=='undefined'?window:globalThis);
