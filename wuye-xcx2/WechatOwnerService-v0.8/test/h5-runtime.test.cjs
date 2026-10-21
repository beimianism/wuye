const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
function load(file, names, dependencies) {
  let source = fs.readFileSync(path.join(__dirname, '..', file), 'utf8');
  const active = [true];
  source = source.split('\n').filter(line => {
    const directive = line.match(/\/\/\s*#(ifdef|ifndef|endif)\s*(\S*)/);
    if (directive) {
      if (directive[1] === 'endif') active.pop();
      else active.push(active[active.length - 1] && (directive[1] === 'ifdef' ? directive[2] === 'H5' : directive[2] !== 'H5'));
      return false;
    }
    return active[active.length - 1];
  }).join('\n').replace(/import\s[\s\S]*?from\s*['"][^'"]+['"];?/g, '').replace(/export function/g, 'function');
  const context = {module:{exports:{}}, console, ...dependencies};
  vm.runInNewContext(source + '\nmodule.exports={' + names.join(',') + '}', context);
  return context.module.exports;
}
test('H5 resolves configured appId before pages exist and consumes one-use OAuth tickets', () => {
  const stored = new Map();
  const calls = [];
  const api = load('api/init/initApi.js', ['getWAppId','onLoad'], {
    getCurrentPages:()=>[], mapping:{W_APP_ID:'wAppId'}, conf:{wAppId:'configured-app'},
    isNull:value=>value == null || value === '', isNotNull:value=>value != null && value !== '',
    uni:{getStorageSync:key=>stored.get(key),setStorageSync:(key,value)=>stored.set(key,value),showToast:()=>{}},
    doLoginOwnerByKey:(ticket,callback)=>{calls.push(ticket);callback();}
  });
  assert.equal(api.getWAppId(), 'configured-app');
  let completed = false;
  api.onLoad({authTicket:'one-use-ticket'}, ()=>{completed=true;});
  assert.equal(calls[0].authTicket,'one-use-ticket');
  assert.equal(completed,true);
});
test('payment is unavailable without explicit configuration; fee queries still execute', () => {
  const runtimeConfig = require('../config/h5-runtime.js');
  const interceptors = {};
  const messages = [];
  runtimeConfig.install({addInterceptor:(name,handler)=>interceptors[name]=handler,hideLoading:()=>{},showToast:options=>messages.push(options.title)},{});
  let failure;
  assert.equal(interceptors.request.invoke({url:'/app/payment/toPay',fail:error=>failure=error}),false);
  assert.equal(failure.code,'PAYMENT_NOT_CONFIGURED');
  assert.equal(interceptors.requestPayment.invoke({}),false);
  assert.notEqual(interceptors.request.invoke({url:'/app/fee.listFee'}),false);
  assert.ok(messages.every(message=>message.includes('未开通')));
});
test('H5 auth uses a browser-safe token header and removes the forbidden Cookie header', () => {
  const config = require('../config/h5-runtime.js');
  const interceptors = {};
  config.install({addInterceptor:(name,handler)=>interceptors[name]=handler,getStorageSync:()=> 'session-token'},{});
  const request = {url:'/app/room.queryRoomsByOwner',header:{cookie:'_java110_token_=session-token','app-id':'owner-client'}};
  interceptors.request.invoke(request);
  assert.equal(request.header.token,'session-token');
  assert.equal(request.header.cookie,undefined);
  assert.equal(request.header['app-id'],'owner-client');
});
