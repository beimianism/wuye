# 公众号账单链路联调记录（2026-10-22）

测试号 AppID：`wxced68de202cbd392`。测试模板 ID：`j2c-PmwOsgrs4pM3YBVXTe-LO9K_chyAsUDnUyrXkTo`，标题为“联调测试账单通知”，字段为 `first`、`keyword1`、`keyword2`、`keyword3`、`remark`，与 `BillNotificationService.message()` 使用的字段一致。

## 已验证

1. 测试号有一名已关注用户。此前发送的模拟账单客服文字消息由用户确认收到。
2. 新建模板在该测试号的模板列表中可查；向唯一关注者发送 `TEST101 / 0.01 元` 模拟账单模板消息，微信接口返回 `errcode=0` 和消息 ID。模板消息的手机端到达状态仍需用户单独确认。
3. 对 `https://luci-ona.site/app/wechat/testCallback` 发送有效签名的模拟回调：GET 返回正确的 `echostr`，POST 返回 HTTP 200 和后台生成的 XML 消息。POST 使用虚构未绑定发送者和普通文字内容，不触发支付。
4. `python3 scripts/tests/simulate_income_bill.py` 在内存数据库中执行项目的 `api.getListPayFee` 原始列表、计数、合计 SQL。模拟一条 `TEST101` 已收 `0.01` 元记录、一条未付账单、另一物业的已收记录；后台报表查询仅返回目标已收记录，合计 `0.01` 元。

## 真实后台推送所需配置

上述测试分别验证微信出站模板、公众号入站回调和本地收入报表。服务器未创建真实欠费、支付或收入记录，也没有通过管理端 `fee.pushBill` 推送，因为当前测试数据中没有 `TEST101` 房屋、业主公众号绑定和账单；公众号账号及模板 ID 尚未写入项目数据库。服务器保留最小测试服务，不能据此认定正式支付回调、账单状态流转和收据任务已运行。

在原项目进行完整联调时，需要给目标小区配置唯一公众号账号、欠费模板属性（`SmallWechatAttrDto.SPEC_CD_OWE_FEE_TEMPLATE`）、已审核的业主 OpenID 绑定和未支付账单，再由已登录物业员工在管理端选择单条账单推送。随后使用真实商户沙箱或受控支付环境验证支付通知与收据任务；不要将本次模拟数据作为真实营收。

本记录不包含 AppSecret、回调 Token、OpenID 或访问令牌。
