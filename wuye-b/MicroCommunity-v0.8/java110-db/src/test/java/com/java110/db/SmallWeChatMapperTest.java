package com.java110.db;

import org.apache.ibatis.builder.xml.XMLMapperBuilder;
import org.apache.ibatis.session.Configuration;
import org.junit.Test;
import java.io.*;
import java.util.*;
import static org.junit.Assert.*;

public class SmallWeChatMapperTest {
    @Test public void clearingPaymentPairWritesBothEmptyFields() throws Exception {
        String local = "src/main/resources/mapper/store/SmallWeChatServiceDaoImplMapper.xml";
        String path = System.getProperty("wechat.mapper", new File(local).isFile() ? local : "wuye-b/MicroCommunity-v0.8/java110-db/" + local);
        Configuration configuration = new Configuration();
        try (InputStream input = new FileInputStream(path)) {
            new XMLMapperBuilder(input,configuration,path,configuration.getSqlFragments()).parse();
        }
        Map<String,Object> fields = new HashMap<>();
        fields.put("weChatId","test-id"); fields.put("statusCd","0");
        fields.put("payPassword",""); fields.put("mchId","");
        String sql = configuration.getMappedStatement("smallWeChatServiceDaoImpl.updateSmallWeChatInfoInstance")
            .getBoundSql(fields).getSql();
        assertTrue(sql,sql.contains("t.pay_password="));
        assertTrue(sql,sql.contains("t.mch_id="));
    }
}
