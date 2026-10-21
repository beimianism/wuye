# 本地公众号测试号：后端接入说明

此说明对应 `feat/wechat-test-integration`。使用公众号测试号、现有业主 H5、本地服务及独立数据库；不配置小程序或真实支付。

## 配置与数据库

管理后台新增或修改公众号时，类型为 `1100`，填写名称、微信 AppID、AppSecret、小区。`mchId` 与 `payPassword` 可以同时留空；只填一个会被拒绝。小程序类型 `1000` 仍须填写完整支付配置。更新以数据库中的类型为准，不能通过提交另一个类型绕过验证。

`small_wechat` 和 `buiness_small_wechat` 的 `pay_password`、`mch_id` 均为 NOT NULL（已核对恢复的本地 MySQL 元数据和仓库建表 SQL）。未开通支付存为两个空字符串，无须改表。清空已有支付配置时，实例更新 SQL 也会写入两个空字符串。微信支付适配器在任何缓存或外部下单请求之前，明确拒绝未配置的支付。

公众号可以来自管理后台记录；请求头 `w-app-id` 是微信的 `wx...` AppID。指定了此头却未找到公众号配置时拒绝授权，不回退到其他账号。未指定时使用外置 Spring 配置：

```properties
java110.auth.wechat.wechatAppId=<测试号AppID>
java110.auth.wechat.wechatAppSecret=<测试号AppSecret>
```

密钥只存于 Git 忽略的本地配置。历史通用请求及 SQL 调试日志包含报文/参数；仅设父包 INFO 不足以覆盖原 XML 中的子 logger DEBUG。本地启动器已生成独立 `logback-local.xml`，同时通过 JVM 的 `logback.configurationFile` 与 Spring 的 `logging.config` 加载，关闭旧 API/Druid 等调试日志，并清理首次导入时产生的本地敏感记录。公众号 OAuth 和服务器校验中的显式密钥、access_token 日志已移除；外部 OAuth 请求异常也不返回含密钥的 URL。

内部应用 ID `992020061452450002` 表示业主公众号客户端，来自 `AppDto.WECHAT_OWNER_APP_ID`；它不是微信 AppID，也不应替换成 `wx...`。小程序内部应用 ID 为 `992019111758490006`。

## 公网路径与微信平台设置

微信平台填写短回调 URL：

```text
https://<临时域名>/wechat-test/callback
```

入口对 GET 使用本地 Token 校验 SHA1 签名并直接返回明文 echostr，减少后台调用延迟；POST 转发至本地配置中的原后台路径，内部应用 ID 和 wId 不允许由外部查询参数覆盖。原后台路径为：

```text
https://<临时域名>/app/wechat/gateway?java110AppId=992020061452450002&wId=<URL编码后的wId>
```

`wId` 可在本机管理通道调用 `/app/getWId?appId=<微信AppID>` 获得；不要将这个准备接口加入公网白名单。`wId` 为旧系统的加密标识，可能包含 `+`、`/`、`=`，必须作为查询值编码。校验 Token 使用此公众号的属性 `33001`（`SmallWechatAttrDto.SPEC_CD_TOKEN`）；新建默认值为 `java110`，应通过本地配置操作改成测试配置中的 Token，并与微信平台保持一致。找不到属性时旧系统会退回全局 WECHAT/TOKEN 映射。

网页授权域名填写临时 HTTPS 域名的主机名，实际回调路径为 `/app/loginOwnerWechatAuth`。H5 和回调必须使用同一个公网来源。临时域名变化后，更新本地入口配置和微信平台设置。

## OAuth 与业主绑定协议

