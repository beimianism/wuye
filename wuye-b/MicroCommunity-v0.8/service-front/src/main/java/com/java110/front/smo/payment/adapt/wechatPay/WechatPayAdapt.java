/*
 * Copyright 2017-2020 吴学文 and java110 team.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.java110.front.smo.payment.adapt.wechatPay;

import com.java110.dto.smallWeChat.SmallWeChatDto;
import com.java110.front.properties.WechatAuthProperties;
import com.java110.front.smo.payment.adapt.IPayAdapt;
import com.java110.utils.cache.MappingCache;
import com.java110.utils.constant.WechatConstant;
import com.java110.utils.util.PayUtil;
import com.java110.utils.util.StringUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.util.Map;
import java.util.SortedMap;
import java.util.TreeMap;

/**
 * 微信通用 支付
 * 此实现方式为 直接调用微信下单方式，不经过 第三方支付平台
 *
 * @desc add by 吴学文 15:33
 */

@Component(value = "wechatPayAdapt")
public class WechatPayAdapt implements IPayAdapt {
    private static final Logger logger = LoggerFactory.getLogger(WechatPayAdapt.class);

    //微信支付
    public static final String DOMAIN_WECHAT_PAY = "WECHAT_PAY";
    // 微信服务商支付开关
    public static final String WECHAT_SERVICE_PAY_SWITCH = "WECHAT_SERVICE_PAY_SWITCH";

    //开关ON打开
    public static final String WECHAT_SERVICE_PAY_SWITCH_ON = "ON";


    @Autowired
    private WechatAuthProperties wechatAuthProperties;

    /**
     * 预下单
     *
     * @param orderNum
     * @param money
     * @param openId
     * @return
     * @throws Exception
     */
    public Map<String, String> java110Payment(RestTemplate outRestTemplate,
                                              String feeName, String tradeType,
                                              String orderNum, double money,
                                              String openId, SmallWeChatDto smallWeChatDto) throws Exception {
        return java110Payment(outRestTemplate, feeName, tradeType, orderNum, money, openId, smallWeChatDto, "");
    }

    /**
     * 预下单
     *
     * @param orderNum
     * @param money
     * @param openId
     * @return
     * @throws Exception
     */
    public Map<String, String> java110Payment(RestTemplate outRestTemplate,
                                              String feeName, String tradeType,
                                              String orderNum, double money,
                                              String openId, SmallWeChatDto smallWeChatDto, String notifyUrl) throws Exception {
        logger.info("【微信支付】 统一下单开始, 订单编号=" + orderNum);
        if (WECHAT_SERVICE_PAY_SWITCH_ON.equals(MappingCache.getValue(DOMAIN_WECHAT_PAY, WECHAT_SERVICE_PAY_SWITCH))) {
            throw new IllegalStateException("当前微信支付模块只支持普通商户模式，服务商模式尚未接入");
        }
        SortedMap<String, String> resultMap = new TreeMap<String, String>();
        // 实付金额必须与服务端生成的业务订单一致，不能按运行环境改写。
        double payAmount = money;
        //添加或更新支付记录(参数跟进自己业务需求添加)

        Map<String, String> resMap = null;

        if (StringUtil.isEmpty(notifyUrl)) {
            resMap = this.java110UnifieldOrder(outRestTemplate, feeName, orderNum, tradeType, payAmount, openId, smallWeChatDto);
        } else {
            resMap = this.java110UnifieldOrder(outRestTemplate, feeName, orderNum, tradeType, payAmount, openId, smallWeChatDto, notifyUrl);
        }

        if ("SUCCESS".equals(resMap.get("return_code"))) {
            String responseSign = PayUtil.createSign(new TreeMap<>(resMap), smallWeChatDto.getPayPassword());
            if (!responseSign.equals(resMap.get("sign"))
                    || !smallWeChatDto.getAppId().equals(resMap.get("appid"))
                    || !smallWeChatDto.getMchId().equals(resMap.get("mch_id"))) {
                throw new IllegalArgumentException("微信统一下单应答验签或商户信息校验失败");
            }
        }
        if ("SUCCESS".equals(resMap.get("return_code")) && "SUCCESS".equals(resMap.get("result_code"))) {
            if (StringUtil.isEmpty(resMap.get("prepay_id"))) {
                throw new IllegalArgumentException("微信统一下单未返回预支付标识");
            }
            if (WechatAuthProperties.TRADE_TYPE_JSAPI.equals(tradeType)) {

                resultMap.put("appId", smallWeChatDto.getAppId());
                resultMap.put("timeStamp", PayUtil.getCurrentTimeStamp());
                resultMap.put("nonceStr", PayUtil.makeUUID(32));
                resultMap.put("package", "prepay_id=" + resMap.get("prepay_id"));
                resultMap.put("signType", "MD5");
                resultMap.put("sign", PayUtil.createSign(resultMap, smallWeChatDto.getPayPassword()));
            } else if (WechatAuthProperties.TRADE_TYPE_APP.equals(tradeType)) {
                resultMap.put("appId", smallWeChatDto.getAppId());
                resultMap.put("timeStamp", PayUtil.getCurrentTimeStamp());
                resultMap.put("nonceStr", PayUtil.makeUUID(32));
                resultMap.put("partnerid", smallWeChatDto.getMchId());
                resultMap.put("prepayid", resMap.get("prepay_id"));
                //resultMap.put("signType", "MD5");
                resultMap.put("sign", PayUtil.createSign(resultMap, smallWeChatDto.getPayPassword()));
            } else if (WechatAuthProperties.TRADE_TYPE_NATIVE.equals(tradeType)) {
                resultMap.put("prepayId", resMap.get("prepay_id"));
                resultMap.put("codeUrl", resMap.get("code_url"));
            }
            resultMap.put("code", "0");
            resultMap.put("orderId", orderNum);
            resultMap.put("msg", "下单成功");
            logger.info("【微信支付】统一下单成功，订单编号={}", orderNum);
        } else {
            resultMap.put("code", resMap.get("return_code"));
            resultMap.put("msg", resMap.get("return_msg"));
            logger.info("【微信支付】统一下单失败，失败原因:" + resMap.get("return_msg"));
        }
        return resultMap;
    }

