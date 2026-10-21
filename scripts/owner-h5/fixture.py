"""Optional, explicitly synthetic owner/room/bill fixture in the isolated local DB."""
import argparse
import json
import re
import secrets
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import local

PREFIX = 'WXTEST20261021'
LABEL = 'LOCAL WECHAT TEST ONLY - NOT A REAL OWNER OR BILL'
RECORD = ROOT / '.runtime/wechat-test-fixture.json'
IDS = {name:PREFIX + suffix for name,suffix in {'floor':'F','unit':'U','room':'R','owner':'O','member':'M','rel':'REL','config':'C','fee':'FEE','business':'B'}.items()}


def q(value):
    return "'" + str(value).replace('\\', '\\\\').replace("'", "''") + "'"


def query(sql):
    return local.mysql_run(sql, database='TT', capture=True)


def ensure_local():
    # local.mysql_run hardcodes loopback:13306; never accept another host/database.
    switch = query("SELECT value FROM c_mapping WHERE `key`='SMS_SEND_SWITCH'")
    if switch != 'OFF':
        raise RuntimeError('Fixture requires SMS_SEND_SWITCH=OFF; no SMS operation was performed')


def create():
    ensure_local()
    config = json.loads((ROOT / '.runtime/wechat-test.json').read_text(encoding='utf-8-sig'))
    community = config['communityId']
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,30}', community):
        raise ValueError('Invalid local community ID')
    details = query(f"SELECT name,city_code FROM s_community WHERE community_id={q(community)} AND status_cd='0' AND state='1100'").split('\t')
    if len(details) != 2:
        raise RuntimeError('Configure one valid existing community first')
    record = json.loads(RECORD.read_text(encoding='utf-8')) if RECORD.exists() else {
        'label':LABEL,'prefix':PREFIX,'communityId':community,'communityName':details[0],
        'areaCode':details[1],'ownerName':'联调测试业主','phone':'19900000000',
        'password':secrets.token_urlsafe(24),
        'ids':IDS
    }
    if record['communityId'] != community or record['label'] != LABEL or record['ids'] != IDS:
        raise RuntimeError('Existing fixture record belongs to a different configuration')
    ids = record['ids']
    user = query("SELECT user_id FROM u_user WHERE status_cd='0' ORDER BY id LIMIT 1")
    store = query("SELECT store_id FROM s_store WHERE status_cd='0' ORDER BY store_id LIMIT 1")
    if not user or not store:
        raise RuntimeError('A local admin user and store are required')
    common = {'b_id':ids['business'],'user_id':user,'remark':LABEL,'status_cd':'0'}
    rows = [
        ('f_floor','floor_id',{**common,'floor_id':ids['floor'],'floor_num':'T1','name':'联调测试楼','community_id':community,'floor_area':'90'}),
        ('building_unit','unit_id',{**common,'unit_id':ids['unit'],'unit_num':'1','floor_id':ids['floor'],'layer_count':'1','lift':'1010','unit_area':'90'}),
        ('building_room','room_id',{**common,'room_id':ids['room'],'room_num':'TEST101','unit_id':ids['unit'],'layer':'1','apartment':'10101','built_up_area':'90','state':'2001','community_id':community,'room_type':'1010301'}),
        ('building_owner','member_id',{**common,'member_id':ids['member'],'owner_id':ids['owner'],'name':record['ownerName'],'sex':'1','age':'30','link':record['phone'],'community_id':community,'id_card':'-1','owner_type_cd':'1001'}),
        ('building_owner_room_rel','rel_id',{**common,'rel_id':ids['rel'],'owner_id':ids['owner'],'room_id':ids['room'],'state':'2001'}),
        ('pay_fee_config','config_id',{'config_id':ids['config'],'b_id':ids['business'],'community_id':community,'fee_type_cd':'888800010001','square_price':'0','additional_amount':'0.01','start_time':'2026-10-01','end_time':'2026-11-01','fee_flag':'2006012','fee_name':'联调测试账单（禁止支付）','computing_formula':'2002','computing_formula_text':LABEL,'bill_type':'005','payment_cycle':'1','payment_cd':'1200','status_cd':'0'}),
        ('pay_fee','fee_id',{'fee_id':ids['fee'],'b_id':ids['business'],'fee_type_cd':'888800010001','community_id':community,'payer_obj_id':ids['room'],'income_obj_id':store,'start_time':'2026-10-01','end_time':'2026-10-01','amount':'0.01','user_id':user,'fee_flag':'2006012','state':'2008001','config_id':ids['config'],'payer_obj_type':'3333','status_cd':'0'})
    ]
    statements = ['START TRANSACTION']
    for table, key, values in rows:
        existing = query(f'SELECT b_id FROM {table} WHERE {key}={q(values[key])}')
        if existing and existing != ids['business']:
            raise RuntimeError('Fixture ID collision: ' + table)
        columns = ','.join('`' + c + '`' for c in values)
        value_sql = ','.join(q(v) for v in values.values())
        statements.append(f'INSERT INTO {table} ({columns}) SELECT {value_sql} WHERE NOT EXISTS (SELECT 1 FROM {table} WHERE {key}={q(values[key])})')
    statements.append('COMMIT')
    RECORD.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    query(';\n'.join(statements)+';')
    print('Created/preserved 7 labeled local fixture rows; credentials saved only in ignored .runtime file.')


