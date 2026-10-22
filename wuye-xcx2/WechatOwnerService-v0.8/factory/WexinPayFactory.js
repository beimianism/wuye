/* 微信内公众号 H5 的 JSAPI 支付调起。支付签名由服务端生成。 */
import {getHeaders} from '../api/java110Request.js';
import url from '../constant/url.js';

class WexinPayFactory {
	wexinPay(data, successCallBack, failureCallBack) {
		if (!data || !data.orderId || !data.appId || !data.sign) {
			uni.showToast({ icon: 'none', title: '支付参数不完整' });
			return;
		}
		const invokePay = () => {
			window.WeixinJSBridge.invoke('getBrandWCPayRequest', {
				appId: data.appId,
				timeStamp: data.timeStamp,
				nonceStr: data.nonceStr,
				package: data.package,
				signType: data.signType,
				paySign: data.sign
			}, result => {
				if (result.err_msg === 'get_brand_wcpay_request:ok') {
					this.confirmPayment(data.orderId, successCallBack);
					return;
				}
				if (failureCallBack) {
					failureCallBack(result);
				}
				uni.showToast({
					icon: 'none',
					title: result.err_msg === 'get_brand_wcpay_request:cancel' ? '已取消支付' : '支付失败'
				});
			});
		};

		if (window.WeixinJSBridge) {
			invokePay();
			return;
		}
		document.addEventListener('WeixinJSBridgeReady', invokePay, { once: true });
	}

	confirmPayment(orderId, successCallBack, remaining = 8) {
		uni.request({
			url: url.paymentStatus + '?orderId=' + encodeURIComponent(orderId),
			header: Object.assign({}, getHeaders(), { 'X-Requested-With': 'XMLHttpRequest' }),
			method: 'GET',
			success: response => {
				if (response.statusCode === 200 && response.data && response.data.status === 'PAID') {
					successCallBack(response.data);
					return;
				}
				if (response.statusCode === 401 || response.statusCode === 403) {
					uni.showToast({ icon: 'none', title: '登录已失效，请重新进入公众号页面' });
					return;
				}
				this.waitForConfirmation(orderId, successCallBack, remaining);
			},
			fail: () => this.waitForConfirmation(orderId, successCallBack, remaining)
		});
	}

	waitForConfirmation(orderId, successCallBack, remaining) {
		if (remaining <= 1) {
			uni.showToast({ icon: 'none', title: '支付结果确认中，请稍后查看缴费记录', duration: 3000 });
			return;
		}
		setTimeout(() => this.confirmPayment(orderId, successCallBack, remaining - 1), 1500);
	}
}

module.exports = new WexinPayFactory();