    /**
     * 小程序支付统一下单
     */
    private Map<String, String> java110UnifieldOrder(RestTemplate outRestTemplate, String feeName, String orderNum,
                                                     String tradeType, double payAmount, String openid,
                                                     SmallWeChatDto smallWeChatDto) throws Exception {
        return java110UnifieldOrder(outRestTemplate, feeName, orderNum, tradeType, payAmount, openid, smallWeChatDto, wechatAuthProperties.getWxNotifyUrl());
    }

    /**
     * 小程序支付统一下单
     */
    private Map<String, String> java110UnifieldOrder(RestTemplate outRestTemplate, String feeName, String orderNum,
                                                     String tradeType, double payAmount, String openid,
                                                     SmallWeChatDto smallWeChatDto, String notifyUrl) throws Exception {

        String systemName = MappingCache.getValue(WechatConstant.WECHAT_DOMAIN, WechatConstant.PAY_GOOD_NAME);

        SortedMap<String, String> paramMap = new TreeMap<String, String>();
        paramMap.put("appid", smallWeChatDto.getAppId());
        paramMap.put("mch_id", smallWeChatDto.getMchId());
        paramMap.put("nonce_str", PayUtil.makeUUID(32));
        paramMap.put("body", systemName + feeName);
        paramMap.put("out_trade_no", orderNum);
        String totalFee = PayUtil.moneyToIntegerStr(payAmount);
        paramMap.put("total_fee", totalFee);
        paramMap.put("spbill_create_ip", PayUtil.getLocalIp());
        if (notifyUrl == null || !notifyUrl.startsWith("https://") || notifyUrl.contains("?")) {
            throw new IllegalArgumentException("微信支付通知地址必须是无参数的公网 HTTPS 地址");
        }
        paramMap.put("notify_url", notifyUrl);
        paramMap.put("attach", WechatPayCallbackValidator.createAttach(smallWeChatDto.getAppId(), totalFee));
        paramMap.put("trade_type", tradeType);
        if (WechatAuthProperties.TRADE_TYPE_JSAPI.equals(tradeType)) {
            if (StringUtil.isEmpty(openid)) {
                throw new IllegalArgumentException("JSAPI 支付缺少用户 OpenID");
            }
            paramMap.put("openid", openid);
        }

        WechatPayCallbackValidator.recordOrder(orderNum, smallWeChatDto, openid, totalFee, tradeType);

        paramMap.put("sign", PayUtil.createSign(paramMap, smallWeChatDto.getPayPassword()));
//转换为xml
        String xmlData = PayUtil.mapToXml(paramMap);

        ResponseEntity<String> responseEntity = outRestTemplate.postForEntity(
                wechatAuthProperties.getWxPayUnifiedOrder(), xmlData, String.class);
//请求微信后台，获取预支付ID
        if (responseEntity.getStatusCode() != HttpStatus.OK) {
            throw new IllegalArgumentException("支付失败" + responseEntity.getBody());
        }
        return PayUtil.xmlStrToMap(responseEntity.getBody());
    }
}
