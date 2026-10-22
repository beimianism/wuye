# 单机 Linux / 1Panel 部署

适用于源码位于 `/srv/wuye/source/wuye-b/MicroCommunity-v0.8`、1Panel 的 MySQL/Redis 只映射到宿主机 `127.0.0.1`、OpenResty 使用 host 网络的服务器。

## 1. 已有中间件

先导入 `hc_community` 与 `tt`，再启动 `compose-middleware.yml` 的 ZooKeeper/Kafka，以及独立的 Eureka。运行环境的 Java 版本为 8。`compose-services.yml` 中的 Java 服务使用 host 网络，只监听 `127.0.0.1`。

## 2. 数据库账号

建立 `wuye_app` 账号，并授予 `hc_community`、`tt` 两个库的权限。账号密码只保存在服务器，勿粘贴到聊天或提交到 Git。若密码已暴露，先用 `ALTER USER 'wuye_app'@'%' IDENTIFIED BY '新密码';` 轮换，再继续。

## 3. 兼容迁移

本项目 Java 0.8 服务搭配 0.6 SQL 导出文件，启动前执行 `compat-migration.sql` 增加缺失列和路由。该文件可重复执行。建议先备份两个库，再在 MySQL 客户端 `SOURCE /srv/wuye/runtime/compat-migration.sql;`，检查无 `ERROR`。

## 4. 生成外部配置

将 `prepare-linux-config.py` 上传到服务器 `/srv/wuye/runtime/`，然后运行：

```bash
python3 /srv/wuye/runtime/prepare-linux-config.py
```

按提示输入数据库应用账号、**轮换后的**密码、Redis 密码（无密码则直接回车）、主库实际名称（当前为 `tt`）。脚本生成 `/srv/wuye/runtime/config`，目录权限 `0700`、配置文件权限 `0600`。它会为各服务生成独立 JSON 和 ShardingSphere `dataSource.yml`，不修改或重新编译 JAR。

## 5. 启动业务服务

将 `compose-services.yml` 上传到 `/srv/wuye/runtime/`，先验证编排文件：

```bash
docker compose -f /srv/wuye/runtime/compose-services.yml config --services
```

然后分批启动并看日志：

```bash
docker compose -f /srv/wuye/runtime/compose-services.yml up -d order user acct common store report api community fee
docker compose -f /srv/wuye/runtime/compose-services.yml up -d front job goods
docker ps --format 'table {{.Names}}\t{{.Status}}'
docker logs --tail 100 wuye-front-smoke
```

启动 `front` 之前，在 `/srv/wuye/runtime/config/wechat.env` 配置公众号环境变量；测试号可用于 OAuth，但真实支付需要正式商户配置。文件不应进入源码包或聊天记录。

```bash
curl -I http://127.0.0.1:8761/
curl -I http://127.0.0.1:8012/
```

OpenResty 已有 `/app/`、`/callComponent/` 两条规则时，代理到 `http://127.0.0.1:8012`。检查 HTTPS H5 页面、微信网页授权、下单和回调。当前支付流水和幂等状态仍依赖 Redis，完成数据库持久化与查单补偿前不可正式收款。
