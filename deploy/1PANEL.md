# 1Panel V2 部署设置

1Panel 的 OpenResty 和 Java 运行环境分别管理网站与容器。项目源码包上传到服务器 `/srv/wuye` 后，先按本目录 `README.md` 校验、解压及构建；源码包没有 JAR，也没有编译后的 H5 页面。

## 网站

1. “应用商店 → OpenResty”安装或检查运行状态，HTTP/HTTPS 端口使用 80/443。
2. “网站 → 创建网站 → 静态网站”：主域名 `luci-ona.site`，代号可填 `wuye-h5`，默认文档 `index.html`。创建后通过“网站 → 配置 → 网站目录”查看**实际网站根目录**，把 HBuilderX 发行的 H5 文件上传到该目录，使其直接包含 `index.html`。不要假设 1Panel 自动把 `/srv/wuye/h5` 挂载进 OpenResty。
3. 在“证书”申请或导入该域名的证书；然后在“网站 → 配置 → HTTPS”选择证书并开启 HTTP 自动跳转 HTTPS。域名 DNS 要先指向服务器，防火墙及云安全组需放行 80/443。
4. 在同一网站的“配置 → 反向代理”中，分别添加 `/app/` 和 `/callComponent/` 两条路径规则，目标为**从 OpenResty 可访问的** Java 接口地址 `http://127.0.0.1:8012`。必须保留原始 URI，不能删除 `/app/` 前缀。如果运行环境把 8012 仅映射到其他地址，则以该映射地址为准；先在 OpenResty 容器终端测试目标地址的连通性。
5. 若面板的代理规则不能按原样保留路径，可在“网站 → 配置 → 配置文件”中编辑该站点已有的 `server` 块，加入以下 `location`，不要再粘贴一份完整 `server` 块：

```nginx
location ^~ /app/ {
    proxy_pass http://127.0.0.1:8012;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
location ^~ /callComponent/ {
    proxy_pass http://127.0.0.1:8012;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

代理地址末尾不加 `/`，以保留 `/app/payment/notify` 等完整路径。若站点已有同名 `location`，应编辑原块，避免重复定义。微信普通缴费与欠费回调分别是 `https://luci-ona.site/app/payment/notify`、`https://luci-ona.site/app/payment/oweFeeNotify`。

## Java 运行环境

1. 先在服务器构建 `service-front/target/service-front.jar`，并替换所有服务 `application-prod.yml` 里的旧连接地址。项目不止一个 Java 服务；Eureka、订单、费用、社区等依赖服务及 MySQL、Redis、Kafka/ZooKeeper 也要运行。
2. “运行环境 → Java → 创建运行环境”选择 **Java 1.8**。以前端接口服务为例：名称 `wuye-front`；项目目录选择 `service-front/target` 的**宿主机绝对路径**；启动命令用 `java -Dfile.encoding=UTF-8 -jar service-front.jar --spring.profiles.active=prod`；容器名称 `wuye-front`。容器内应用端口为 `8012`，在运行环境的端口设置中将它映射到宿主机；无需对公网开放。
3. 通过 1Panel 的运行环境“环境变量”填写 `deploy/wechat.env.example` 所列变量，值只在服务器面板内填写。不要在容器内使用宿主机 `/etc/wuye/wechat.env` 路径，除非已显式挂载。Java 容器必须能访问这些变量及全部后端服务地址。
4. 启动后查看运行环境日志并从 OpenResty 所在环境检查 `8012` 连通性。若 OpenResty 或 Java 的网络模式与以上不同，应以实际端口映射调整代理目标；容器内不要把 Java 绑定到 `127.0.0.1`。

当前版本只能做部署与联调测试，真实收款前仍须完成持久化支付流水、数据库级幂等和微信查单补偿。详情见 `docs/WECHAT-PAYMENT-READINESS.md`。
