# 服务器联调状态（2026-10-21）

目标服务器：`49.232.183.81`；域名：`luci-ona.site`。此文件不包含凭据。

## 已完成

- 通过 `ubuntu` SSH 登录服务器；因当前 WSL 默认网络出口存在大包连接问题，SSH 使用 `curve25519-sha256` 和 `aes128-ctr`，HTTPS 验证使用 `eth2` 出口。
- 保留已停止的 1Panel `wuye-front` 容器。Compose 测试服务改名为 `wuye-front-smoke`，并已启动。`wuye-order` 与 `wuye-eureka` 也已启动。
- 从运行中的 1Panel Redis 读取密码，在服务器私有配置中修正 Redis 连接；从 1Panel MySQL 读取 root 凭据，轮换 `wuye_app` 密码并验证新密码。同步更新 12 份服务 JSON、10 份数据源 YAML。旧配置备份位于 `/srv/wuye/runtime/config/backup-before-credential-fix-20261021170057`，该目录应保持私有。
- 通过 HTTP 验证 OpenResty 到 `service-front` 的 `/app/` 代理；普通缴费和欠费通知接口对无效 XML 都返回 HTTP 200 + 微信格式 `FAIL`。这只验证通知路径和拒绝行为，不代表真实支付成功。
- 为 `luci-ona.site` 签发 Let's Encrypt 证书，配置 OpenResty 的 443 站点和 HTTP→HTTPS 跳转。证书到期日为 2027-01-19；Certbot 定时器处于 enabled/active，部署钩子已手动测试，可复制续期证书并重载 OpenResty。完整续期模拟运行过久，被中止，尚未确认模拟签发结果。
- `service-front` 开启 `server.use-forward-headers=true`，HTTPS 请求的登录跳转现在保持 `https://`。
- 将已提供的公众号测试号 AppID/AppSecret 写入服务器 `/srv/wuye/runtime/config/wechat.env`（权限 0600）。已成功从微信接口获取测试号访问令牌，未在输出中显示令牌。
- 修正业主 H5 的支付状态轮询请求，明确发送 `X-Requested-With: XMLHttpRequest`，使登录失效时收到 HTTP 401，停止轮询并提示重新进入公众号页面。现有支付桥接测试 5 项通过。该源码修正需在后续 H5 构建中发布。

## 验证结果

- `https://luci-ona.site/app/payment/status?orderId=test`：未登录时返回 HTTP 302，跳转到 `https://luci-ona.site/user.html#/pages/frame/login`。这是服务已有的未登录行为。
- 对同一状态接口携带 `X-Requested-With: XMLHttpRequest` 时，公网 HTTPS 返回 HTTP 401，符合业主 H5 修正后的轮询行为。
- `https://luci-ona.site/app/payment/oweFeeNotify`：无效通知报文返回 HTTP 200，内容为微信 `FAIL` XML。
- `wuye-front-smoke` 和 `wuye-order` 均运行且重启次数为 0。`wuye-order` 的本机 8001 端口返回 HTTP 404（根路径无处理器，说明 HTTP 服务已监听）。
- `http://luci-ona.site/` 现在重定向到 HTTPS；ACME 校验路径仍在 HTTP 上直达。

## 仍需完成

1. 业主 H5 源码在 `wuye-xcx2/WechatOwnerService-v0.8`。该旧版 Uni-app 项目需要用 HBuilderX 发行 H5，再把构建产物上传到 1Panel 站点目录 `/opt/1panel/www/sites/wuye-h5/index`。目前该目录只有占位页；`user.html` 也未部署，不能用浏览器完成业主端流程。
2. 在微信测试号后台设置网页授权域名 `luci-ona.site`；若使用 JS-SDK，再设置 JS 接口安全域名 `luci-ona.site`。截图中的消息接口 URL/Token 栏位当前为空，公众号网页授权测试不依赖消息接口配置。
3. 真实 JSAPI 收款还需要正式公众号绑定的普通商户号、APIv2 密钥及商户平台授权目录。测试公众号不能替代真实商户支付联调。不要把商户密钥写入源码或 H5 构建产物。
4. 目前仅启动了基础测试所需的前台、订单、Eureka 和中间件。其余业务服务未启动，完整缴费业务链路和真实支付未验证。

服务器私有配置在 `/srv/wuye/runtime/config`。证书位于 `/etc/letsencrypt/live/luci-ona.site`，OpenResty 使用的副本在 `/opt/1panel/www/sites/wuye-h5/ssl`。两处私钥及数据库配置应保持仅管理员可读。
