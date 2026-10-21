package com.java110.api.listener.room;

import com.alibaba.fastjson.JSONObject;
import com.java110.dto.FloorDto;
import com.java110.intf.community.IFloorInnerServiceSMO;
import org.junit.Test;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;

public class QueryRoomsListenerTest {
    @Test
    public void queryWithoutFloorDoesNotRequireExistingFloors() throws Exception {
        FloorLookup lookup = new FloorLookup(0);
        validate(request(), lookup);
        assertEquals(0, lookup.calls);
    }

    @Test
    public void queryWithEmptyFloorDoesNotRequireExistingFloors() throws Exception {
        FloorLookup lookup = new FloorLookup(0);
        JSONObject request = request();
        request.put("floorId", "");
        validate(request, lookup);
        assertEquals(0, lookup.calls);
    }

    @Test
    public void suppliedFloorIsCheckedWithinRequestedCommunity() throws Exception {
        FloorLookup lookup = new FloorLookup(1);
        JSONObject request = request();
        request.put("floorId", "floor-1");
        validate(request, lookup);
        assertEquals(1, lookup.calls);
        assertEquals("floor-1", lookup.filter.getFloorId());
        assertEquals("community-1", lookup.filter.getCommunityId());
    }

    @Test
    public void floorOutsideRequestedCommunityIsRejected() throws Exception {
        FloorLookup lookup = new FloorLookup(0);
        JSONObject request = request();
        request.put("floorId", "other-community-floor");
        try {
            validate(request, lookup);
            fail("A floor outside the requested community must be rejected");
        } catch (IllegalArgumentException expected) {
            assertEquals("传入小区楼ID不是该小区的楼", expected.getMessage());
        }
        assertEquals(1, lookup.calls);
        assertEquals("other-community-floor", lookup.filter.getFloorId());
        assertEquals("community-1", lookup.filter.getCommunityId());
    }

    private JSONObject request() {
        JSONObject request = new JSONObject();
        request.put("communityId", "community-1");
        request.put("page", 1);
        request.put("row", 10);
        return request;
    }

    private void validate(JSONObject request, FloorLookup lookup) throws Exception {
        QueryRoomsListener listener = new QueryRoomsListener();
        listener.setFloorInnerServiceSMOImpl((IFloorInnerServiceSMO) Proxy.newProxyInstance(
                IFloorInnerServiceSMO.class.getClassLoader(),
                new Class<?>[]{IFloorInnerServiceSMO.class}, lookup));
        Method validate = QueryRoomsListener.class.getDeclaredMethod("validateRoomData", JSONObject.class);
        validate.setAccessible(true);
        try {
            validate.invoke(listener, request);
        } catch (InvocationTargetException exception) {
            throw (Exception) exception.getCause();
        }
    }

    private static class FloorLookup implements InvocationHandler {
        private final int count;
        private int calls;
        private FloorDto filter;

        private FloorLookup(int count) {
            this.count = count;
        }

        @Override
        public Object invoke(Object proxy, Method method, Object[] arguments) {
            if (!"queryFloorsCount".equals(method.getName())) {
                throw new AssertionError("Unexpected floor service call: " + method.getName());
            }
            calls++;
            filter = (FloorDto) arguments[0];
            return count;
        }
    }
}
