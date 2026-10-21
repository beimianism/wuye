import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

spec = importlib.util.spec_from_file_location('owner_h5_fixture', Path(__file__).with_name('fixture.py'))
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


class FixtureOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.record = Path(self.temp.name) / 'fixture.json'
        self.data = {'label':fixture.LABEL,'prefix':fixture.PREFIX,'ids':fixture.IDS,
                     'createdUserId':'generated-test-account','phone':'19900000000','ownerName':'test-owner'}
        self.record.write_text(json.dumps(self.data),encoding='utf-8')
        self.addCleanup(self.temp.cleanup)

    def test_cleanup_preserves_account_when_binding_does_not_match(self):
        with patch.object(fixture,'RECORD',self.record),patch.object(fixture,'ensure_local'),patch.object(fixture,'query',return_value='0') as query:
            with self.assertRaisesRegex(RuntimeError,'ownership'):
                fixture.cleanup()
            self.assertFalse(any('DELETE' in call.args[0] for call in query.call_args_list))

    def test_cleanup_preserves_account_that_acquired_another_binding(self):
        with patch.object(fixture,'RECORD',self.record),patch.object(fixture,'ensure_local'),patch.object(fixture,'query',side_effect=['1','1']) as query:
            with self.assertRaisesRegex(RuntimeError,'other owner bindings'):
                fixture.cleanup()
            self.assertFalse(any('DELETE' in call.args[0] for call in query.call_args_list))

    def test_cleanup_rejects_record_with_non_fixture_ids(self):
        self.data['ids'] = {**fixture.IDS,'member':'original-owner-member'}
        self.record.write_text(json.dumps(self.data),encoding='utf-8')
        with patch.object(fixture,'RECORD',self.record),patch.object(fixture,'ensure_local'),patch.object(fixture,'query') as query:
            with self.assertRaisesRegex(RuntimeError,'Unrecognized'):
                fixture.cleanup()
            query.assert_not_called()

    def test_cleanup_cannot_adopt_unrecorded_accounts(self):
        del self.data['createdUserId']
        self.record.write_text(json.dumps(self.data),encoding='utf-8')
        with patch.object(fixture,'RECORD',self.record),patch.object(fixture,'ensure_local'),patch.object(fixture,'query',return_value='1') as query:
            with self.assertRaisesRegex(RuntimeError,'Unrecorded account'):
                fixture.cleanup()
            self.assertFalse(any('DELETE' in call.args[0] for call in query.call_args_list))


@unittest.skipUnless(os.environ.get('WUYE_LOCAL_DB_TESTS') == '1','Requires dedicated loopback DB on 13306')
class MapperSchemaTests(unittest.TestCase):
    def test_retained_owner_room_and_bill_mapper_columns_exist(self):
        root = fixture.ROOT / 'wuye-b/MicroCommunity-v0.8/java110-db/src/main/resources/mapper'
        pairs = [('user/OwnerAppUserServiceDaoImplMapper.xml','getOwnerAppUserInfo'),
                 ('community/RoomServiceDaoImplMapper.xml','getRoomInfoByOwner'),
                 ('fee/FeeServiceDaoImplMapper.xml','getFeeInfo')]
        for file,name in pairs:
            with self.subTest(mapper=name):
                mapper = ET.parse(root / file)
                sql = next(node.text for node in mapper.getroot().findall('select') if node.get('id') == name)
                # The fixed SELECT/JOIN before optional dynamic filters is the
                # actual mapper projection; MySQL validates it without reading data.
                fixture.query(sql + ' LIMIT 0')


if __name__ == '__main__':
    unittest.main()