def register():
    ensure_local()
    record = json.loads(RECORD.read_text(encoding='utf-8'))
    if query(f"SELECT count(*) FROM owner_app_user WHERE member_id={q(record['ids']['member'])}") != '0':
        if not record.get('createdUserId'):
            raise RuntimeError('Existing account has no fixture creation provenance; preserving it')
        print('Recorded fixture owner account already registered; preserved existing account.')
        return
    if query(f"SELECT count(*) FROM u_user WHERE tel={q(record['phone'])}") != '0':
        raise RuntimeError('Phone already belongs to an account; preserving it without registration')
    payload = {'communityName':record['communityName'],'areaCode':record['areaCode'],'appUserName':record['ownerName'],'link':record['phone'],'msgCode':'LOCAL_ONLY_NO_SMS','password':record['password'],'remark':LABEL}
    request = urllib.request.Request('http://127.0.0.1:8012/app/owner.ownerRegister',data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json','app-id':'992020061452450002','transaction-id':PREFIX,'req-time':'20261021000000','sign':'1234567','user-id':'-1'},method='POST')
    with urllib.request.urlopen(request,timeout=45) as response:
        result = json.load(response)
    if result.get('code') != 0:
        raise RuntimeError('Registration did not succeed; inspect local backend logs without exposing credentials')
    user = query(f"SELECT u.user_id FROM owner_app_user o JOIN u_user u ON u.user_id=o.user_id WHERE o.member_id={q(record['ids']['member'])} AND o.link={q(record['phone'])} AND u.tel={q(record['phone'])} AND o.remark={q(LABEL)}")
    if not user or '\n' in user:
        raise RuntimeError('Registration provenance could not be verified; preserve rows for review')
    record['createdUserId'] = user
    RECORD.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Local fixture account registered through ownerRegister API; no SMS was requested.')


def cleanup():
    ensure_local()
    record = json.loads(RECORD.read_text(encoding='utf-8'))
    if record.get('label') != LABEL or record.get('prefix') != PREFIX or record.get('ids') != IDS:
        raise RuntimeError('Unrecognized fixture record')
    ids = record['ids']
    user = record.get('createdUserId')
    statements = ['START TRANSACTION']
    if user:
        owned = query(f"SELECT count(*) FROM owner_app_user o JOIN u_user u ON u.user_id=o.user_id WHERE o.member_id={q(ids['member'])} AND o.user_id={q(user)} AND o.link={q(record['phone'])} AND u.tel={q(record['phone'])} AND o.remark={q(LABEL)}")
        if owned != '1':
            raise RuntimeError('Account no longer matches fixture ownership; no cleanup performed')
        others = query(f"SELECT count(*) FROM owner_app_user WHERE user_id={q(user)} AND member_id<>{q(ids['member'])}")
        if others != '0':
            raise RuntimeError('Fixture account now has other owner bindings; preserving it without cleanup')
        for table in ['u_user_attr','business_user_attr','business_user']:
            statements.append(f'DELETE FROM {table} WHERE user_id={q(user)}')
        statements.append(f'DELETE FROM u_user WHERE user_id={q(user)} AND tel={q(record["phone"])} AND name={q(record["ownerName"])}')
    elif query(f"SELECT count(*) FROM owner_app_user WHERE member_id={q(ids['member'])}") != '0':
        raise RuntimeError('Unrecorded account exists; preserving it without cleanup')
    for table in ['owner_app_user','business_owner_app_user']:
        statements.append(f'DELETE FROM {table} WHERE member_id={q(ids["member"])}')
    for table,key,name in [('pay_fee','fee_id','fee'),('pay_fee_config','config_id','config'),('building_owner_room_rel','rel_id','rel'),('building_owner','member_id','member'),('building_room','room_id','room'),('building_unit','unit_id','unit'),('f_floor','floor_id','floor')]:
        statements.append(f'DELETE FROM {table} WHERE {key}={q(ids[name])} AND b_id={q(ids["business"])}')
    statements.append('COMMIT')
    query(';\n'.join(statements)+';')
    print('Removed only recorded local fixture/account rows. Ignored credential record retained for review.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['create','register','cleanup'])
    args = parser.parse_args()
    {'create':create,'register':register,'cleanup':cleanup}[args.action]()
