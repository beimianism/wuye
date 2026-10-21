import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import json
import tempfile

spec = importlib.util.spec_from_file_location('wechat_test', Path(__file__).parents[1] / 'wechat_test.py')
wechat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wechat)


class WechatSetupTests(unittest.TestCase):
    def test_stop_tunnel_checks_project_marker_for_each_supported_provider(self):
        for marker in ['wechat-tunnel-known-hosts', 'wechat-pinggy-known-hosts', None]:
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                state = Path(directory) / 'state.json'
                state.write_text(json.dumps({'pid': 12345}))
                command = 'ssh -o UserKnownHostsFile=' + str((wechat.local.RUN / marker).resolve()) if marker else 'ssh unrelated-host'
                queried = SimpleNamespace(stdout=json.dumps({'CommandLine': command}))
                with patch.object(wechat, 'SSH_STATE', state), patch.object(wechat.subprocess, 'run', return_value=queried) as run:
                    wechat.stop_tunnel()
                kills = [call for call in run.call_args_list if call.args[0][0] == 'taskkill']
                self.assertEqual(len(kills), 1 if marker else 0)

    def test_pinggy_origin_uses_tunnel_host_not_provider_upgrade_link(self):
        log = ('Upgrade at https://dashboard.pinggy.io\n'
               '\x1b[32mhttps://sample-112-27-254-11.free.pinggy.net\x1b[0m\n'
               'https://other-112-27-254-11.run.pinggy-free.link\n')
        self.assertEqual(wechat.tunnel_origin(log), 'https://sample-112-27-254-11.free.pinggy.net')
        self.assertIsNone(wechat.tunnel_origin('Upgrade at https://dashboard.pinggy.io\nhttps://example.com'))

    def test_tunnel_url_ignores_provider_help_links_and_uses_latest_announcement(self):
        help_text = 'Manage domains at https://admin.localhost.run/\nSee https://localhost.run/docs/\n'
        self.assertIsNone(wechat.tunnel_origin(help_text))
        self.assertEqual(wechat.tunnel_origin(help_text + 'abc123.lhr.life tunneled with tls termination, https://abc123.lhr.life\n'), 'https://abc123.lhr.life')
        self.assertEqual(wechat.tunnel_origin('old.lhr.life tunneled with tls termination, https://old.lhr.life\nnew.lhr.life tunneled with tls termination, https://new.lhr.life\n'), 'https://new.lhr.life')

    def test_public_url_requires_https_origin(self):
        self.assertEqual(wechat.public_origin('https://example.com/'), 'https://example.com')
        for value in ['http://example.com', 'https://user:pass@example.com', 'https://example.com/path', 'https://example.com/?key=secret', 'https://example.com/#x']:
            with self.assertRaises(ValueError):
                wechat.public_origin(value)

    def test_handoff_escapes_values_and_never_contains_app_secret(self):
        config = {'publicBaseUrl': 'https://test.example', 'callbackPath': '/app/wechat/gateway?wId=a%2Bb&java110AppId=992020061452450002',
                  'token': 'callback-token', 'accessCode': '<code>', 'appSecret': 'NEVER-IN-HANDOFF'}
        page = wechat.handoff_html(config, {'ownerName': 'local-test-owner', 'password': 'local-test-password'})
        self.assertNotIn(config['appSecret'], page)
        self.assertIn('&lt;code&gt;', page)
        self.assertIn('callback-token', page)
        self.assertIn('test.example', page)
        self.assertIn('local-test-owner', page)
        self.assertIn('local-test-password', page)
        self.assertIn('https://test.example/wechat-test/callback', page)


if __name__ == '__main__':
    unittest.main()
