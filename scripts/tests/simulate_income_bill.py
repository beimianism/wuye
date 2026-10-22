"""Exercise the admin payment report SQL with an isolated 0.01 yuan fixture.

This uses SQLite in memory, so it never creates a real bill, payment, or receipt.
Run: python3 scripts/tests/simulate_income_bill.py
"""
import json
from pathlib import Path
import re
import sqlite3
from decimal import Decimal


ROOT = Path(__file__).resolve().parents[2]
QUERIES = json.loads((ROOT / 'scripts/local-payments-query.json').read_text(encoding='utf-8'))['queries']


def render(sql):
    # Select the no-filter branch of the project's MyBatis-style query.
    sql = re.sub(r'<if test="[^"]+">.*?</if>', '', sql, flags=re.S)
    return re.sub(r'#(\w+)#', r':\1', sql)


def main():
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    db.create_function('DATE_FORMAT', 2, lambda value, _format: value)
    db.executescript('''
        CREATE TABLE pay_fee(fee_id TEXT, status_cd TEXT, payer_obj_type TEXT,
            payer_obj_id TEXT, income_obj_id TEXT, config_id TEXT);
        CREATE TABLE pay_fee_detail(fee_id TEXT, detail_id TEXT, status_cd TEXT,
            community_id TEXT, b_id TEXT, cycles INTEGER, prime_rate REAL,
            receivable_amount REAL, received_amount REAL, create_time TEXT);
        CREATE TABLE pay_fee_config(config_id TEXT, status_cd TEXT, fee_name TEXT, fee_type_cd TEXT);
        CREATE TABLE t_dict(status_cd TEXT, table_name TEXT, table_columns TEXT, name TEXT);
        CREATE TABLE c_business(b_id TEXT, o_id TEXT);
        CREATE TABLE c_orders(o_id TEXT, user_id TEXT);
        CREATE TABLE u_user(user_id TEXT, name TEXT);
        CREATE TABLE building_owner(owner_id TEXT, name TEXT, status_cd TEXT, owner_type_cd TEXT);
        CREATE TABLE building_owner_room_rel(owner_id TEXT, room_id TEXT, status_cd TEXT);
        CREATE TABLE owner_car(owner_id TEXT, car_id TEXT, status_cd TEXT);
        INSERT INTO pay_fee_config VALUES ('cfg','0','物业费','8888');
        INSERT INTO t_dict VALUES ('8888','pay_fee_config','fee_type_cd','物业费');
        INSERT INTO building_owner VALUES ('owner','联调测试业主','0','1001');
        INSERT INTO building_owner_room_rel VALUES ('owner','TEST101','0');
        INSERT INTO c_business VALUES ('biz','order');
        INSERT INTO c_orders VALUES ('order','staff');
        INSERT INTO u_user VALUES ('staff','联调收银员');
        INSERT INTO pay_fee VALUES
            ('paid','0','3333','TEST101','store','cfg'),
            ('unpaid','0','3333','TEST101','store','cfg'),
            ('other-store','0','3333','TEST101','other','cfg');
        INSERT INTO pay_fee_detail VALUES
            ('paid','detail-paid','0','community','biz',1,1,0.01,0.01,'2026-10-22 12:00:00'),
            ('other-store','detail-other','0','community','biz',1,1,9.99,9.99,'2026-10-22 12:01:00');
    ''')
    params = {'storeId': 'store', 'communityId': 'community', 'page': 0, 'row': 10}
    rows = db.execute(render(QUERIES['param1']), params).fetchall()
    count = db.execute(render(QUERIES['param2']), params).fetchone()['total']
    totals = db.execute(render(QUERIES['param3']), params).fetchone()
    assert count == len(rows) == 1
    assert rows[0]['feeId'] == 'paid'
    assert rows[0]['payObjName'] == '联调测试业主'
    assert rows[0]['feeName'] == '物业费'
    assert Decimal(str(rows[0]['receivedAmount'])) == Decimal('0.01')
    assert Decimal(str(totals['allReceivedAmount'])) == Decimal('0.01')
    assert Decimal(str(totals['allReceivableAmount'])) == Decimal('0.01')
    print(json.dumps({
        'mode': 'isolated_in_memory_admin_report_sql',
        'reportCode': 'api.getListPayFee',
        'rows': count,
        'receivedAmount': '0.01',
        'unpaidExcluded': True,
        'otherStoreExcluded': True,
        'realPaymentCreated': False,
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
