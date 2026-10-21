"""Real MySQL checks; temporary tables shadow empty demo tables in this session only."""
import json
import os
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))
import local


@unittest.skipUnless(os.environ.get('WUYE_TEST_MYSQL') == '1', 'Set WUYE_TEST_MYSQL=1 with isolated MySQL running')
class PaymentQueryTests(unittest.TestCase):
    def query(self, values):
        queries = json.loads((local.ROOT / 'scripts/local-payments-query.json').read_text(encoding='utf-8'))['queries']
        fixture = """
USE TT;
CREATE TEMPORARY TABLE pay_fee(fee_id varchar(30),status_cd varchar(2),payer_obj_type varchar(12),payer_obj_id varchar(30),income_obj_id varchar(30),config_id varchar(30));
CREATE TEMPORARY TABLE pay_fee_detail(fee_id varchar(30),detail_id varchar(30),status_cd varchar(2),community_id varchar(30),b_id varchar(30),cycles int,prime_rate decimal(3,2),receivable_amount decimal(10,2),received_amount decimal(10,2),create_time datetime);
CREATE TEMPORARY TABLE pay_fee_config(config_id varchar(30),status_cd varchar(2),fee_name varchar(50),fee_type_cd varchar(12));
CREATE TEMPORARY TABLE t_dict(status_cd varchar(12),table_name varchar(50),table_columns varchar(50),name varchar(50));
CREATE TEMPORARY TABLE c_business(b_id varchar(30),o_id varchar(30));
CREATE TEMPORARY TABLE c_orders(o_id varchar(30),user_id varchar(30));
CREATE TEMPORARY TABLE u_user(user_id varchar(30),name varchar(50));
INSERT INTO pay_fee_config VALUES ('cfg','0','Property','888');
INSERT INTO pay_fee VALUES ('a','0','3333','room','store','cfg'),('b','0','6666','car','store','cfg'),('otherstore','0','3333','room','other','cfg'),('deleted','1','3333','room','store','cfg');
INSERT INTO c_business VALUES ('biz','order'); INSERT INTO c_orders VALUES ('order','staff'); INSERT INTO u_user VALUES ('staff','Cashier');
INSERT INTO pay_fee_detail VALUES
('a','d1','0','community','biz',1,1,100,90,'2026-10-01'),
('b','d2','0','community','biz',1,1,50,50,'2026-10-02'),
('otherstore','d3','0','community','biz',1,1,999,999,'2026-10-03'),
('deleted','d4','0','community','biz',1,1,999,999,'2026-10-03'),
('a','d5','0','othercommunity','biz',1,1,999,999,'2026-10-03'),
('a','d6','1','community','biz',1,1,999,999,'2026-10-03');
"""
        params = dict(storeId='store', communityId='community', page=0, row=10,
                      startTime='', endTime='', configId='', userCode='', primeRate='')
        params.update(values)
        def render(sql):
            def condition(match):
                key = re.search(r'^(\w+)', match[1])[1]
                return match[2] if params.get(key) not in ('', None) else ''
            sql = re.sub(r'<if test="([^"]+)">(.*?)</if>', condition, sql, flags=re.S)
            sql = sql.replace('&gt;', '>').replace('&lt;', '<')
            return re.sub(r'#(\w+)#', lambda m: str(params[m[1]]) if isinstance(params[m[1]], int) else "'" + str(params[m[1]]).replace("'", "''") + "'", sql)
        statements = fixture + '\n'.join(render(queries[key]) + ';' for key in ('param1', 'param2', 'param3'))
        return local.mysql_run(statements, capture=True).splitlines()

    def test_mixed_types_share_total_sum_and_tenant_scope(self):
        rows = self.query({})
        self.assertEqual(len(rows), 4)
        self.assertIn('\td2\t', rows[0])
        self.assertIn('\td1\t', rows[1])
        self.assertEqual(rows[-2:], ['2', '150.00\t140.00'])

    def test_pagination_and_date_filters_apply_to_totals(self):
        rows = self.query({'startTime': '2026-10-02', 'row': 1})
        self.assertEqual(len(rows), 3)
        self.assertIn('\td2\t', rows[0])
        self.assertEqual(rows[-2:], ['1', '50.00\t50.00'])
        self.assertEqual(self.query({'communityId': 'empty'})[-2:], ['0', '0.00\t0.00'])


if __name__ == '__main__':
    unittest.main()
