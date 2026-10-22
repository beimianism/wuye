#!/usr/bin/env python3
"""Generate private, external configuration for the single-host Linux deployment."""

import argparse
import getpass
import json
import os
from pathlib import Path
import re


SERVICES = {
    "order": 8001,
    "user": 8002,
    "acct": 8003,
    "common": 8005,
    "store": 8006,
    "report": 8007,
    "api": 8008,
    "community": 8009,
    "fee": 8010,
    "front": 8012,
    "job": 8013,
    "goods": 8014,
}


def jdbc(database):
    return (
        "jdbc:mysql://127.0.0.1:3306/" + database
        + "?useUnicode=true&characterEncoding=utf-8&serverTimezone=Asia/Shanghai"
        + "&useSSL=false&allowPublicKeyRetrieval=true"
    )


def write_private(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(value)
    os.chmod(path, 0o600)


def prepare_datasource(source, destination, db_user, db_password, main_db):
    data = source.read_text(encoding="utf-8")
    data, urls = re.subn(
        r"jdbc:mysql://[^\s]+/(hc_community|TT)\?[^\s]+",
        lambda match: jdbc("hc_community" if match.group(1) == "hc_community" else main_db),
        data,
    )
    if not urls:
        raise ValueError("No JDBC URL in " + str(source))
    data = re.sub(
        r"(?m)^(\s*)username:.*$",
        lambda match: match.group(1) + "username: " + json.dumps(db_user),
        data,
    )
    data = re.sub(
        r"(?m)^(\s*)password:.*$",
        lambda match: match.group(1) + "password: " + json.dumps(db_password),
        data,
    )
    data = re.sub(r"(?m)^(\s*)(minIdle|initialSize):.*$", r"\1\2: 1", data)
    write_private(destination, data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("/srv/wuye/source/wuye-b/MicroCommunity-v0.8"),
    )
    parser.add_argument("--output", type=Path, default=Path("/srv/wuye/runtime/config"))
    args = parser.parse_args()

    db_user = input("MySQL username (press Enter for wuye_app): ").strip() or "wuye_app"
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,31}", db_user):
        raise ValueError("Invalid MySQL username. Use wuye_app, or press Enter for it.")
    db_password = getpass.getpass("MySQL application password: ")
    if not db_password:
        raise ValueError("MySQL application password cannot be empty")
    redis_password = getpass.getpass("Redis password (Enter if none): ")
    main_db = input("Main database name [tt]: ").strip() or "tt"
    if main_db not in {"tt", "TT"}:
        raise ValueError("Main database must be tt or TT")

    args.output.mkdir(parents=True, exist_ok=True)
    os.chmod(args.output, 0o700)
    for name, port in SERVICES.items():
        service_source = args.source / ("service-" + name) / "src/main/resources"
        properties = {
            "server.address": "127.0.0.1",
            "server.port": port,
            "eureka.client.serviceUrl.defaultZone": "http://127.0.0.1:8761/eureka/",
            "eureka.instance.hostname": "127.0.0.1",
            "eureka.instance.ip-address": "127.0.0.1",
            "eureka.instance.preferIpAddress": True,
            "eureka.instance.instanceId": "127.0.0.1:" + str(port),
            "spring.redis.host": "127.0.0.1",
            "spring.redis.port": 6379,
            "spring.redis.password": redis_password,
            "jedis.pool.host": "127.0.0.1",
            "jedis.pool.port": 6379,
            "jedis.pool.password": redis_password,
            "jedis.pool.config.maxTotal": 20,
            "jedis.pool.config.maxIdle": 5,
            "kafka.consumer.servers": "127.0.0.1:9092",
            "kafka.producer.servers": "127.0.0.1:9092",
            "kafka.consumer.zookeeper.connect": "127.0.0.1:2181",
            "kafka.producer.zookeeper.connect": "127.0.0.1:2181",
            "kafka.consumer.concurrency": 1,
            "java110.code.zookeeper.url": "127.0.0.1",
            "java110.code.zookeeper.port": 2181,
            "server.tomcat.max-threads": 30,
            "server.tomcat.min-spare-threads": 2,
            "logging.file": "/tmp/wuye-" + name + ".log",
            "spring.datasource.url": jdbc(main_db),
            "spring.datasource.username": db_user,
            "spring.datasource.password": db_password,
        }
        datasource = service_source / "dataSource.yml"
        if datasource.exists():
            output = args.output / (name + "-datasource.yml")
            prepare_datasource(datasource, output, db_user, db_password, main_db)
            properties["java110.datasource.config"] = "file:/etc/wuye/" + output.name
        write_private(args.output / (name + ".json"), json.dumps(properties, ensure_ascii=False))
    wechat_env = args.output / "wechat.env"
    if not wechat_env.exists():
        write_private(wechat_env, "# Add official-account and merchant variables before payment testing.\n")
    print("Generated external configuration in " + str(args.output))
    print("Keep this directory private; it contains database and Redis credentials.")


if __name__ == "__main__":
    main()
