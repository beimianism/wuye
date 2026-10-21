# 公众号测试号联调实施计划

**Goal:** 在本机准备可用的业主 H5 和公众号测试号接入环境，完成可执行的本地验证，并把真实微信联调推进到外部参数允许的阶段。

**Architecture:** 复用业主 uni-app、现有微信登录和账单后端，补充 H5 构建及专用受限入口。运行配置及工具放在忽略目录。开发在当前已隔离的功能分支上进行，不修改原始快照。

**Tech Stack:** Vue 2 / uni-app H5、Node、Java 8、Python、微信测试号、临时 HTTPS 隧道。

**2026-10-21 执行记录：** 已完成代码、构建和本地真实业务查询，测试号凭据已通过微信 token 接口验证。旧隧道 URL/Token 曾提交成功，切换新入口后消息回调校验仍失败；独立网页授权域名已保存，用户手机微信授权、测试账号登录及房屋/0.01 元账单查询通过，后台确认 WECHAT OpenID 绑定。没有进行真实通知或支付。详细结果见 `docs/WECHAT-TEST.md`、`docs/OWNER-H5.md`、`docs/WECHAT-BACKEND.md` 和 `docs/PROJECT-STATUS.md`。

## Task 1: 恢复环境并记录事实

- [x] 检查独立 MySQL、Java 服务和日志，不复用其他 MySQL 数据；通过启动脚本恢复。
- [x] 复验浏览器登录与保留查询，记录数据库和资源占用。

## Task 2: H5 构建与保留路径

- [x] 检查现有 package、manifest、平台条件编译和登录方式；为 H5 配置最小可重复构建工具链。
- [x] 添加必要的行为回归测试，先重现 H5 故障再修复。
- [x] 实际构建、提供本地运行命令，验证入口、登录、房屋及账单页面，支付未配置时不展示可用收款状态。
- [x] 文件范围：`wuye-xcx2/WechatOwnerService-v0.8`；构建脚本及对应说明。不得重新注册裁剪页面。

## Task 3: 公众号基础配置与授权

- [x] 明确区分未开通支付与已配置支付：公众号可仅使用 AppID、AppSecret 和类型等必要资料保存、更新，支付参数成对校验。
- [x] 对配置输入做有意义的单元测试，验证缺失、部分和完整支付配置；防止误改小程序路径。
- [x] 检查既有 OAuth 域名、编码、AppID、回调、OpenID 与业主关系，针对实际阻碍做最小修复并记录测试。
- [x] 文件范围：后端公众号配置/授权与 Web 对应表单、测试；不执行真实通知、菜单发布或支付。

## Task 4: 受限入口与本地密钥配置

- [x] 生成忽略的测试号配置模板，读取本地密钥不打印；确认测试号 AppID、回调 Token、URL 和当前小区。
- [x] 为专用联调入口写 HTTP 集成测试，先验证禁止管理和内部路径，再实现允许的 H5/微信路径。
- [x] 使用临时 HTTPS 隧道暴露该入口；验证公网路径和身份限制，记录进程以便停止。
- [x] 提供域名更新、测试号平台保存配置和手机打开步骤；等待必须由用户扫码/填写的平台操作，其他工作继续。

## Task 5: 集成验证和交付

- [x] 两阶段审查：先核对方案范围，再检查实现质量、秘密处理与业务隔离。
- [x] 完成相关 Node、Python、Java 测试及实际 H5/Java 构建；一次完整浏览器检查。
- [x] 微信真实联调按已收到参数验证，不把模拟替代真实授权或支付。
- [x] 更新项目现状和联调说明；提交并同步已授权的 GitHub 仓库，明确已完成与仍待用户操作的事项。

## Pending external verification

- [ ] WeChat test platform callback submission and OAuth domain save.
- [ ] Phone WeChat authorization, owner identity binding and bill query.
- [ ] Explicitly designated notification template and test recipient (no messages sent).
