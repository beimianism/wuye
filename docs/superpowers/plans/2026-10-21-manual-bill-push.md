# 单条账单推送实施计划

**Goal:** 在现有后台欠费清单手动发送一条公众号账单通知。

**Architecture:** 管理页调用登录保护的 POST `/app/fee.pushBill`，API listener 校验身份后调用单条发送服务。服务只从内部接口获取可信账单、收件人和配置，使用 Redis 保存锁及请求/收件人结果。

**Tech Stack:** Java 7/8、Spring/Feign、Redis、FastJSON、Vue 2、Node test、JUnit。

- [ ] 后台测试先行：指定明细、跨小区拒绝、已缴费拒绝、ownerId 匹配、模板/绑定缺失、微信失败、重复请求与并发、部分发送和状态更新失败。
- [ ] 后台实现：`service-api/.../listener/fee/PushBillListener.java` 与 `service-api/.../bmo/fee/impl/BillNotificationService.java`，采用现有 listener 协议及接口，不遍历全小区。
- [ ] 前端测试先行并实现：`billOweManage` HTML/JS 确认、等待、结果展示，已支付禁止；保留当前页，状态筛选3000为已通知。
- [ ] H5 房屋定位：`roomFeeListNew` 尊重通知链接的 roomId；无该房屋不显示另一房屋。
- [ ] 适当 Java、Node 回归，定向打包 API 并重启；不启用自动任务。
- [ ] 浏览器验证真实账单入口与按钮，测试请求不得发出真实微信消息；刷新必要的临时入口及文档，将发送动作留给用户。
- [ ] 独立审查，记录验证证据，提交并同步功能分支。
