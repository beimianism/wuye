'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('local navigation loads user information without subscribing to browser notice messages', () => {
  const sockets = [];
  const requests = [];
  function WebSocket(url) { sockets.push(url); }
  function Vue(options) {
    Object.assign(this,options.data,options.methods);
    options.mounted.call(this);
  }
  const vc = {
    getData: () => ({userId:'local-user',logo:'local'}),
    getCurrentCommunity: () => ({communityId:'local-community'}),
    getCommunitys: () => [],
    http: {get(component,method) {requests.push(component + '/' + method);}}
  };
  vm.runInNewContext(fs.readFileSync(require.resolve('../public/components/frame/nav/nav.js'), 'utf8'), {
    window:{vc,localFeatures:require('../public/js/local-features'),WebSocket,location:{protocol:'http:',host:'127.0.0.1:3000'}},
    Vue,WebSocket,console
  });
  assert.deepEqual(requests,['nav/getUserInfo']);
  assert.deepEqual(sockets,[]);
});
