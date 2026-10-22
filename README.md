# 物业系统主项目

本目录是后续开发、微信支付接入和服务器部署的主项目。当前支付主入口为**公众号 H5（普通商户 APIv2 JSAPI）**；小程序保留为次要入口。

| 目录 | 内容 |
| --- | --- |
| `wuye-b/MicroCommunity-v0.8/` | Java 微服务及数据库脚本 |
| `wuye-f/MicroCommunityWeb-v0.8/` | 物业管理 Web |
| `wuye-xcx/PropertyApp-v0.8/` | 员工端 |
| `wuye-xcx2/WechatOwnerService-v0.8/` | 业主小程序及 H5 |
| `scripts/` | 本地启动、迁移和检查脚本 |

本地运行见 [本地开发](docs/LOCAL-DEVELOPMENT.md)。微信支付现状、待处理问题与部署准备见 [微信支付接入与部署准备](docs/WECHAT-PAYMENT-READINESS.md)。
Linux 源码包的目录安排、构建步骤和 OpenResty 示例见 [部署测试说明](deploy/README.md)。
使用 1Panel 时见 [1Panel V2 设置](deploy/1PANEL.md)。
