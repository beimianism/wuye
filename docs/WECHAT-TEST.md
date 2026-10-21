# 公众号测试号与本地系统联调

本轮采用微信官方测试号 + 现有业主 H5 + 本机管理后台。现有未认证服务号和未开通的微信支付不参与真实收款。测试号凭据保存在 Git 忽略的 `.runtime/wechat-test.json`，不需要发送到聊天或提交仓库。

## 启动和停止

在项目根目录使用 PowerShell：

```powershell
python scripts/local.py infra
python scripts/local.py start all
node scripts/owner-h5.cjs build
python scripts/wechat_test.py start
python scripts/wechat_test.py tunnel
python scripts/wechat_test.py status
```

H5 工具链安装和首次构建见 [OWNER-H5.md](OWNER-H5.md)。管理后台地址为 `http://127.0.0.1:3000`；受限业主入口为 `http://127.0.0.1:8080`；H5 静态服务绑定本机 `8000`。自定义 `ownerH5Port` 后需重启 H5 和受限入口。

`tunnel` 使用 Windows OpenSSH 将本机受限入口转发到临时 HTTPS 域名，地址写回本地配置，并更新独立数据库的 `OWNER_WECHAT_URL` 和欠费页面链接。匿名隧道可能在运行中或重启后更换域名；本次已观察到运行中换域名，旧域名返回 502。遇到此情况重新执行 `tunnel`，打开新生成的填写说明，并重新设置微信平台 URL 和授权域名。当前环境 Cloudflare 的连接测试未通过，采用 SSH 临时入口；这不是长期固定的测试环境。

```powershell
# 只停止业主入口及对应 SSH 隧道，保留本地管理后台
python scripts/wechat_test.py stop

# 使用其他已准备好的 HTTPS 隧道地址
python scripts/wechat_test.py set-public https://你的临时域名

# 根据已导入的后台公众号记录重新生成本地填写说明
python scripts/wechat_test.py handoff
```

## 微信平台填写

1. 登录 [微信公众平台接口测试号](https://mp.weixin.qq.com/debug/cgi-bin/sandbox?t=sandbox/login)。AppID/AppSecret 已填写时不用重复操作。新机器先执行 `python scripts/wechat_test.py init`；重新填写可以运行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/wechat-test-setup.ps1`，密钥输入框为隐藏输入。
2. 后台公众号记录保存成功，并将其属性 `33001` 改为本地 Token 后，生成 `.runtime/wechat-test-handoff.html`。此页只含填写所需回调地址、Token、域名、入口及访问码，不含 AppSecret。
3. 打开该本地说明页，将短 URL `https://<临时域名>/wechat-test/callback` 和 Token 填入测试号平台的「接口配置信息」，点击提交；在「网页授权获取用户基本信息」中设置授权回调域名，只填主机名。「JS接口安全域名」是另一项设置，保存它不代表网页授权域名已保存。
4. 手机微信扫码关注测试号，在微信内打开临时 HTTPS 地址，输入测试访问码，进入业主页面。实际 OAuth 必须在微信内由用户完成授权。
5. 绑定业主后检查「我的房屋」、物业费及账单详情。新数据库没有真实业主、房屋和费用时，需要先录入业务数据或使用明确标识的本机联调数据。

公众号内部应用 ID 为 `992020061452450002`，与微信 `wx...` AppID 不同。短回调的 GET 校验由入口检查 Token 签名后直接返回原始 echostr；POST 消息转发至配置中的后台回调，使用可信的内部应用 ID 和编码后的 `wId`，由后台再次验签。详细后端协议见 [WECHAT-BACKEND.md](WECHAT-BACKEND.md)。

## 开放范围与当前边界

公网入口只允许列明的业主接口、H5 静态文件及微信验证/授权回调。管理后台、数据库、服务发现及其他内部路径不通过该入口开放。除微信回调外，访问还需要测试访问码；登录后的请求继续由后端校验业主 token。

微信授权返回使用一次性 `authTicket`，不在地址中传递永久用户 key。回调 state 有效期 300 秒且仅消费一次。临时授权票据、本地配置、数据库和日志均不入 Git。

支付接口在此测试入口中关闭，H5 提示「微信支付尚未开通」。未执行真实下单、收款、支付回调、公众号菜单发布或通知发送；测试号授权不代表正式服务号认证完成。账单自动任务仍默认暂停。

本地单元测试、HTTP 测试和模拟浏览器用例不能代替微信平台提交、手机 OAuth 或真实支付验收。实施结果与尚待操作在 [PROJECT-STATUS.md](PROJECT-STATUS.md) 记录。
