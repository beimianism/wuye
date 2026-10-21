import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('wuye_local', Path(__file__).parents[1] / 'local.py')
local = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local)


class LocalConfigTests(unittest.TestCase):
    def test_all_services_use_isolated_middleware(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(local, 'RUN', Path(directory)), patch.object(local, 'settings', return_value={'db_password': 'test_only'}):
            local.configure()
            for name, port in local.SERVICES.items():
                text = (Path(directory) / f'config/{name}.properties').read_text()
                self.assertIn(f'server.port={port}', text)
                self.assertIn('server.address=127.0.0.1', text)
                self.assertIn('spring.redis.port=16379', text)
                self.assertIn('kafka.producer.servers=127.0.0.1:19092', text)
                self.assertIn('java110.code.zookeeper.port=12181', text)
                self.assertNotIn('dev.java110.com', text)
                source = local.BACK / f'service-{name}/src/main/resources/dataSource.yml'
                if source.exists():
                    datasource = (Path(directory) / f'config/{name}-datasource.yml').read_text()
                    active = '\n'.join(line for line in datasource.splitlines() if not line.lstrip().startswith('#'))
                    self.assertNotIn('dev.db.java110.com', active)
                    self.assertNotIn('password: TT@', active)
                    self.assertIn('127.0.0.1:13306/TT', active)
                    self.assertIn('shardingRule:', active)
                    self.assertIn('java110.datasource.config=file:', text)

    def test_existing_import_never_reimports_business_data(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(local, 'RUN', Path(directory)), patch.object(local, 'mysql_run') as mysql:
            (Path(directory) / 'database-imported.json').write_text('{}')
            local.import_db()
            for call in mysql.call_args_list:
                self.assertNotIn('DROP', call.args[0])
                self.assertNotIn('CREATE DATABASE', call.args[0])

    def test_launch_overrides_packaged_dev_profile_without_command_line_secrets(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(local, 'RUN', Path(directory)), patch.object(local, 'BACK', Path(directory) / 'backend'), patch.object(local, 'settings', return_value={'db_password': 'test_only'}), patch.object(local, 'java', return_value='java.exe'), patch.object(local, 'spawn') as spawn:
            jar = local.BACK / 'service-eureka/target/service-eureka.jar'
            jar.parent.mkdir(parents=True)
            jar.touch()
            local.start(['eureka'])
            import json
            values = json.loads(spawn.call_args.kwargs['env']['SPRING_APPLICATION_JSON'])
            self.assertEqual(values['spring.redis.port'], '16379')
            self.assertEqual(values['spring.datasource.password'], 'test_only')
            self.assertNotIn('test_only', str(spawn.call_args.args))


if __name__ == '__main__':
    unittest.main()
