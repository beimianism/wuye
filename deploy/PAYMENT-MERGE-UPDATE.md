# 支付模块合并与远端更新

目标仓库是 `https://github.com/haixiang718/wuye`。支付改动放在 `feat/payment-deploy-20261022` 分支，基于原项目的 `feat/wechat-test-integration`，保留原项目公众号测试、手动账单通知等提交。后续更新原项目时，先把上游提交合进这个分支，再构建部署；不要把旧模块目录整体覆盖回上游。

## 目录和接口

- `wuye-b/MicroCommunity-v0.8`：后端。`service-front` 处理公众号授权、统一下单、两条支付通知与支付状态；`service-api`、`service-fee`、`service-order`、`service-store`、`service-user`、`service-community` 完成费用、订单、商户配置、业主和房屋调用。
- `wuye-xcx2/WechatOwnerService-v0.8`：业主 H5 页面。`scripts/owner-h5.cjs` 构建 `index.html`、旧登录跳转用的 `user.html` 和默认关闭支付的公开配置。
- `deploy/compose-services.yml`：服务器现用的 Java 服务编排；`/srv/wuye/runtime/config` 是服务器私有配置，不纳入 Git。
- 公开入口为 `https://luci-ona.site/`；`/app/` 经 OpenResty 转发到前台服务。普通缴费通知 `/app/payment/notify`，欠费通知 `/app/payment/oweFeeNotify`，前端以 `/app/payment/status?orderId=...` 查询业务确认结果。

## 原项目后续合并

在有该功能分支的工作副本中执行：

```bash
git fetch origin
git switch feat/payment-deploy-20261022
git merge origin/feat/wechat-test-integration
```

冲突时保留原项目后续的业务改动，同时核对 `WechatPayAdapt` 普通商户校验、`OwnerAppLoginSMOImpl` OAuth 错误处理和支付通知的签名、金额、订单校验。合并后运行下面的构建与测试，再部署。若功能分支尚未推送到 GitHub，可从本机工作副本 `/home/x1908/workwork/wuye-upstream-20261022` 获取。

## 快速部署步骤

1. 备份服务器当前 JAR、站点文件及私有配置。仅把源码同步到 `/srv/wuye/source`；排除 `.git/`、`node_modules/`、`target/`、`unpackage/`、`.runtime/`、`.env.*`。不要用源码同步覆盖 `/srv/wuye/runtime/config`。
2. 在仓库根目录执行 `npm --prefix wuye-xcx2/WechatOwnerService-v0.8 ci --legacy-peer-deps` 和 `npm run build:h5`。将 `wuye-xcx2/WechatOwnerService-v0.8/unpackage/dist/build/h5/` 同步到站点 `/opt/1panel/www/sites/wuye-h5/index/`，确认 `index.html`、`user.html` 和 `/wechat-test/config.js` 可由 HTTPS 获取。
3. 在服务器的 `maven:3.9.9-eclipse-temurin-8` 容器里挂载后端目录及 `/srv/wuye/runtime/m2`，运行 `mvn -DskipTests package`。需要执行指定 Java 测试时，用 `mvn -DskipTests=false -Dtest=WechatPayUnavailableTest,OwnerWechatOAuthTest -Dsurefire.failIfNoSpecifiedTests=false package`；本项目 `service-front` 的依赖解包在 `package` 阶段，单独运行 `test` 会失败。
4. 先确认 MySQL、Redis、Kafka、ZooKeeper、Eureka 正常，再以 `/srv/wuye/runtime/compose-services.yml` 启动 `api fee store user community`，重启 `order front`。通过 Eureka 检查这七个服务均已注册，再检查公网 HTTPS 路由、支付通知 `FAIL` 拒绝行为和登录保护。服务器内存为 3.6 GiB，当前额外的 1 GiB 交换文件位于 `/srv/wuye/runtime/payment.swap` 并写入 `/etc/fstab`；增加服务前必须检查资源余量。
5. 商户信息只在服务器私有配置和商户平台管理。启用支付前，核对公众号 AppID 与商户号绑定、APIv2 密钥、JSAPI 授权目录、公众号网页授权域名、通知 URL、数据库 `smallWeChat` 记录和支付适配器配置。H5 的公开 `paymentEnabled` 只能在后端具备真实商户条件、持久化幂等和真实联调后打开。

回退时，先停止新启动的业务服务，恢复 `/srv/wuye/backups/payment-20261022-running-jars.tar.gz` 中的旧前台和订单 JAR，以及 `/srv/wuye/backups/payment-20261022-h5-before/` 中的旧站点文件，再重启原有的 `order front`。源码改动的备份在 `/srv/wuye/backups/payment-20261022-source/`。回退不清理或修改业务数据。

## 2026-10-22 部署记录

- 全量 Maven `package` 成功；支付未配置拒绝测试 1 项、公众号 OAuth 测试 9 项通过。H5 支付测试、本地业主测试和配置测试已通过。
- 业主 H5 已部署；`/`、`/user.html` 均返回 200。七个支付链路服务在 Eureka 注册；未登录支付状态查询返回 401；普通缴费和欠费通知对无效 XML 均返回微信格式的 `FAIL`。
- 服务器尚无正式商户号和 APIv2 密钥，H5 `paymentEnabled:false`，没有执行真实 JSAPI 扣款。订单与通知幂等状态仍依赖 Redis，持久流水、数据库唯一约束和微信查单补偿尚未实现。现阶段是支付代码与基础链路部署，不能作为正式收款验收。
