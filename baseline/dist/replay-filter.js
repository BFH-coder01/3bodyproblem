(function(root){
const minimumSeconds=5;
function qualifies(record){return Number.isFinite(record?.time)&&record.time>=0&&(record.outcome==='Escaped'||record.time>minimumSeconds);}
const api={minimumSeconds,qualifies};if(typeof module!=='undefined')module.exports=api;else root.ReplayFilter=api;
})(typeof window!=='undefined'?window:globalThis);
