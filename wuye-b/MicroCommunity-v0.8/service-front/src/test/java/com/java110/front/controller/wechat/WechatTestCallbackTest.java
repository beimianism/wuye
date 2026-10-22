package com.java110.front.controller.wechat;

import com.java110.core.context.IPageData;
import com.java110.core.factory.WechatFactory;
import com.java110.dto.app.AppDto;
import com.java110.front.properties.WechatAuthProperties;
import com.java110.front.smo.wechatGateway.IWechatGatewaySMO;
import org.junit.Before;
import org.junit.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import javax.servlet.http.HttpServletRequest;
import java.lang.reflect.Field;
import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;

public class WechatTestCallbackTest {
    private final WechatGatewayController controller = new WechatGatewayController();
    private final WechatAuthProperties properties = new WechatAuthProperties();
    private final AtomicReference<IPageData> message = new AtomicReference<>();
    private final AtomicReference<String> messageWId = new AtomicReference<>();

    @Before public void setup() throws Exception {
        properties.setWechatAppId("wx-test");
        properties.setCallbackToken("unit-test-token");
        field("wechatAuthProperties").set(controller, properties);
        IWechatGatewaySMO service = (IWechatGatewaySMO) Proxy.newProxyInstance(
                getClass().getClassLoader(), new Class[]{IWechatGatewaySMO.class}, (proxy, method, args) -> {
                    if ("gateway".equals(method.getName())) {
                        message.set((IPageData) args[0]);
                        messageWId.set((String) args[1]);
                        return ResponseEntity.ok("ack");
                    }
                    return null;
                });
        field("wechatGatewaySMOImpl").set(controller, service);
    }

    private Field field(String name) throws Exception {
        Field field = WechatGatewayController.class.getDeclaredField(name);
        field.setAccessible(true);
        return field;
    }

    private HttpServletRequest request(Map<String,String> params) {
        return (HttpServletRequest) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class[]{HttpServletRequest.class}, (proxy, method, args) -> {
                    if ("getRequestURI".equals(method.getName())) return "/app/wechat/testCallback";
                    if ("getParameter".equals(method.getName())) return params.get(args[0]);
                    return null;
                });
    }

    private static String signature(String token, String timestamp, String nonce) throws Exception {
        String[] parts = {token, timestamp, nonce};
        Arrays.sort(parts);
        byte[] digest = MessageDigest.getInstance("SHA-1")
                .digest((parts[0] + parts[1] + parts[2]).getBytes(StandardCharsets.UTF_8));
        StringBuilder hex = new StringBuilder();
        for (byte value : digest) hex.append(String.format("%02x", value & 0xff));
        return hex.toString();
    }

    private Map<String,String> validParams() throws Exception {
        Map<String,String> params = new HashMap<>();
        params.put("timestamp", "1700000000");
        params.put("nonce", "test-nonce");
        params.put("echostr", "wechat-echo");
        params.put("signature", signature(properties.getCallbackToken(), "1700000000", "test-nonce"));
        return params;
    }

    @Test public void validChallengeReturnsOriginalEcho() throws Exception {
        ResponseEntity<String> result = controller.gateway(request(validParams()));
        assertEquals(HttpStatus.OK, result.getStatusCode());
        assertEquals("wechat-echo", result.getBody());
    }

    @Test public void wrongSignatureAndMissingTokenAreRejected() throws Exception {
        Map<String,String> params = validParams();
        params.put("signature", signature("other-token", "1700000000", "test-nonce"));
        assertEquals(HttpStatus.FORBIDDEN, controller.gateway(request(params)).getStatusCode());
        properties.setCallbackToken("");
        assertEquals(HttpStatus.SERVICE_UNAVAILABLE, controller.gateway(request(params)).getStatusCode());
    }

    @Test public void messageUsesConfiguredAccountInsteadOfQueryOverrides() throws Exception {
        Map<String,String> params = validParams();
        params.put("java110AppId", "attacker-app");
        params.put("wId", "attacker-account");
        String xml = "<xml><FromUserName>from</FromUserName><ToUserName>to</ToUserName>"
                + "<MsgType>text</MsgType><Content>hello</Content></xml>";
        ResponseEntity<String> result = controller.gateway(xml, request(params));
        assertEquals(HttpStatus.OK, result.getStatusCode());
        assertEquals("ack", result.getBody());
        assertNotNull(message.get());
        assertEquals(AppDto.WECHAT_OWNER_APP_ID, message.get().getAppId());
        assertEquals("wx-test", WechatFactory.getAppId(messageWId.get()));
    }
}
