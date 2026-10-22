#!/usr/bin/env python3
"""Build repeatable 0.6-dump compatibility SQL for the 0.8 services."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def literal(value):
    return "CONVERT(0x" + str(value).encode("utf-8").hex() + " USING utf8mb4)"


def main():
    lines = [
        "-- Compatibility changes used by scripts/local.py migrate().",
        "-- Safe to source more than once; import the base SQL first.",
        "",
    ]
    for change in json.loads((ROOT / "scripts/local-schema.json").read_text(encoding="utf-8")):
        database = "tt" if change["database"] == "TT" else change["database"]
        table = change["table"]
        column = change["column"]
        statement = (
            "ALTER TABLE `" + database + "`.`" + table + "` ADD COLUMN `" + column + "` "
            + change["definition"]
        )
        lines.extend([
            "SET @wuye_sql = (SELECT IF(COUNT(*) = 0, " + literal(statement)
            + ", 'SELECT 1') FROM information_schema.columns WHERE table_schema="
            + literal(database) + " AND table_name=" + literal(table)
            + " AND column_name=" + literal(column) + ");",
            "PREPARE wuye_stmt FROM @wuye_sql;",
            "EXECUTE wuye_stmt;",
            "DEALLOCATE PREPARE wuye_stmt;",
            "",
        ])

    for route in json.loads((ROOT / "scripts/local-routes.json").read_text(encoding="utf-8")):
        code, service_id = route["code"], route["id"]
        instance = route.get("instance", "T")
        values = [
            literal(service_id), literal(code), literal("0.8 compatibility route"),
            literal("API"), literal(""), literal(instance),
            literal(route["url"]), literal(route["method"]),
        ]
        lines.append(
            "INSERT INTO `tt`.`c_service`"
            "(service_id,service_code,name,business_type_cd,messageQueueName,is_instance,url,method)"
            " SELECT " + ",".join(values) + " WHERE NOT EXISTS"
            "(SELECT 1 FROM `tt`.`c_service` WHERE service_code=" + literal(code) + ");"
        )
        lines.append(
            "UPDATE `tt`.`c_service` SET business_type_cd='API',messageQueueName=''"
            " WHERE service_id=" + literal(service_id) + ";"
        )
        for app in route["apps"]:
            lines.append(
                "INSERT INTO `tt`.`c_route`"
                "(app_id,service_id,order_type_cd,invoke_limit_times,invoke_model,status_cd)"
                " SELECT " + literal(app) + ",s.service_id,'Q',1000,'S','0'"
                " FROM `tt`.`c_service` s WHERE s.service_code=" + literal(code)
                + " AND NOT EXISTS(SELECT 1 FROM `tt`.`c_route` r WHERE r.app_id="
                + literal(app) + " AND r.service_id=s.service_id AND r.status_cd='0');"
            )
        lines.append("")

    query = json.loads((ROOT / "scripts/local-payments-query.json").read_text(encoding="utf-8"))
    values = [
        literal(query["code"]), literal(query["name"]), "'1'", "'1'",
        literal(json.dumps(query["queries"], ensure_ascii=False)),
        literal(json.dumps(query["template"], ensure_ascii=False)),
    ]
    lines.append(
        "INSERT INTO `tt`.`c_service_sql`(service_code,name,params,query_model,`sql`,template)"
        " SELECT " + ",".join(values)
        + " WHERE NOT EXISTS(SELECT 1 FROM `tt`.`c_service_sql`"
        " WHERE service_code='api.getListPayFee');"
    )
    output = ROOT / "deploy/compat-migration.sql"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
