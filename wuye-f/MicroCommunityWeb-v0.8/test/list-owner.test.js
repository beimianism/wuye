'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function ownerScreen(response, attrSpecs) {
  const requests = [];
  const events = [];
  const vc = {
    extends(definition) {
      this.component = Object.assign({}, definition.data, definition.methods);
    },
    getCurrentCommunity: () => ({communityId:'local-community'}),
    getAttrSpec: (name, callback) => callback(attrSpecs),
    emit: (...args) => events.push(args),
    http: {get(component, method, params, success) {
      requests.push({component,method,params});
      success(JSON.stringify(response));
    }}
  };
  const context = {window:{vc},console:{log() {}}};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(require.resolve('../public/pages/property/listOwner/listOwner.js'), 'utf8'), context);
  context.$that = vc.component;
  return {screen:vc.component, requests, events};
}

test('empty owner list responses clear previous rows and still update pagination', () => {
  for (const response of [
    {page:0,records:0,rows:0,total:0},
    {records:0,total:0,owners:null},
    {records:0,total:0,owners:[]}
  ]) {
    const {screen,requests,events} = ownerScreen(response);
    screen.listOwnerInfo.owners = [{ownerId:'previous-search'}];
    assert.doesNotThrow(() => screen._listOwnerData(1,10));
    assert.equal(screen.listOwnerInfo.owners.length,0);
    assert.equal(screen.listOwnerInfo.total,0);
    assert.equal(screen.listOwnerInfo.records,0);
    assert.equal(requests[0].component,'listOwner');
    assert.equal(requests[0].method,'list');
    assert.equal(requests[0].params.params.communityId,'local-community');
    assert.equal(events.length,1);
    assert.equal(events[0][0],'pagination');
    assert.equal(events[0][2].dataCount,0);
    assert.equal(events[0][2].total,0);
  }
});

test('owners without optional attributes render blank columns and retain supplied attribute values', () => {
  const {screen} = ownerScreen({total:4,records:1,owners:[
    {ownerId:'missing'},
    {ownerId:'null',ownerAttrDtos:null},
    {ownerId:'empty',ownerAttrDtos:[]},
    {ownerId:'with-attributes',ownerAttrDtos:[{specName:'source',valueName:'verified'}]}
  ]});
  screen.listOwnerInfo.listColumns = ['source','other'];
  assert.doesNotThrow(() => screen._listOwnerData(1,10));
  assert.deepEqual(JSON.parse(JSON.stringify(screen.listOwnerInfo.owners.map(owner=>owner.listValues))),
    [['',''],['',''],['',''],['verified','']]);
  assert.equal(screen.listOwnerInfo.total,4);
  assert.doesNotThrow(() => screen.dealOwnerAttr(undefined));
});

test('absent optional attribute specifications do not prevent owner list loading', () => {
  for (const specs of [undefined,null,[]]) {
    const {screen,requests} = ownerScreen({page:0,records:0,rows:0,total:0},specs);
    assert.doesNotThrow(() => screen._getColumns(() => screen._listOwnerData(1,10)));
    assert.equal(screen.listOwnerInfo.listColumns.length,0);
    assert.equal(requests.length,1);
  }
});
