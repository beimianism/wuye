'use strict';
function publicConfig() {
  return typeof window !== 'undefined' && window.__WUYE_WECHAT_TEST__ || {};
}
function install(runtime, config = publicConfig()) {
  if (!runtime || !runtime.addInterceptor || runtime.__ownerH5Installed) return;
  runtime.__ownerH5Installed = true;
  const deny = options => {
    if (config.paymentEnabled === true) return;
    const error = {code:'PAYMENT_NOT_CONFIGURED',errMsg:'微信支付未开通，当前仅支持账单查询'};
    runtime.hideLoading();
    runtime.showToast({icon:'none',title:error.errMsg});
    if (options.fail) options.fail(error);
    if (options.complete) options.complete(error);
    return false;
  };
  runtime.addInterceptor('request', {invoke(options) {
    // Browsers reject manually supplied Cookie headers. The local gateway maps
    // this header to the backend's existing cookie after its access check.
    if (/^\/?(?:app|callComponent)\//.test(options.url || '')) {
      const header = options.header || (options.header = {});
      Object.keys(header).forEach(key=>{if (key.toLowerCase() === 'cookie') delete header[key];});
      const token = runtime.getStorageSync && runtime.getStorageSync('token');
      if (token) header.token = token;
    }
    if (/\/app\/payment\//i.test(options.url || '')) return deny(options);
  }});
  runtime.addInterceptor('requestPayment', {invoke:deny});
}
module.exports = {publicConfig,install};
