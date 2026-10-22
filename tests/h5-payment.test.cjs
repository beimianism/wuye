const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

function setup({bridge = true, notify = 'get_brand_wcpay_request:ok', statuses = ['PAID'], statusCode = 200} = {}) {
  let code = fs.readFileSync(path.join(__dirname, '../wuye-xcx2/WechatOwnerService-v0.8/factory/WexinPayFactory.js'), 'utf8');
  code = code.replace(/^import .*;\s*$/gm, '');
  const calls = {requests: [], toasts: [], listeners: [], successes: [], failures: []};
  const context = {
    module: {exports: {}},
    getHeaders: () => ({cookie: 'session'}),
    url: {paymentStatus: '/app/payment/status'},
    window: bridge ? {WeixinJSBridge: {invoke: (_name, args, callback) => {
      calls.bridgeArgs = args;
      callback({err_msg: notify});
    }}} : {},
    document: {addEventListener: (name, callback) => calls.listeners.push({name, callback})},
    uni: {
      request: req => {
        calls.requests.push(req);
        req.success({statusCode, data: {status: statuses.shift() || 'PENDING'}});
      },
      showToast: toast => calls.toasts.push(toast)
    },
    setTimeout: callback => callback(),
    encodeURIComponent
  };
  vm.runInNewContext(code, context);
  const payment = context.module.exports;
  const data = {appId: 'wx-account', timeStamp: '1', nonceStr: 'nonce', package: 'prepay_id=p', signType: 'MD5', sign: 'signature', orderId: '123'};
  payment.wexinPay(data, result => calls.successes.push(result), result => calls.failures.push(result));
  return calls;
}

test('JSAPI bridge success waits for server payment confirmation', () => {
  const calls = setup({statuses: ['PENDING', 'PAID']});
  assert.equal(calls.requests.length, 2);
  assert.equal(calls.requests[0].url, '/app/payment/status?orderId=123');
  assert.equal(calls.requests[0].header['X-Requested-With'], 'XMLHttpRequest');
  assert.equal(calls.successes.length, 1);
  assert.equal(calls.bridgeArgs.paySign, 'signature');
});

test('cancel does not confirm payment', () => {
  const calls = setup({notify: 'get_brand_wcpay_request:cancel'});
  assert.equal(calls.requests.length, 0);
  assert.equal(calls.failures.length, 1);
});

test('pending server status never reports success', () => {
  const calls = setup({statuses: Array(8).fill('PENDING')});
  assert.equal(calls.requests.length, 8);
  assert.equal(calls.successes.length, 0);
  assert.match(calls.toasts[0].title, /确认中/);
});

test('waits for WeixinJSBridgeReady in WeChat H5', () => {
  const calls = setup({bridge: false});
  assert.equal(calls.listeners[0].name, 'WeixinJSBridgeReady');
  assert.equal(calls.requests.length, 0);
});

test('unauthorized status stops polling and never reports success', () => {
  const calls = setup({statusCode: 403});
  assert.equal(calls.requests.length, 1);
  assert.equal(calls.successes.length, 0);
  assert.match(calls.toasts[0].title, /登录已失效/);
});
