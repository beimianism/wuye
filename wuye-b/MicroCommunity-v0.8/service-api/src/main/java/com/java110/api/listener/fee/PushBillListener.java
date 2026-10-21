package com.java110.api.listener.fee;

import com.alibaba.fastjson.JSONObject;
import com.java110.api.bmo.fee.impl.BillNotificationService;
import com.java110.api.listener.AbstractServiceApiListener;
import com.java110.core.annotation.Java110Listener;
import com.java110.core.context.DataFlowContext;
import com.java110.core.event.service.api.ServiceDataFlowEvent;
import com.java110.utils.util.Assert;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.*;
import java.util.Map;

@Java110Listener("pushBillListener")
public class PushBillListener extends AbstractServiceApiListener {
    @Autowired private BillNotificationService billNotificationService;
    @Override public String getServiceCode() { return "fee.pushBill"; }
    @Override public HttpMethod getHttpMethod() { return HttpMethod.POST; }
    @Override protected void validate(ServiceDataFlowEvent event,JSONObject request) {
        Assert.hasKeyAndValue(request,"communityId","缺少小区信息");
        Assert.hasKeyAndValue(request,"oweId","缺少账单明细");
        Assert.hasKeyAndValue(request,"requestId","缺少请求标识");
    }
    @Override protected void doSoService(ServiceDataFlowEvent event,DataFlowContext context,JSONObject request) {
        Map<String,String> headers=context.getRequestCurrentHeaders();
        JSONObject result=billNotificationService.send(request.getString("communityId"),request.getString("oweId"),request.getString("requestId"),headers.get("store-id"),headers.get("user-id"));
        context.setResponseEntity(new ResponseEntity<String>(result.toJSONString(),HttpStatus.OK));
    }
}
