#!/usr/bin/env python3
"""Render execution analysis JSON as a Lark test result report."""

import argparse
import json
from html import escape
from pathlib import Path


def txt(value):
    return escape(str(value or ""), quote=True)


def pct(value):
    return f"{float(value or 0) * 100:.2f}%"


def table(headers, rows):
    head = "".join(
        f'<th background-color="light-gray">{txt(value)}</th>' for value in headers
    )
    body = "".join(
        "<tr>" + "".join(f'<td vertical-align="top">{txt(value)}</td>' for value in row) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def build(data):
    meta = data.get("meta", {})
    summary = data["summary"]
    failed = [case for case in data.get("cases", []) if case.get("result") == "FAIL"]
    conclusion = (
        f"本轮共执行并形成结论 {summary['tested']} 条，"
        f"发现 {summary['fail']} 条失败用例。"
        + ("存在失败项，暂不建议判定整体通过。" if summary["fail"] else "当前已执行用例未发现失败项。")
    )
    return "\n".join([
        f"<title>{txt(meta.get('project') or '项目')}测试执行结果报告</title>",
        "<h1>1. 执行概述</h1>",
        table(
            ["项目", "版本", "测试人员", "总用例", "已测试", "完成率", "PASS", "FAIL", "N/A", "N/T"],
            [[
                meta.get("project", ""),
                meta.get("version", ""),
                meta.get("testers", ""),
                summary["total"],
                summary["tested"],
                pct(summary["completion_rate"]),
                summary["pass"],
                summary["fail"],
                summary["na"],
                summary["nt"],
            ]],
        ),
        "<h1>2. 失败用例</h1>",
        table(
            ["分类", "模块", "用例", "需求ID", "预期结果", "实际结果"],
            [[
                case.get("sheet", ""),
                case.get("module", ""),
                case.get("name", ""),
                ",".join(case.get("requirement_ids", [])),
                case.get("expected", ""),
                case.get("note", "") or "实际现象待补充",
            ] for case in failed],
        ) if failed else "<p>当前没有 FAIL 用例。</p>",
        "<h1>3. 需求追踪状态</h1>",
        table(
            ["需求ID", "需求摘要", "关联用例", "PASS", "FAIL", "未执行", "状态"],
            [[
                item.get("requirement_id", ""),
                item.get("requirement_text", ""),
                item.get("case_count", 0),
                item.get("pass", 0),
                item.get("fail", 0),
                item.get("not_yet", 0),
                item.get("status", ""),
            ] for item in data.get("traceability", [])],
        ),
        "<h1>4. 缺陷摘要</h1>",
        table(
            ["缺陷ID", "标题", "严重程度", "优先级", "实际现象"],
            [[
                item.get("defect_id", ""),
                item.get("title", ""),
                item.get("severity", ""),
                item.get("priority", ""),
                item.get("actual", ""),
            ] for item in data.get("defects", [])],
        ) if data.get("defects") else "<p>当前没有由 FAIL 用例生成的缺陷草稿。</p>",
        "<h1>5. 执行结论</h1>",
        f"<p>{txt(conclusion)}</p>",
    ]) + "\n"


def main():
    parser = argparse.ArgumentParser(description="生成测试执行结果飞书 DocxXML")
    parser.add_argument("analysis_json")
    parser.add_argument("-o", "--output", required=True)
    args = parser.parse_args()
    with open(args.analysis_json, encoding="utf-8") as source:
        data = json.load(source)
    Path(args.output).write_text(build(data), encoding="utf-8")
    print(f"✓ 已生成测试执行报告 XML → {args.output}")


if __name__ == "__main__":
    main()
