"""Local WeChat test ingress. Secrets stay in .runtime; see docs/WECHAT-TEST.md."""
import argparse
import html
import json
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import time
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local

CONFIG = local.RUN / 'wechat-test.json'
SSH_STATE = local.RUN / 'wechat-ssh-tunnel-process.json'
SSH_LOG = local.RUN / 'logs/wechat-ssh-tunnel.log'


def read_config():
    if not CONFIG.exists():
        local.save(CONFIG, {'appId': '', 'appSecret': '', 'token': secrets.token_hex(16),
                           'communityId': '7020181217000001', 'publicBaseUrl': '',
                           'notificationTemplateId': '', 'notificationOpenId': '',
                           'accessCode': secrets.token_urlsafe(24), 'sessionSecret': secrets.token_hex(32),
                           'gatewayPort': 8080, 'ownerH5Port': 8000})
    return json.loads(CONFIG.read_text(encoding='utf-8-sig'))


def public_origin(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment
            or not re.fullmatch(r'[a-zA-Z0-9.:-]+', parsed.netloc)):
        raise ValueError('Use an HTTPS origin only, for example https://test.example.com')
    return 'https://' + parsed.netloc


def tunnel_origin(log):
    announcements = re.findall(r'tunneled with tls termination,\s*(https://[a-zA-Z0-9-]+\.(?:lhr\.life|localhost\.run))', log)
    return announcements[-1] if announcements else None


def handoff_html(config, fixture=None):
    origin = public_origin(config['publicBaseUrl'])
    callback = origin + '/wechat-test/callback'
    values = [('接口配置信息 → URL', callback), ('接口配置信息 → Token', config['token']),
              ('网页授权获取用户基本信息 → 授权回调页面域名', urlsplit(origin).netloc),
              ('手机微信内打开', origin + '/'), ('测试访问码', config['accessCode'])]
    if fixture:
        values.extend([('页面要求登录时 → 本机测试账号', fixture['ownerName']),
                       ('本机测试账号密码', fixture['password']),
                       ('测试房屋 / 费用', 'TEST101；一次性 0.01 元联调测试账单，支付关闭')])
    rows = ''.join('<label>' + html.escape(label) + '</label><pre>' + html.escape(value) + '</pre>' for label, value in values)
    return ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>公众号测试号接入配置</title><style>body{font:16px sans-serif;max-width:900px;margin:40px auto;padding:20px;color:#1e293b}'
            'pre{padding:16px;background:#f1f5f9;white-space:pre-wrap;overflow-wrap:anywhere;user-select:all}label{font-weight:bold}</style>'
            '<h1>公众号测试号接入配置</h1><p>在微信测试号平台填写前两项并点击提交，再设置网页授权域名（仅域名，无 https:// 或路径）。JS接口安全域名与网页授权域名是不同设置，保存前者不代表后者已保存。</p>'
            + rows + '<p>用手机微信扫码关注该测试号后，在微信内打开测试地址并输入访问码。公众号菜单暂未发布，支付暂未开通。</p>'
            '<p>此页只保存在本机，请勿上传到 GitHub。临时隧道重启后域名可能变化，需要重新填写。</p></html>')


def handoff(config=None):
    config = config or read_config()
    if not config.get('callbackPath'):
        raise RuntimeError('Backend account configuration is not imported yet; callbackPath missing.')
    target = local.RUN / 'wechat-test-handoff.html'
    record = local.RUN / 'wechat-test-fixture.json'
    fixture = json.loads(record.read_text(encoding='utf-8')) if record.exists() else None
    target.write_text(handoff_html(config, fixture), encoding='utf-8')
    print('Local configuration guide: ' + str(target))


def set_public(value):
    config = read_config()
    config['publicBaseUrl'] = public_origin(value)
    local.save(CONFIG, config)
    # Update only the project's isolated database; quote URL through a hex literal.
    def literal(text):
        return 'CONVERT(0x' + text.encode().hex() + ' USING utf8mb4)'
    origin = config['publicBaseUrl']
    local.mysql_run('UPDATE TT.c_mapping SET value=' + literal(origin) + " WHERE `key`='OWNER_WECHAT_URL'; "
                    'UPDATE TT.c_mapping SET value=' + literal(origin + '/#/pages/roomOweFee/roomOweFee?roomId=')
                    + " WHERE domain='WECHAT' AND `key`='OWE_FEE_PAGE';")
    print('Public test origin updated: ' + origin)
    if config.get('callbackPath'):
        handoff(config)


