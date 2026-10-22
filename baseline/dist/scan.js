(function(root){
function choose2(n){return n*(n-1)/2;}function choose3(n){return n*(n-1)*(n-2)/6;}
function spec(radius){if(!Number.isFinite(radius)||radius<.1||radius>2)throw Error('Radius must be between 0.1 and 2 metres.');let n=Math.floor((12-2*radius)/radius+1e-8)+1,N=n*n;return {radius,n,N,total:choose3(N)};}
function tripleAt(N,rank){if(!Number.isSafeInteger(rank)||rank<0||rank>=choose3(N))throw Error('Scan index out of range.');let lo=0,hi=N-3;while(lo<hi){let m=Math.ceil((lo+hi)/2);if(choose3(N)-choose3(N-m)<=rank)lo=m;else hi=m-1;}let a=lo;rank-=choose3(N)-choose3(N-a);lo=a+1;hi=N-2;while(lo<hi){let m=Math.ceil((lo+hi)/2);if(choose2(N-a-1)-choose2(N-m)<=rank)lo=m;else hi=m-1;}let b=lo;rank-=choose2(N-a-1)-choose2(N-b);return [a,b,b+1+rank];}
function initial(radius,ordinal){let s=spec(radius),triple=tripleAt(s.N,ordinal),p=[];for(let i of triple)p.push(-6+radius+(i%s.n)*radius,6-radius-Math.floor(i/s.n)*radius);return {p,v:Array(6).fill(0),name:'Radius scan · all at rest',scan:{ordinal,triple,...s}};}
const api={spec,tripleAt,initial,choose3};if(typeof module!=='undefined')module.exports=api;else root.Scan=api;
})(typeof window!=='undefined'?window:globalThis);
