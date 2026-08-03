#!/usr/bin/env python3
"""Fail-closed coverage gate for generated test cases."""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path


NUMBER_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:[<>≤≥=±~～]?\s*)?\d+(?:\.\d+)?\s*"
    r"(?:%|mm|cm|m|kg|g|ms|s|秒|分钟|次|N|轴|度|°|万平米|平米)"
)
TABLE_RE = re.compile(r"<table\b.*?</table>", re.I | re.S)
ROW_RE = re.compile(r"<tr\b.*?</tr>", re.I | re.S)
CELL_RE = re.compile(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")
ENUM_HINTS = ("键位表", "语音指令表", "离线语音", "障碍类型", "障碍物类型")


def normalize(value):
    return re.sub(r"[\s`*_，,。；;：:（）()<>≤≥=±~～/\\-]+", "", str(value)).lower()


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def all_cases(data):
    return [
        case
        for sheet in data.get("sheets", [])
        for case in sheet.get("cases", [])
        if isinstance(case, dict)
    ]


def validation_result(cases_path):
    validator = Path(__file__).with_name("validate_cases.py")
    proc = subprocess.run(
        [sys.executable, str(validator), str(cases_path), "--strict-detail"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    return {
        "passed": proc.returncode == 0,
        "output": (proc.stdout + proc.stderr).strip(),
    }


def threshold_result(requirement_path, cases_blob):
    quality_path = Path(requirement_path).with_name("quality_review.json")
    source = Path(requirement_path).read_text(encoding="utf-8", errors="replace")
    if quality_path.exists():
        quality = load_json(quality_path)
        source = "\n".join(
            str(item.get("text", ""))
            for item in quality.get("requirements", [])
            if item.get("testable", True)
        )
    values = []
    seen = set()
    for match in NUMBER_RE.finditer(source):
        value = match.group(0).strip()
        key = normalize(value)
        if key and key not in seen:
            seen.add(key)
            values.append(value)
    covered = [value for value in values if normalize(value) in cases_blob]
    missing = [{"value": value} for value in values if value not in covered]
    return {
        "passed": not missing,
        "total": len(values),
        "covered": len(covered),
        "missing": missing,
    }


def enum_candidates(requirement_text):
    candidates = []
    for table in TABLE_RE.finditer(requirement_text):
        context = requirement_text[max(0, table.start() - 500):table.start()]
        heading_start = max(context.rfind("\n#"), context.rfind("\n###"))
        if heading_start >= 0:
            context = context[heading_start:]
        if not any(hint in context for hint in ENUM_HINTS):
            continue
        rows = ROW_RE.findall(table.group(0))
        for row in rows[1:]:
            cells = [
                TAG_RE.sub("", cell).strip()
                for cell in CELL_RE.findall(row)
            ]
            cells = [cell for cell in cells if cell]
            if not cells:
                continue
            if "键位表" in context:
                # rowspan 后续行不再重复“逆解模式”，此时首列就是具体动作。
                label = (
                    cells[1]
                    if cells[0] == "逆解模式" and len(cells) > 1
                    else cells[0]
                )
            else:
                label = cells[0]
            if len(normalize(label)) >= 2:
                candidates.append(label)
    return list(dict.fromkeys(candidates))


def enum_result(requirement_path, cases_blob):
    text = Path(requirement_path).read_text(encoding="utf-8", errors="replace")
    candidates = enum_candidates(text)
    def covered(item):
        variants = {
            normalize(item),
            normalize(re.sub(r"(移动|状态|功能|指令|按钮)$", "", item)),
        }
        return any(value and value in cases_blob for value in variants)

    missing = [
        {"key": item}
        for item in candidates
        if not covered(item)
    ]
    return {
        "passed": not missing,
        "missing_count": len(missing),
        "tables": [{"missing": missing}] if missing else [],
        "total": len(candidates),
        "covered": len(candidates) - len(missing),
    }


def requirement_result(cases, requirement_path):
    quality_path = Path(requirement_path).with_name("quality_review.json")
    if not quality_path.exists():
        return {"passed": False, "missing": ["quality_review.json"]}
    quality = load_json(quality_path)
    expected = [
        str(item.get("id"))
        for item in quality.get("requirements", [])
        if item.get("id") and item.get("testable", True)
    ]
    counts = Counter(
        str(req_id)
        for case in cases
        for req_id in case.get("requirement_ids", [])
    )
    missing = [req_id for req_id in expected if counts[req_id] < 3]
    return {"passed": not missing, "missing": missing, "counts": dict(counts)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("requirement")
    parser.add_argument("cases")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    cases_data = load_json(args.cases)
    cases = all_cases(cases_data)
    cases_blob = normalize(json.dumps(cases, ensure_ascii=False))
    result = {
        "validate": validation_result(args.cases),
        "requirement_coverage": requirement_result(cases, args.requirement),
        "threshold_coverage": threshold_result(args.requirement, cases_blob),
        "enum_coverage": enum_result(args.requirement, cases_blob),
    }
    result["passed"] = all(section["passed"] for section in result.values())
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        for name, section in result.items():
            if name != "passed":
                print(f"{name}: {'PASS' if section['passed'] else 'FAIL'}")
        print("🎉 三道门槛全部通过" if result["passed"] else "✗ 覆盖度门禁未通过")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
