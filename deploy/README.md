# Linux 部署与支付模块

原项目合并及当前远端支付链路更新见 [PAYMENT-MERGE-UPDATE.md](PAYMENT-MERGE-UPDATE.md)。

本仓库源码部署在 `/srv/wuye/source`，服务器私有配置在 `/srv/wuye/runtime/config`，业主 H5 站点在 `/opt/1panel/www/sites/wuye-h5/index`。上述路径是当前远端服务器的实际目录。

## 服务器准备

1. 将压缩包和同名 `.sha256` 上传到服务器，在文件所在目录执行 `sha256sum -c 压缩包名.tar.gz.sha256`。然后创建 `/srv/wuye/source`，执行 `tar -xzf 压缩包名.tar.gz -C /srv/wuye/source --strip-components=1`。不要把真实商户密钥写入源码或 H5 构建文件。
2. 准备 Java 8、Maven，以及本项目实际依赖的 MySQL、Redis、Kafka/ZooKeeper。检查并替换各服务 `application-prod.yml` 中的 `prod.*.java110.com`、数据库和中间件地址；仓库自带的生产配置不能直接用于新服务器。
3. 当前服务器在 `/srv/wuye/runtime/config/wechat.env` 按 `deploy/wechat.env.example` 保存公众号和普通商户 APIv2 凭据，文件权限为 `0600`，由 Compose 只读挂载到前台服务。直接使用 `deploy/start-front.sh` 的宿主机模式另用 `/etc/wuye/wechat.env`。公众号测试号密钥只用于 OAuth 测试，不能用于真实 JSAPI 收款。
4. 后端源码在 `wuye-b/MicroCommunity-v0.8`。在 Maven 容器中执行 `mvn -DskipTests package`，再按支付调用顺序使用 `deploy/compose-services.yml` 启动服务；`service-front` 默认端口为 `8012`。上线前检查服务注册和健康状态，不能只启动 `service-front`。
5. 业主 H5 源码在 `wuye-xcx2/WechatOwnerService-v0.8`。安装依赖后运行 `npm run build:h5`，将 `unpackage/dist/build/h5/` 同步到站点目录，确认包含 `index.html`、`user.html` 和默认关闭支付的 `wechat-test/config.js`。正式入口需传入绑定商户号的公众号 AppID；`baseUrl='/'` 保持同域请求。
6. 将 `deploy/openresty-wuye.conf.example` 的证书路径替换为服务器上的实际路径，并作为 OpenResty/Nginx 的站点配置加载。先检查语法，再重载服务。DNS 应指向服务器，`https://luci-ona.site` 及两个支付通知地址须能从公网访问。

`deploy/start-front.sh` 仅用于宿主机直接运行 Java 进程。若使用 1Panel 的容器化 Java 运行环境，请按 `deploy/1PANEL.md` 配置项目目录、容器内启动命令、环境变量和端口。其他微服务各有自己的 JAR；仅启动 `service-front` 不足以运行完整支付链路。

`/app/`、`/callComponent/` 由 OpenResty 转发到本机 `127.0.0.1:8012`。微信通知地址为 `https://luci-ona.site/app/payment/notify` 和 `https://luci-ona.site/app/payment/oweFeeNotify`，均不含查询参数。公众号网页授权域名填 `luci-ona.site`，商户平台 JSAPI 支付授权目录需覆盖实际付款页面。

## 测试边界

2026-10-22 已在服务器构建全量 JAR，并把 H5 静态产物部署到 HTTPS 站点；详情见合并与更新记录。真实支付测试仍必须使用已绑定普通商户号的公众号和真实商户配置。

**当前代码不能直接用于正式收款。** 支付订单和通知幂等状态仍在 Redis，持久化流水、数据库级幂等和微信查单补偿尚未完成。具体风险与联调顺序见 `docs/WECHAT-PAYMENT-READINESS.md`。