1. H5 请求 `GET /app/refreshToken`，查询参数为绝对 `redirectUrl`、同来源的 `errorUrl`（允许相对路径）、`loginFlag=0` 或 `1`；请求头为 `app-id: 992020061452450002` 和可选 `w-app-id: wx...`。响应 `data.openUrl` 指向微信授权页。
2. 服务端保存原始微信账号、内部应用和 loginFlag，生成 300 秒随机 state。回调必须携带匹配的 state/urlCode，且只能消费一次；回调参数中的 wId/loginFlag 不能覆盖缓存。微信返回错误时跳转原 errorUrl，不继续请求用户资料。
3. `loginFlag=1` 或尚未绑定业主时，服务端返回一次性 `code`，OpenID 保留在 Redis；页面不能自行提交可信 OpenID。`POST /app/loginOwner` 的 `{username,password,code}` 在账号验证通过后消费 code，沿用现有 `REFRESH_APP_USER_BINDING_OWNER_OPEN_ID` 绑定逻辑，公众号类型为 `WECHAT`。
4. `loginFlag=0` 且 OpenID 已绑定公众号业主时，重定向只带 `authTicket`。H5 请求既有 `POST /app/loginOwnerByKey`，报文为 `{authTicket}`。该票据有效 300 秒、仅用一次，并校验内部应用。旧客户端 `{key}` 登录协议继续保留；永久用户 key 不再写入 OAuth 重定向 URL。

uni-app 使用 `#/pages/...` 路由，所以 `code`/`authTicket` 加入 fragment 内的页面查询参数，例如 `/#/pages/my/myHouse?wAppId=wx...&authTicket=...`。返回前移除旧的 key/code/authTicket 参数。业务请求继续使用现有登录 token；浏览器通过入口转发 `token` 请求头为后端 `_java110_token_` Cookie，保持访问会话与业务身份各自校验。

## 已执行的局部验证

- Java 8 手动编译修改的 API、front、utils 类成功。
- JUnit：`SmallWeChatConfigurationTest`、`OwnerWechatOAuthTest`、`WechatPayUnavailableTest`、`SmallWeChatMapperTest`、`SmallWeChatListContractTest` 共 20 项通过，覆盖无支付/部分/完整配置、类型伪造、空字符串更新 SQL、state、回放、fragment 路由、微信错误、上游异常、已绑定业主票据登录及单次消费、列表响应类型保留及 Web 凭据清除。
- Web：`node --test wuye-f/MicroCommunityWeb-v0.8/tests/wechat-config.test.cjs`，8 项通过，包含管理页传入数字类型的情况。

Java 局部验证使用 `.tools/zulu8.96.0.205-ca-jdk8.0.504-win_x64`、`.runtime/query-rooms-test/lib`，排除冲突的 `log4j-slf4j-impl`，并使用 Maven 缓存中的 JUnit 4.13.1/hamcrest。测试的 Redis、内部业务 HTTP 和微信 HTTP 都是内存替身，不请求真实微信，不生成订单或发布菜单。完整打包、运行数据库保存/更新和公网验证需由集成步骤另行记录。

局部测试不能替代平台和手机验证。2026-10-21 集成补充：用户在手机微信授权后登录测试业主账号，确认房屋及测试账单可见；只读查询确认该测试业主 WECHAT 绑定有非空 OpenID。旧隧道的平台 URL 校验曾通过，新隧道仍受提供方确认页影响而提交失败；真实支付及会话失效后自动登录尚未验收。

同日针对单个测试业主执行一次真实账单通知：先通过原出账业务生成 TEST101 的 0.01 元账单，再限定对象调用原推送业务，微信返回 `errcode=0` 与消息 ID，实际账单明细状态更新为 `3000`（已通知未支付）。修正按 `ownerId` 查询和匹配，成功响应必须包含 `errcode=0` 和非空 `msgid`；错误响应、无 OpenID、无匹配对象不再误标记已发送，删除含完整通知数据的 INFO 日志。10 项回归通过，任务服务及依赖 8 模块打包成功并重启。调用方仍需处理部分收件人失败与网络超时的不确定结果，不承诺严格只发送一次。

API 受理与手机收件是不同证据；用户随后确认新网页授权域名保存成功，并已收到通知、点击后能查看测试费用，本轮手机收件及跳转查询通过。入站消息回调校验失败不阻止本轮主动调用微信模板发送 API；这也不能反向证明入站回调已接通。验证范围、页面限制和本机回执见 [WECHAT-TEST.md](WECHAT-TEST.md)。

本次 10 项通知测试通过 JUnitCore 直接编译/执行，未调用微信。既有父 POM 将 Surefire 默认跳过，且单独执行 reactor 的 `test` 生命周期会因 dependency:unpack 尚无已打包依赖报 MDEP-98；不能把该命令视为自动测试已通过。生产代码的 `package -DskipTests` 8 模块打包与直接 JUnit 的结果分别记录；尚未调整项目整体测试生命周期。
