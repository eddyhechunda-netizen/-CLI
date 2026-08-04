#!/usr/bin/env python3
"""Build Mermaid and Feishu XML test-point mind maps from cases.json."""

import argparse
import json
from html import escape
from pathlib import Path


def clean(value):
    return " ".join(str(value or "").replace("\n", " ").split())


def mermaid_label(value):
    return clean(value).replace("(", "（").replace(")", "）")


def build(data):
    project = clean(data.get("meta", {}).get("project_id") or "测试用例")
    lines = ["mindmap", f"  root(({mermaid_label(project)} 测试点))"]
    total = 0
    for sheet in data.get("sheets", []):
        sheet_name = clean(sheet.get("title") or sheet.get("name") or "未分类")
        lines.append(f"    {mermaid_label(sheet_name)}")
        modules = {}
        for case in sheet.get("cases", []):
            module = clean(case.get("module") or "其他")
            modules.setdefault(module, []).append(case)
            total += 1
        for module, cases in modules.items():
            lines.append(f"      {mermaid_label(module)}")
            for case in cases:
                name = mermaid_label(case.get("name") or "未命名测试点")
                level = clean(case.get("level"))
                suffix = f"〔{level}〕" if level else ""
                lines.append(f"        {name}{suffix}")
    return project, len(data.get("sheets", [])), total, "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cases")
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("--xml", required=True)
    parser.add_argument("--title", help="覆盖思维导图标题")
    args = parser.parse_args()

    data = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    project, category_count, total, mermaid = build(data)
    title = clean(args.title) or f"{project} 测试点思维导图"
    Path(args.output).write_text(mermaid, encoding="utf-8")
    xml = (
        f"<title>{escape(title)}</title>\n"
        f"<p>按「分类 → 功能模块 → 测试点」自动汇总，共 "
        f"{category_count} 个分类、{total} 个测试点。</p>\n"
        '<whiteboard type="mermaid">\n'
        f"{escape(mermaid)}"
        "</whiteboard>\n"
    )
    Path(args.xml).write_text(xml, encoding="utf-8")
    print(f"生成 {total} 个测试点：{args.output}、{args.xml}")


if __name__ == "__main__":
    main()