def start():
    config = read_config()
    if not config.get('appId') or not config.get('appSecret'):
        raise RuntimeError('Fill AppID/AppSecret using scripts/wechat-test-setup.ps1 first.')
    node = shutil.which('node')
    if not node:
        raise RuntimeError('Node.js is required.')
    env = dict(__import__('os').environ, OWNER_H5_PORT=str(config.get('ownerH5Port', 8000)))
    local.spawn('owner-h5', [node, str(local.ROOT / 'scripts/owner-h5.cjs'), 'serve'], config.get('ownerH5Port', 8000), env=env)
    local.spawn('wechat-gateway', [node, str(local.ROOT / 'scripts/wechat-test-gateway.cjs')], config.get('gatewayPort', 8080))


def stop_tunnel():
    if not SSH_STATE.exists():
        return
    state = json.loads(SSH_STATE.read_text(encoding='utf-8'))
    # Check the recorded process and a project-specific command argument before killing.
    result = subprocess.run(['powershell', '-NoProfile', '-Command',
                             "$p=Get-CimInstance Win32_Process -Filter 'ProcessId=" + str(int(state['pid']))
                             + "'; if ($p) { $p | Select-Object CommandLine | ConvertTo-Json -Compress }"],
                            capture_output=True, text=True)
    actual = json.loads(result.stdout).get('CommandLine', '') if result.stdout.strip() else ''
    marker = str((local.RUN / 'wechat-tunnel-known-hosts').resolve())
    if marker.lower() in actual.lower():
        subprocess.run(['taskkill', '/PID', str(state['pid']), '/T', '/F'], capture_output=True)
        print('WeChat SSH tunnel stopped.')
    SSH_STATE.unlink()


def tunnel():
    config = read_config()
    port = config.get('gatewayPort', 8080)
    if not local.listening(port):
        raise RuntimeError('Start the restricted ingress first.')
    stop_tunnel()
    ssh = shutil.which('ssh')
    if not ssh:
        raise RuntimeError('Windows OpenSSH client is required.')
    SSH_LOG.parent.mkdir(parents=True, exist_ok=True)
    command = [ssh, '-p', '22', '-o', 'StrictHostKeyChecking=accept-new', '-o',
               'UserKnownHostsFile=' + str((local.RUN / 'wechat-tunnel-known-hosts').resolve()),
               '-o', 'ServerAliveInterval=30', '-o', 'ConnectTimeout=20', '-o', 'ExitOnForwardFailure=yes',
               '-T', '-R', f'80:127.0.0.1:{port}', 'nokey@localhost.run']
    with SSH_LOG.open('wb') as output:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS)
    local.save(SSH_STATE, {'pid': process.pid, 'command': command})
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        text = SSH_LOG.read_text(encoding='utf-8', errors='replace')
        origin = tunnel_origin(text)
        if origin:
            set_public(origin)
            return
        if process.poll() is not None:
            raise RuntimeError('SSH tunnel exited; see .runtime/logs/wechat-ssh-tunnel.log')
        time.sleep(1)
    raise RuntimeError('Tunnel URL not ready; see .runtime/logs/wechat-ssh-tunnel.log')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'start', 'tunnel', 'set-public', 'handoff', 'status', 'stop'])
    parser.add_argument('url', nargs='?')
    args = parser.parse_args()
    if args.action == 'init':
        read_config()
        print('Local configuration: ' + str(CONFIG))
    elif args.action == 'set-public':
        set_public(args.url or '')
    elif args.action == 'stop':
        stop_tunnel()
        local.stop(['wechat-gateway', 'owner-h5'])
    elif args.action == 'status':
        config = read_config()
        for name, port in [('Owner H5', config.get('ownerH5Port', 8000)), ('Restricted ingress', config.get('gatewayPort', 8080))]:
            print(f'{name}: {port} {"LISTENING" if local.listening(port) else "STOPPED"}')
        print('Configured public URL: ' + (config.get('publicBaseUrl') or '(not configured)'))
        print('A configured URL does not prove the tunnel is online; check it in a browser.')
    else:
        globals()[args.action]()


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
