// Retained page lifecycle hooks can query rooms while an OAuth ticket is exchanged.
let pending = Promise.resolve();
function begin() {
  let complete;
  pending = new Promise(resolve => {complete = resolve;});
  return complete;
}
module.exports = {begin,ready:()=>pending};
