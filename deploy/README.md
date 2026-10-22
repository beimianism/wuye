# Linux 部署测试包

本包是 `wuye-feat-local-trim` 的**源码包**，不是已经编译好的服务。建议放在 `/srv/wuye/source`，H5 构建结果放在 `/srv/wuye/h5`，运行密钥放在 `/etc/wuye`，日志放在 `/var/log/wuye`。

## 服务器准备

1. 将压缩包和同名 `.sha256` 上传到服务器，在文件所在目录执行 `sha256sum -c 压缩包名.tar.gz.sha256`。然后创建 `/srv/wuye/source`，执行 `tar -xzf 压缩包名.tar.gz -C /srv/wuye/source --strip-components=1`。不要把真实商户密钥写入源码或 H5 构建文件。
2. 准备 Java 8、Maven，以及本项目实际依赖的 MySQL、Redis、Kafka/ZooKeeper。检查并替换各服务 `application-prod.yml` 中的 `prod.*.java110.com`、数据库和中间件地址；仓库自带的生产配置不能直接用于新服务器。
3. 在服务器 `/etc/wuye/wechat.env` 按 `deploy/wechat.env.example` 配置真实公众号和普通商户 APIv2 凭据，文件权限设为 `0600`，并确保运行 Java 应用的用户有读取权限。`deploy/start-front.sh` 启动时会读取这个文件。公众号测试号密钥只用于 OAuth 测试，不能用于真实 JSAPI 收款。
4. 后端源码在 `wuye-b/MicroCommunity-v0.8`。在 Maven 可访问依赖仓库的环境中执行 `mvn -DskipTests package`，再按服务依赖顺序部署；`service-front` 默认端口为 `8012`。上线前应为各服务建立 systemd 单元并检查健康状态，不能只启动 `service-front`。
5. 业主 H5 源码在 `wuye-xcx2/WechatOwnerService-v0.8`。该项目没有独立 npm H5 构建脚本，需在 HBuilderX 中选择“发行 → 网站 PC-Web 或手机 H5”，再把 `unpackage/dist/build/web/`（较旧版本可能是 `h5/`）内的文件复制到 `/srv/wuye/h5`，确认该目录直接包含 `index.html`。H5 的 `conf/config.js` 默认 `wAppId` 为空；正式入口需传入绑定商户号的公众号 AppID，或在构建前填同一 AppID。`baseUrl='/'` 应保持同域请求。
6. 将 `deploy/openresty-wuye.conf.example` 的证书路径替换为服务器上的实际路径，并作为 OpenResty/Nginx 的站点配置加载。先检查语法，再重载服务。DNS 应指向服务器，`https://luci-ona.site` 及两个支付通知地址须能从公网访问。

`deploy/start-front.sh` 仅用于宿主机直接运行 Java 进程。若使用 1Panel 的容器化 Java 运行环境，请按 `deploy/1PANEL.md` 配置项目目录、容器内启动命令、环境变量和端口。其他微服务各有自己的 JAR；仅启动 `service-front` 不足以运行完整支付链路。

`/app/`、`/callComponent/` 由 OpenResty 转发到本机 `127.0.0.1:8012`。微信通知地址为 `https://luci-ona.site/app/payment/notify` 和 `https://luci-ona.site/app/payment/oweFeeNotify`，均不含查询参数。公众号网页授权域名填 `luci-ona.site`，商户平台 JSAPI 支付授权目录需覆盖实际付款页面。

## 测试边界

本地已通过 H5 支付桥接和状态轮询测试；当前机器没有 Java/Maven 和 HBuilderX，故本包内没有已验证的 JAR 或 H5 静态构建产物。服务器部署后先检查 OAuth 登录、业务接口、反向代理和通知可达性。真实支付测试必须使用已绑定普通商户号的公众号和真实商户配置。

**当前代码不能直接用于正式收款。** 支付订单和通知幂等状态仍在 Redis，持久化流水、数据库级幂等和微信查单补偿尚未完成。具体风险与联调顺序见 `docs/WECHAT-PAYMENT-READINESS.md`。
