package com.java110.api.bmo.smallWeChat;

import com.alibaba.fastjson.JSONObject;
import com.java110.dto.smallWeChat.SmallWeChatDto;

/** Validation shared by create and the merged, persisted update configuration. */
public final class SmallWeChatConfiguration {
    private SmallWeChatConfiguration() { }

    public static void validate(JSONObject configuration) {
        required(configuration, "name", 100);
        required(configuration, "appId", 100);
        required(configuration, "appSecret", 200);
        String type = configuration.getString("weChatType");
        if (!SmallWeChatDto.WECHAT_TYPE_PUBLIC.equals(type) && !"1000".equals(type)) {
            throw new IllegalArgumentException("请选择有效的微信配置类型");
        }
        String merchant = clean(configuration.getString("mchId"));
        String password = clean(configuration.getString("payPassword"));
        if (merchant.isEmpty() != password.isEmpty()) {
            throw new IllegalArgumentException("商户ID与支付密码必须同时填写或同时留空");
        }
        if (!SmallWeChatDto.WECHAT_TYPE_PUBLIC.equals(type) && merchant.isEmpty()) {
            throw new IllegalArgumentException("小程序必须配置商户ID与支付密码");
        }
        if (merchant.length() > 200 || password.length() > 200) {
            throw new IllegalArgumentException("商户ID与支付密码不能超过200个字符");
        }
        // Both historical tables require NOT NULL; an empty pair means payment is unavailable.
        configuration.put("mchId", merchant);
        configuration.put("payPassword", password);
    }

    private static void required(JSONObject configuration, String field, int max) {
        String value = clean(configuration.getString(field));
        if (value.isEmpty() || value.length() > max) {
            throw new IllegalArgumentException(field + "不能为空且不能超过" + max + "个字符");
        }
        configuration.put(field, value);
    }

    private static String clean(String value) { return value == null ? "" : value.trim(); }
}
