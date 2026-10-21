package com.java110.front.smo.payment.adapt.wechatPay;
import com.java110.dto.smallWeChat.SmallWeChatDto;
import org.junit.Test;
import static org.junit.Assert.*;
public class WechatPayUnavailableTest {
    @Test public void missingMerchantConfigurationFailsBeforeExternalOrCacheAccess() throws Exception {
        try {
            new WechatPayAdapt().java110Payment(null,"test","JSAPI","test-order",1,"openid",new SmallWeChatDto());
            fail("unconfigured payment accepted");
        } catch (IllegalArgumentException expected) { assertTrue(expected.getMessage().contains("未开通")); }
    }
}
