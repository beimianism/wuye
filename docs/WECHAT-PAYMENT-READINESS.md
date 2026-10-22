# 公众号 H5 微信支付接入与部署准备

目标项目：`haixiang718/wuye` 的 `feat/payment-deploy-20261022` 分支。支付方案已确定为**普通商户 APIv2，公众号内 H5（JSAPI）优先**；小程序共用服务端下单和通知代码，但不是本次上线主入口。微信内 JSAPI 与微信外浏览器的 H5/MWEB 是不同产品；本次不接 MWEB。APIv2 仍有官方接口文档，不能简单视为全面停用：[JSAPI 开发指引](https://pay.weixin.qq.com/doc/v2/merchant/4011935209)。

## 当前实现

1. 业主登录公众号 H5 后，以公众号 AppID 查询关联的 OpenID。缴费页面提交费用对象；服务端生成业务订单并计算应付金额，不再按 DEV 环境压成几分钱。
2. `WechatPayAdapt` 使用 APIv2 统一下单，`trade_type=JSAPI`，校验统一下单应答签名、AppID、商户号，再返回 `appId/timeStamp/nonceStr/package/signType/sign/orderId`。公众号 H5 使用 `WeixinJSBridge.invoke('getBrandWCPayRequest', ...)` 调起支付；支付签名不再误用作 `wx.config` 签名。[JSAPI 调起文档](https://pay.weixin.qq.com/doc/v2/merchant/4011935213)。
3. 微信向无查询参数的公网 HTTPS `notify_url` 发送 XML 通知。服务端禁用 XML 外部实体，验 APIv2 签名，比较 AppID、商户号、OpenID、订单号、交易类型和分单位金额。订单服务原先在 `finally` 中无论成败都返回 200，现已修复；业务确认真正成功后才向微信回 `SUCCESS`。[APIv2 支付通知](https://pay.weixin.qq.com/doc/v2/merchant/4011941607)。
4. 重复通知由订单锁和支付标记处理。H5 桥接层返回 `ok` 后，页面凭登录态轮询 `/app/payment/status?orderId=...`，只有服务端业务确认完成才显示“支付成功”。未确认时保持待确认状态。

## 上线前仍须完成

**当前不能宣称可以真实收款。** 代码和 H5 已部署到公网 HTTPS，Java 编译与定向测试通过，但服务器前台服务环境变量尚未配置正式商户号和 APIv2 密钥，数据库商户记录尚未核验，也未做真实扣款联调。尤其支付订单、待销账明细和已支付标记目前仍存 Redis。Redis 丢数据，或业务服务已成功而前端服务在写支付标记前崩溃，可能造成状态不可恢复或重复销账。上线前需把订单与支付流水、通知幂等状态落库，按唯一 `out_trade_no` 和 `transaction_id` 做数据库级幂等，并用微信查单/对账补偿。欠费销账业务也要以订单号在持久层保证只执行一次。当前代码只提供运行期间的重复通知保护。

另需核验旧配置 `application-prod.yml` 中 `prod.*.java110.com` 服务地址、演示 SQL 中 `HC_ENV=DEV`、其他费用类型（如出租、商品）的旧回调实现。当前重点核验了普通缴费和欠费两个入口，其他入口不能据此视为已完成支付安全改造。

## 商户平台与公众号配置

- 确认商户号为普通商户，开通 JSAPI 支付，将**公众号 AppID** 与商户号绑定。数据库 `smallWeChat` 记录如用于该小区，应填同一公众号 AppID、商户号、APIv2 密钥；否则使用环境变量中的默认商户配置。
- 将项目的 `WECHAT_SERVICE_PAY_SWITCH` 配置为关闭；当前接入只支持普通商户，若开启服务商模式，下单和回调会拒绝处理。
- 将 `WECHAT` 域的 `PAY_ADAPT` 设为 `wechatPayAdapt`，或留空使用默认值。当前普通缴费和欠费各有自己的默认回调适配器，共用的 `PAY_NOTIFY_ADAPT` 应留空，避免把欠费通知误路由到普通缴费适配器。
- 配置 JSAPI 支付授权目录，必须覆盖真实付款页面路径；配置公众号网页授权域名和 H5 业务域名。登录后公众号 OpenID 与统一下单 AppID 必须属于同一公众号。[JSAPI 支付准备](https://pay.weixin.qq.com/doc/v2/merchant/4011935208)。
- H5 应从公众号菜单/授权入口进入，链接携带正确 `wAppId`；`conf/config.js` 的 `wAppId` 目前为空，仅用作部署时设置的默认值。当前预定 H5 域名为 `https://luci-ona.site`。`#ifdef H5` 的 `baseUrl='/'` 要由同域反向代理转发 `/app/` 到 `service-front`。全站启用 HTTPS。
- 微信支付通知 URL 使用 HTTPS、无查询参数，并能由微信公网访问。普通缴费为 `/app/payment/notify`，欠费为 `/app/payment/oweFeeNotify`；两者要经反向代理直达 `service-front`，不可被网页登录拦截。

## 服务端配置

`service-front/src/main/resources/wechatAuth.properties` 已改为从环境变量取值，不提交真实凭据：

| 环境变量 | 用途 |
| --- | --- |
| `WECHAT_APP_ID`、`WECHAT_APP_SECRET` | 默认公众号 AppID、AppSecret；如由数据库配置，则仍须核对一致性 |
| `WECHAT_PAY_MCH_ID`、`WECHAT_PAY_API_V2_KEY` | 普通商户号、APIv2 密钥 |
| `WECHAT_OFFICIAL_ACCOUNT_APP_ID`、`WECHAT_OFFICIAL_ACCOUNT_APP_SECRET` | 原有公众号授权登录配置 |
| `WECHAT_PAY_NOTIFY_URL` | `https://luci-ona.site/app/payment/notify`，正式商户联调时启用 |
| `WECHAT_OWE_FEE_NOTIFY_URL` | `https://luci-ona.site/app/payment/oweFeeNotify`，正式商户联调时启用 |
| `WECHAT_RENTING_NOTIFY_URL`、`WECHAT_GOODS_NOTIFY_URL` | 仅在启用对应业务并完成回调改造后配置 |

公众号 H5 使用单个公众号时，`WECHAT_APP_ID` 与 `WECHAT_OFFICIAL_ACCOUNT_APP_ID` 应为同一个 AppID；两个 AppSecret 变量也应取该公众号的同一密钥。启用数据库中的商户配置时，还需核对数据库记录与这组值一致。

不要把密钥写进前端、Git、日志或部署文档。服务器还需 Java 8、MySQL、Redis、Kafka/ZooKeeper、反向代理及项目各服务的真实连接配置。`scripts/local.py` 是 Windows 本地启动器，不能直接用于 Linux 服务器；生产环境还没有完成服务编排。

## 联调验收顺序

1. 在真实 HTTPS 域名和公众号授权环境登录 H5，核对前端 `wAppId`、登录 OpenID 与下单 `appid`。
2. 创建一笔小额真实业务订单，核对业务应付金额与统一下单 `total_fee`（分），核对返回的 `orderId`。
3. 在微信内调起 JSAPI，分别验证支付成功、取消、支付失败；页面只有查到服务端 `PAID` 才显示成功。
4. 检查通知签名、商户号、AppID、OpenID、订单号和金额；模拟重复通知及业务服务失败，核对回执与幂等行为。
5. 补齐持久流水与微信查单对账后，执行重启/Redis 故障/回调延迟/业务服务超时恢复测试；核对账单、缴费明细与退款流程。

## 本地测试号环境（仅公众号接口）

测试号凭据保存在项目根目录的 `.env.wechat-test.local`，文件权限为 `0600` 且被 Git 忽略。它设置公众号登录所需的 `WECHAT_OFFICIAL_ACCOUNT_APP_ID`、`WECHAT_OFFICIAL_ACCOUNT_APP_SECRET`，以及 `WUYE_H5_ORIGIN=https://luci-ona.site` 作为本地测试目标；不设置商户号或支付密钥。启动本地 `service-front` 的同一个终端先执行 `source .env.wechat-test.local`。H5 页面入口 URL 通过 `wAppId=<测试号 AppID>` 传入公开的 AppID；`conf/config.js` 不固化测试号，避免生产构建误用。

2026-10-22 已在服务器验证 `luci-ona.site` 的 HTTPS 站点和应用路由；用户已确认该域名完成备案。公众号测试号后台的网页授权域名填 `luci-ona.site`（不带协议和路径）；正式公众号仍需独立配置网页授权域名。正式支付商户平台的 JSAPI 授权目录按当前 H5 单页应用可先设为 `https://luci-ona.site/`，再用真实付款页面验证目录匹配。支付通知地址已由公网反向代理开放。

遇到微信 `redirect_uri` 域名不一致（10003）时，进入**该测试号 AppID 对应**的测试平台「网页授权获取用户基本信息」，将授权回调页面域名改为 `luci-ona.site` 并保存。此项与「JS 接口安全域名」、消息接口 URL/Token、商户平台 JSAPI 支付授权目录是不同配置；旧的 Pinggy 域名不适用于当前站点。服务端已验证生成的 OAuth `redirect_uri` 为 `https://luci-ona.site/app/loginOwnerWechatAuth?...`，且 OAuth URL 使用测试号 AppID。若平台已保存正确域名但仍报 10003，应从 `https://luci-ona.site/` 重新打开入口，并核对当前页面 URL 与 OAuth URL 的 `appid`、`redirect_uri`，避免沿用旧临时入口或缓存的账号链接。[微信支付官方 10003 排查](https://pay.weixin.qq.com/doc/v2/merchant/4011935211)。

测试平台「接口配置信息 → URL」使用 `https://luci-ona.site/app/wechat/testCallback`，Token 与服务器私有配置 `WECHAT_OFFICIAL_ACCOUNT_CALLBACK_TOKEN` 相同；此项用于公众号消息回调，与网页授权域名分别设置。固定服务器的旧 `/wechat-test/callback` 不存在。

已运行 H5 桥接与状态轮询测试、业主端本地功能测试、Python 配置测试；服务器 Java 打包及支付未配置拒绝、公众号 OAuth 定向测试通过。此前测试号已完成一次手机微信授权登录与账单查看；本次重新部署后仍需真机回归，不等于完成正式商户支付联调。公众号接口测试号不能替代已认证并绑定商户号的正式公众号进行真实 JSAPI 支付；`wechatpay-dev-cli` 主要面向 APIv3 查单排障，也不能直接代替本项目的 APIv2 统一下单联调。[APIv2 JSAPI 接入准备](https://pay.wechatpay.cn/doc/v2/merchant/4011935208)、[微信支付开发 CLI](https://pay.wechatpay.cn/doc/v3/merchant/4019638116)。
