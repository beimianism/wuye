"""Verify notification-state updates cannot overwrite payment (dedicated local DB only)."""
import os
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET
sys.path.insert(0, str(Path(__file__).parents[1]))
import local


@unittest.skipUnless(os.environ.get('WUYE_LOCAL_DB_TESTS') == '1', 'Requires isolated MySQL on 13306')
class NotificationPaymentRaceTests(unittest.TestCase):
    def test_notify_keeps_paid_state_and_can_update_unpaid(self):
        mapper = local.BACK / 'java110-db/src/main/resources/mapper/fee/FeeServiceDaoImplMapper.xml'
        update = next(n for n in ET.parse(mapper).getroot().findall('update') if n.get('id') == 'updateBillOweFees')
        sql = update.text
        for child in update:
            sql += (child.text or '') + (child.tail or '')
        for key, value in {'state': '3000', 'feeId': 'fee', 'communityId': 'community', 'billId': 'bill', 'oweId': 'selected'}.items():
            sql = sql.replace('#{' + key + '}', "'" + value + "'")
        result = local.mysql_run("CREATE TEMPORARY TABLE bill_owe_fee (fee_id varchar(30), community_id varchar(30),bill_id varchar(30),state varchar(12),owe_id varchar(30));"
                                 "INSERT INTO bill_owe_fee VALUES ('fee','community','bill','2000','selected'),('fee','community','bill','1000','selected'),('fee','community','bill','1000','other');"
                                 + sql + ";SELECT state FROM bill_owe_fee ORDER BY state;", database='TT', capture=True)
        self.assertEqual(result.splitlines(), ['1000', '2000', '3000'])


if __name__ == '__main__':
    unittest.main()
