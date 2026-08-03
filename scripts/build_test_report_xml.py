#!/usr/bin/env python3
"""Render an execution-ready engineering test report as Lark DocxXML."""

import argparse
import json
import sys
from html import escape
from pathlib import Path


def text(value):
    return escape(str(value or ""), quote=True)


def paragraph(value):
    return f"<p>{text(value)}</p>"


def list_xml(items, ordered=False):
    if not items:
        return "<p>无。</p>"
    tag = "ol" if ordered else "ul"
    return f"<{tag}>" + "".join(f"<li>{text(item)}</li>" for item in items) + f"</{tag}>"


def table_xml(headers, rows):
    if not headers:
        return "<p>无。</p>"
    header = "".join(
        f'<th background-color="light-gray">{text(item)}</th>' for item in headers
    )
    body_rows = rows or [["待记录"] + [""] * (len(headers) - 1)]
    body = []
    for row in body_rows:
        values = list(row)[:len(headers)]
        values.extend([""] * (len(headers) - len(values)))
        body.append(
            "<tr>"
            + "".join(f'<td vertical-align="top">{text(cell)}</td>' for cell in values)
            + "</tr>"
        )
    return (
        "<table><thead><tr>"
        + header
        + "</tr></thead><tbody>"
        + "".join(body)
        + "</tbody></table>"
    )


def require(data, path):
    current = data
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            sys.exit(f"缺少必填字段：{path}")
        current = current[key]
    if current in ("", None, []):
        sys.exit(f"必填字段为空：{path}")


def build(data):
    required = (
        "meta.title",
        "purpose",
        "equipment",
        "method.steps",
        "calculations",
        "record_sections",
        "result_summaries",
        "analysis",
        "conclusion",
    )
    for field in required:
        require(data, field)

    meta = data["meta"]
    status = meta.get("status") or "待执行"
    method = data["method"]
    parts = [
        f"<title>{text(meta['title'])}</title>",
        '<callout emoji="🧪" background-color="light-blue" border-color="blue">'
        f"<p>报告状态：<b>{text(status)}</b>。"
        "未提供真实执行数据时，记录值和统计结果保留为待记录/待计算，"
        "不得据此判定测试通过。</p></callout>",
        table_xml(
            ["项目", "版本", "需求来源", "报告状态", "编制人"],
            [[
                meta.get("project", ""),
                meta.get("version", ""),
                meta.get("source", ""),
                status,
                meta.get("author", ""),
            ]],
        ),
        "<h1>1. 测试目的</h1>",
        paragraph(data["purpose"]),
        "<h1>2. 测试定义</h1>",
        table_xml(
            ["术语/指标", "定义与评价口径"],
            [[item.get("term", ""), item.get("description", "")]
             for item in data.get("definition", [])],
        ),
        "<h1>3. 测试设备与工装</h1>",
        table_xml(
            ["设备/工装", "规格与要求", "用途"],
            [[
                item.get("item", ""),
                item.get("specification", ""),
                item.get("purpose", ""),
            ] for item in data["equipment"]],
        ),
        "<h1>4. 测试方法</h1>",
        paragraph(method.get("overview", "")),
        "<h2>4.1 执行步骤</h2>",
        list_xml(method["steps"], ordered=True),
        "<h2>4.2 点位与采样设计</h2>",
        paragraph(method.get("sampling", "待确认。")),
        "<h2>4.3 数据采集要求</h2>",
        paragraph(method.get("data_collection", "待确认。")),
        "<h2>4.4 脚本与附件</h2>",
        list_xml(method.get("scripts", [])),
        "<h1>5. 计算与判定方法</h1>",
        table_xml(
            ["指标", "计算公式", "变量与单位", "评价与判定方法"],
            [[
                item.get("metric", ""),
                item.get("formula", ""),
                item.get("variables", ""),
                item.get("evaluation", ""),
            ] for item in data["calculations"]],
        ),
        "<h1>6. 测试记录</h1>",
    ]

    for index, section in enumerate(data["record_sections"], 1):
        parts.extend([
            f"<h2>6.{index} {text(section.get('title', '测试记录'))}</h2>",
            paragraph(section.get("description", "")),
            table_xml(section.get("columns", []), section.get("rows", [])),
        ])

    parts.append("<h1>7. 测试结果汇总</h1>")
    for index, summary in enumerate(data["result_summaries"], 1):
        parts.extend([
            f"<h2>7.{index} {text(summary.get('title', '结果汇总'))}</h2>",
            table_xml(summary.get("columns", []), summary.get("rows", [])),
        ])

    parts.extend([
        "<h1>8. 结果分析</h1>",
        list_xml(data["analysis"]),
        "<h2>8.1 风险与影响因素</h2>",
        table_xml(
            ["风险或影响因素", "影响", "控制与缓解措施"],
            [[
                item.get("risk", ""),
                item.get("impact", ""),
                item.get("mitigation", ""),
            ] for item in data.get("risks", [])],
        ),
        "<h2>8.2 待确认项</h2>",
        list_xml(data.get("open_questions", [])),
        "<h1>9. 测试结论</h1>",
        paragraph(data["conclusion"]),
    ])
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description="把工程测试报告 JSON 渲染成飞书 DocxXML")
    parser.add_argument("report_json")
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()

    with open(args.report_json, encoding="utf-8") as source:
        data = json.load(source)
    Path(args.output).write_text(build(data), encoding="utf-8")
    print(f"✓ 已生成飞书工程测试报告 XML → {args.output}")


if __name__ == "__main__":
    main()
