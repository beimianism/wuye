package com.java110.api.listener.smallWeChat;

import com.alibaba.fastjson.JSONObject;
import com.java110.dto.app.AppDto;
import com.java110.dto.smallWeChat.SmallWeChatDto;
import com.java110.utils.util.BeanConvertUtil;
import com.java110.vo.api.smallWeChat.ApiSmallWeChatDataVo;
import com.java110.vo.api.smallWeChat.ApiSmallWeChatVo;
import org.junit.Test;
import java.lang.reflect.Method;
import java.util.Collections;
import java.util.List;
import static org.junit.Assert.*;

public class SmallWeChatListContractTest {
    private List<ApiSmallWeChatDataVo> list(String type) {
        SmallWeChatDto saved = new SmallWeChatDto();
        saved.setWeChatType(type); saved.setAppId("wx-synthetic-test");
        saved.setAppSecret("synthetic-list-secret"); saved.setPayPassword("synthetic-pay-key");
        return BeanConvertUtil.covertBeanList(Collections.singletonList(saved),ApiSmallWeChatDataVo.class);
    }
    private String response(List<ApiSmallWeChatDataVo> data) {
        ApiSmallWeChatVo output = new ApiSmallWeChatVo(); output.setSmallWeChats(data);
        return JSONObject.toJSONString(output);
    }
    @Test public void publicAccountTypeSurvivesListResponseRoundTripForOAuth() {
        JSONObject row = JSONObject.parseObject(response(list("1100"))).getJSONArray("smallWeChats").getJSONObject(0);
        SmallWeChatDto actual = BeanConvertUtil.covertBean(row,SmallWeChatDto.class);
        assertEquals("1100",actual.getWeChatType());
    }
    @Test public void miniProgramTypeRemainsDistinctInListResponse() {
        JSONObject row = JSONObject.parseObject(response(list("1000"))).getJSONArray("smallWeChats").getJSONObject(0);
        assertEquals("1000",BeanConvertUtil.covertBean(row,SmallWeChatDto.class).getWeChatType());
    }
    @Test public void webListKeepsTypeWhileRemovingServerCredentials() throws Exception {
        List<ApiSmallWeChatDataVo> data = list("1100");
        Method sanitize = ListSmallWeChatsListener.class.getDeclaredMethod("freshSecure",List.class,String.class);
        sanitize.setAccessible(true); sanitize.invoke(new ListSmallWeChatsListener(),data,AppDto.WEB_APP_ID);
        JSONObject row = JSONObject.parseObject(response(data)).getJSONArray("smallWeChats").getJSONObject(0);
        assertEquals("1100",row.getString("weChatType"));
        assertEquals("",row.getString("appSecret")); assertEquals("",row.getString("payPassword"));
    }
}
