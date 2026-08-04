#!/usr/bin/env python3
"""Render requirement quality review JSON as Lark DocxXML."""

import argparse
import json
import sys
from html import escape
from pathlib import Path


def txt(value):
    return escape(str(value or ""), quote=True)


def table(headers, rows):
    head = "".join(
        f'<th background-color="light-gray">{txt(value)}</th>' for value in headers
    )
    body = "".join(
        "<tr>" + "".join(f'<td vertical-align="top">{txt(value)}</td>' for value in row) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def items(values):
    if not values:
        return "<p>无。</p>"
    return "<ul>" + "".join(f"<li>{txt(value)}</li>" for value in values) + "</ul>"


def build(data):
    meta = data.get("meta", {})
    summary = data.get("summary", {})
    requirements = data.get("requirements", [])
    findings = data.get("findings", [])
    if not meta.get("title"):
        sys.exit("缺少必填字段：meta.title")
    if not requirements:
        sys.exit("缺少需求清单：requirements")

    return "\n".join([
        f"<title>{txt(meta['title'])}</title>",
        "<h1>1. 检查概述</h1>",
        table(
            ["项目", "版本", "需求来源", "需求数", "问题数", "阻断数", "质量评分"],
            [[
                meta.get("project", ""),
                meta.get("version", ""),
                meta.get("source", ""),
                summary.get("requirement_count", len(requirements)),
                summary.get("issue_count", len(findings)),
                summary.get("blocker_count", 0),
                summary.get("score", ""),
            ]],
        ),
        "<h1>2. 需求目录与可测试性</h1>",
        table(
            ["需求ID", "模块", "需求描述", "可测试", "风险"],
            [[
                item.get("id", ""),
                item.get("module", ""),
                item.get("text", ""),
                "是" if item.get("testable") else "否",
                item.get("risk", ""),
            ] for item in requirements],
        ),
        "<h1>3. 质量问题清单</h1>",
        table(
            ["问题ID", "需求ID", "严重程度", "问题类别", "问题描述", "修改建议"],
            [[
                item.get("id", ""),
                item.get("requirement_id", ""),
                item.get("severity", ""),
                item.get("category", ""),
                item.get("problem", ""),
                item.get("suggestion", ""),
            ] for item in findings],
        ),
        "<h1>4. 待确认问题</h1>",
        items(data.get("open_questions", [])),
        "<h1>5. 检查结论</h1>",
        f"<p>{txt(data.get('conclusion', '需求质量检查已完成。'))}</p>",
    ]) + "\n"


def main():
    parser = argparse.ArgumentParser(description="生成需求质量检查飞书 DocxXML")
    parser.add_argument("review_json")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--title", help="覆盖在线文档标题")
    args = parser.parse_args()
    with open(args.review_json, encoding="utf-8") as source:
        data = json.load(source)
    if args.title:
        data.setdefault("meta", {})["title"] = args.title
    Path(args.output).write_text(build(data), encoding="utf-8")
    print(f"✓ 已生成需求质量检查 XML → {args.output}")


if __name__ == "__main__":
    main()
