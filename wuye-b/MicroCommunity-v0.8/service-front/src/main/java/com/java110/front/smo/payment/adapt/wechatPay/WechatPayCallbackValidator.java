package com.java110.front.smo.payment.adapt.wechatPay;

import com.alibaba.fastjson.JSONObject;
import com.java110.core.factory.WechatFactory;
import com.java110.dto.smallWeChat.SmallWeChatDto;
import com.java110.utils.cache.CommonCache;
import com.java110.utils.util.PayUtil;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Map;
import java.util.SortedMap;
import java.util.TreeMap;

/** APIv2 支付通知的公共校验。attach 由下单时生成，并由微信原样返回。 */
public final class WechatPayCallbackValidator {

    private static final String ORDER_KEY = "WECHAT_PAY_ORDER_";

    private WechatPayCallbackValidator() {
    }

    public static String createAttach(String appId, String totalFee) {
        String attach = WechatFactory.getWId(appId) + "|" + totalFee;
        if (attach.length() > 127) {
            throw new IllegalArgumentException("支付附加数据超过微信接口长度限制");
        }
        return attach;
    }

    public static String getAppId(Map<String, Object> notification) {
        String[] parts = getAttachParts(notification);
        return WechatFactory.getAppId(parts[0]);
    }

    public static void recordOrder(String orderNo, SmallWeChatDto merchant, String openId, String totalFee,
                                   String tradeType) {
        JSONObject order = new JSONObject();
        order.put("orderNo", orderNo);
        order.put("appId", merchant.getAppId());
        order.put("mchId", merchant.getMchId());
        order.put("openId", openId);
        order.put("totalFee", totalFee);
        order.put("tradeType", tradeType);
        String key = ORDER_KEY + orderNo;
        String existing = CommonCache.getValue(key);
        if (existing != null) {
            JSONObject saved = JSONObject.parseObject(existing);
            for (String field : new String[]{"orderNo", "appId", "mchId", "openId", "totalFee", "tradeType"}) {
                if (!String.valueOf(saved.get(field)).equals(String.valueOf(order.get(field)))) {
                    throw new IllegalStateException("同一商户订单号对应的支付参数不一致");
                }
            }
            return;
        }
        CommonCache.setValue(key, order.toJSONString());
    }

    /** 付款入口完成统一下单后绑定登录用户，供 H5 查单鉴权。 */
    public static void bindOwner(String orderNo, String userId) {
        String key = ORDER_KEY + orderNo;
        String value = CommonCache.getValue(key);
        if (value == null || userId == null || userId.isEmpty()) {
            throw new IllegalStateException("支付订单或登录用户不存在");
        }
        JSONObject order = JSONObject.parseObject(value);
        if (order.getString("userId") != null && !userId.equals(order.getString("userId"))) {
            throw new IllegalStateException("支付订单所属用户不一致");
        }
        order.put("userId", userId);
        CommonCache.setValue(key, order.toJSONString());
    }

    public static boolean belongsTo(String orderNo, String userId) {
        String value = CommonCache.getValue(ORDER_KEY + orderNo);
        return value != null && userId != null
                && userId.equals(JSONObject.parseObject(value).getString("userId"));
    }

    public static void verify(Map<String, Object> notification, SmallWeChatDto merchant) {
        if (merchant == null || merchant.getPayPassword() == null) {
            throw new IllegalArgumentException("未找到支付商户配置");
        }

        SortedMap<String, String> signedFields = new TreeMap<>();
        for (Map.Entry<String, Object> field : notification.entrySet()) {
            if (field.getValue() != null) {
                signedFields.put(field.getKey(), field.getValue().toString());
            }
        }
        String expectedSign = PayUtil.createSign(signedFields, merchant.getPayPassword());
        if (!MessageDigest.isEqual(expectedSign.getBytes(StandardCharsets.US_ASCII),
                String.valueOf(notification.get("sign")).getBytes(StandardCharsets.US_ASCII))) {
            throw new IllegalArgumentException("微信支付通知验签失败");
        }

        if (!"SUCCESS".equals(notification.get("return_code"))
                || !"SUCCESS".equals(notification.get("result_code"))) {
            throw new IllegalArgumentException("微信支付通知交易状态或类型不符");
        }

        String orderNo = String.valueOf(notification.get("out_trade_no"));
        String localOrder = CommonCache.getValue(ORDER_KEY + orderNo);
        if (localOrder == null || "null".equals(orderNo)) {
            throw new IllegalArgumentException("未找到本地支付订单");
        }
        JSONObject order = JSONObject.parseObject(localOrder);

        String[] parts = getAttachParts(notification);
        if (!merchant.getAppId().equals(getAppId(notification))
                || !merchant.getAppId().equals(notification.get("appid"))
                || !merchant.getMchId().equals(notification.get("mch_id"))) {
            throw new IllegalArgumentException("微信支付通知商户信息不匹配");
        }
        if (!parts[1].equals(notification.get("total_fee"))) {
            throw new IllegalArgumentException("微信支付通知金额与下单金额不一致");
        }
        if (!orderNo.equals(order.getString("orderNo"))
                || !merchant.getAppId().equals(order.getString("appId"))
                || !merchant.getMchId().equals(order.getString("mchId"))
                || (order.getString("openId") != null && !order.getString("openId").isEmpty()
                    && !order.getString("openId").equals(notification.get("openid")))
                || !order.getString("totalFee").equals(notification.get("total_fee"))
                || !order.getString("tradeType").equals(notification.get("trade_type"))
                || notification.get("transaction_id") == null) {
            throw new IllegalArgumentException("微信支付通知与本地订单不一致");
        }
    }

    private static String[] getAttachParts(Map<String, Object> notification) {
        Object attach = notification.get("attach");
        if (attach == null) {
            throw new IllegalArgumentException("微信支付通知缺少附加数据");
        }
        String[] parts = attach.toString().split("\\|", -1);
        if (parts.length != 2 || parts[0].isEmpty() || !parts[1].matches("[1-9][0-9]*")) {
            throw new IllegalArgumentException("微信支付通知附加数据无效");
        }
        return parts;
    }
}
