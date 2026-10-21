const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function component(kind, type, payment = {}) {
    const field = `${kind}SmallWeChatInfo`;
    const vc = {
        component: {},
        propTypes: { string: 'string' },
        extends(definition) { this.component = { ...definition.data, ...definition.methods }; },
        validate: {
            errInfo: '',
            validate(data, rules) {
                for (const [key, checks] of Object.entries(rules)) {
                    const value = data[field][key.split('.')[1]];
                    for (const rule of checks) {
                        if (rule.limit === 'required' && !String(value || '').trim()) return false;
                        if (rule.limit === 'maxin' && value && value.length > +rule.param.split(',')[1]) return false;
                    }
                }
                return true;
            }
        }
    };
    const source = path.join(__dirname, `../public/components/property/${kind}SmallWeChat/${kind}SmallWeChat.js`);
    vm.runInNewContext(fs.readFileSync(source, 'utf8'), { window: { vc } });
    Object.assign(vc.component[field], { name: 'Test', appId: 'wx-test', appSecret: 'secret',
        weChatId: 'id', objType: '1000', weChatType: type }, payment);
    return vc.component[`${kind}SmallWeChatValidate`]();
}
for (const kind of ['add', 'edit']) {
    test(`${kind} public account accepts absent payment pair`, () => assert.equal(component(kind, '1100'), true));
    test(`${kind} accepts numeric account type from management event`, () => assert.equal(component(kind, 1100), true));
    test(`${kind} rejects partial payment pair`, () => {
        assert.equal(component(kind, '1100', { payPassword: 'key' }), false);
        assert.equal(component(kind, '1100', { mchId: 'merchant' }), false);
    });
    test(`${kind} mini program still requires payment`, () => {
        assert.equal(component(kind, '1000'), false);
        assert.equal(component(kind, '1000', { payPassword: 'key', mchId: 'merchant' }), true);
    });
}
