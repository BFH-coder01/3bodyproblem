const assert=require('node:assert/strict'),P=require('../dist/physics.js'),S=require('../dist/scan.js'),O=require('../dist/orbit.js');
for(let N=3;N<30;N++){let rank=0;for(let a=0;a<N-2;a++)for(let b=a+1;b<N-1;b++)for(let c=b+1;c<N;c++)assert.deepEqual(S.tripleAt(N,rank++),[a,b,c]);assert.equal(rank,S.choose3(N));}
let spec=S.spec(.25);assert.equal(spec.total,1794096784);assert.deepEqual(S.initial(.25,0).p,[-5.75,5.75,-5.5,5.75,-5.25,5.75]);assert.deepEqual(S.initial(.25,1).scan.triple,[0,1,3]);assert.deepEqual(S.initial(.25,spec.N-2).scan.triple,[0,2,3]);assert.deepEqual(S.tripleAt(spec.N,spec.total-1),[spec.N-3,spec.N-2,spec.N-1]);assert(S.initial(.25,25).v.every(v=>v===0));
function run(initial,duration=30){let sim=P.create(initial,{duration,dt:.001});while(!sim.advance(20000)){}let r=sim.result;assert.equal(r.frames.length,r.velocityFrames.length);assert(r.frames.length<=1201);return r;}
let collapse=run(S.initial(.25,0));assert.equal(collapse.outcome,'Close encounter');assert(!O.analyze(collapse).detected);assert(collapse.frames.length>5);
let eight=run(P.preset('eight'));let orbit=O.analyze(eight);console.log({eightOutcome:eight.outcome,eightFrames:eight.frames.length,orbit});assert.equal(eight.outcome,'Bounded');assert(orbit.detected);assert(Math.abs(orbit.period-5.713)<.03);
let short=run(P.preset('eight'),1);assert(!O.analyze(short).detected);
let escape=run({p:[-2,0,0,0,2,0],v:[-20,0,0,0,20,0]},1);assert.equal(escape.outcome,'Escaped');assert(!O.analyze(escape).detected);
let rest=run({p:[-3,-2,1,-1,2,3],v:[0,0,0,0,0,0]},.1);for(let b=0;b<3;b++)assert(Math.hypot(rest.frames.at(-1)[2*b+1]-rest.initial.p[2*b],rest.frames.at(-1)[2*b+2]-rest.initial.p[2*b+1])>0);
console.log('PASS: exhaustive enumeration order and direct resume, 1.794 billion count, radius spacing, all-rest physics, collapse/escape rejection, periodic reference detection and insufficient-cycle rejection.');
const ReplayFilter=require('../dist/replay-filter.js');
for(let time of [0,1,4.999,5,NaN,Infinity,undefined])assert.equal(ReplayFilter.qualifies({time}),false);
for(let time of [5.000001,6,30])assert.equal(ReplayFilter.qualifies({time}),true);
let qualifying=[];for(let i=0;i<29;i++){let r=run(S.initial(2,i),6);if(ReplayFilter.qualifies(r))qualifying.push(i);}
assert.deepEqual(qualifying,[28]);console.log('PASS: first 28 short rest-start trials excluded; trial 29 qualifies; exact five-second boundary excluded.');
for(let time of [0,.2,4.999,5,6])assert.equal(ReplayFilter.qualifies({time,outcome:'Escaped'}),true);
for(let time of [-1,NaN,Infinity,undefined])assert.equal(ReplayFilter.qualifies({time,outcome:'Escaped'}),false);
for(let outcome of ['Bounded','Close encounter','Numerical error','Unresolved','Orbit candidate'])assert.equal(ReplayFilter.qualifies({time:5,outcome}),false);
let shortEscape=run(S.initial(2,57),6);assert.equal(shortEscape.outcome,'Escaped');assert(shortEscape.time<5);assert(ReplayFilter.qualifies(shortEscape));console.log('PASS: all escapes qualify, including a real all-rest scan escape at '+shortEscape.time.toFixed(3)+' seconds; other short outcomes remain excluded.');
