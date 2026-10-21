package com.java110.api.listener.smallWeChat;

import com.alibaba.fastjson.JSONObject;
import com.java110.api.bmo.smallWeChat.impl.SmallWeChatBMOImpl;
import com.java110.core.context.DataFlowContext;
import com.java110.dto.smallWeChat.SmallWeChatDto;
import com.java110.intf.store.ISmallWeChatInnerServiceSMO;
import com.java110.po.store.SmallWechatPo;
import org.junit.Test;
import java.lang.reflect.Field;
import java.lang.reflect.Proxy;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.util.Collections;
import static org.junit.Assert.*;

public class SmallWeChatConfigurationTest {
    private JSONObject config(String type) {
        JSONObject in = new JSONObject();
        in.put("name", "Test account"); in.put("appId", "wx-test");
        in.put("appSecret", "test-secret"); in.put("weChatType", type);
        in.put("weChatId", "test-id"); in.put("objId", "community");
        return in;
    }
    private void validate(JSONObject in) { new SaveSmallWeChatListener().validate(null, in); }
    private void rejects(JSONObject in) {
        try { validate(in); fail("Invalid configuration accepted"); }
        catch (IllegalArgumentException expected) { }
    }
    @Test public void publicAccountWithoutPaymentUsesNonNullEmptyFields() {
        JSONObject in = config("1100"); validate(in);
        assertEquals("", in.getString("payPassword")); assertEquals("", in.getString("mchId"));
    }
    @Test public void publicAccountRejectsEachPartialPaymentConfiguration() {
        JSONObject in = config("1100"); in.put("payPassword", "key"); rejects(in);
        in = config("1100"); in.put("mchId", "merchant"); rejects(in);
    }
    @Test public void publicAccountAcceptsCompletePaymentPair() {
        JSONObject in = config("1100"); in.put("payPassword", "key"); in.put("mchId", "merchant");
        validate(in); assertEquals("key", in.getString("payPassword"));
    }
    @Test public void miniProgramStillRequiresCompletePaymentPair() {
        JSONObject in = config("1000"); rejects(in);
        in.put("payPassword", "key"); rejects(in);
        in.put("mchId", "merchant"); validate(in);
    }
    @Test public void rejectsBlankCredentialsAndUnknownType() {
        JSONObject in = config("1100"); in.put("appSecret", "  "); rejects(in);
        in = config("1100"); in.put("appId", "  "); rejects(in);
        rejects(config("unknown"));
    }
    @Test public void updateValidatesPersistedAccountTypeAndCanClearPayment() throws Exception {
        SmallWeChatBMOImpl bmo = bmo("1100"); JSONObject in = config("1100");
        in.put("payPassword", ""); in.put("mchId", "");
        new UpdateSmallWeChatListener().validate(null, in);
        final JSONObject[] business = new JSONObject[1];
        DataFlowContext context = (DataFlowContext) Proxy.newProxyInstance(getClass().getClassLoader(),
            new Class[]{DataFlowContext.class}, new InvocationHandler() {
                @Override public Object invoke(Object proxy, Method method, Object[] args) {
                if ("addServiceBusiness".equals(method.getName())) business[0] = (JSONObject) args[0];
                return null;
                }
            });
        bmo.updateSmallWeChat(in, context);
        JSONObject saved = business[0].getJSONObject("datas").getJSONArray("SmallWechatPo").getJSONObject(0);
        assertEquals("", saved.getString("payPassword")); assertEquals("", saved.getString("mchId"));
        bmo = bmo("1000");
        try { bmo.updateSmallWeChat(in, context); fail("Public type spoof bypassed mini program validation"); }
        catch (IllegalArgumentException expected) { }
    }
    private SmallWeChatBMOImpl bmo(String storedType) throws Exception {
        final SmallWeChatDto stored = new SmallWeChatDto(); stored.setWeChatId("test-id");
        stored.setWeChatType(storedType); stored.setPayPassword("old-key"); stored.setMchId("old-merchant");
        ISmallWeChatInnerServiceSMO service = (ISmallWeChatInnerServiceSMO) Proxy.newProxyInstance(
            getClass().getClassLoader(), new Class[]{ISmallWeChatInnerServiceSMO.class},
            new InvocationHandler() {
                @Override public Object invoke(Object proxy, Method method, Object[] args) {
                    return Collections.singletonList(stored);
                }
            });
        SmallWeChatBMOImpl bmo = new SmallWeChatBMOImpl();
        Field field = SmallWeChatBMOImpl.class.getDeclaredField("smallWeChatInnerServiceSMOImpl");
        field.setAccessible(true); field.set(bmo, service); return bmo;
    }
}
