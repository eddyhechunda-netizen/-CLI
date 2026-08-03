#!/usr/bin/env python3
"""
validate_cases.py — 生成前自检用例 JSON，把问题在出 xlsx 前暴露出来。

为什么需要：测试用例表有几个"哑约束"——字段枚举值写错不会报错，但会让首页
统计公式失效或评审时被打回。例如"用例类型"必须是模板认的那几类、"用例等级"
必须是高/中/低。这个脚本把这些约束显式化，顺带统计覆盖分布，方便判断是否够穷举。

用法：
    python validate_cases.py cases.json
退出码非 0 表示有阻断级错误。
"""
import argparse
import json
import sys
from collections import Counter

# 用例类型枚举：含真实交付文件实际用到的类型（外观检查、稳定性测试等）
TYPE_ENUM = {"功能测试", "性能测试", "安全性测试", "接口测试", "可靠性测试",
             "异常测试", "耐久测试", "稳定性测试", "外观检查", "其他测试", "其他"}
STATUS_ENUM = {"正常", "待更新", "已废弃"}
# 用例等级：详细 sheet 用 高/中/低；概述/部分团队用 P0/P1/P2 风险等级，两者都放行
LEVEL_ENUM = {"高", "中", "低", "P0", "P1", "P2"}
REQUIRED = ("name", "steps", "expected")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases_json")
    ap.add_argument(
        "--strict-detail",
        action="store_true",
        help="启用机器人详细模式的覆盖密度和字段完整度门槛",
    )
    args = ap.parse_args()
    data = json.load(open(args.cases_json, encoding="utf-8"))

    errors, warnings = [], []
    sheets = data.get("sheets", [])
    if not sheets:
        errors.append("没有任何 sheet。")

    total = 0
    type_dist, level_dist, requirement_dist = Counter(), Counter(), Counter()
    for si, sh in enumerate(sheets):
        sname = sh.get("name", f"#{si}")
        cases = sh.get("cases", [])
        if not cases:
            warnings.append(f"[{sname}] 没有用例。")
        seen_names = set()
        for ci, c in enumerate(cases):
            total += 1
            tag = f"[{sname}#{ci+1}]"
            for field in REQUIRED:
                if not str(c.get(field, "")).strip():
                    errors.append(f"{tag} 缺必填字段 “{field}”。")
            name = c.get("name", "")
            if name in seen_names:
                warnings.append(f"{tag} 用例名称重复：{name}")
            seen_names.add(name)
            t = c.get("type", "功能测试")
            if t not in TYPE_ENUM:
                warnings.append(f"{tag} 用例类型 “{t}” 不在推荐枚举内，可能影响后续筛选。")
            type_dist[t] += 1
            s = c.get("status", "正常")
            if s not in STATUS_ENUM:
                warnings.append(f"{tag} 用例状态 “{s}” 不在 {STATUS_ENUM} 内。")
            lv = c.get("level", "中")
            if lv not in LEVEL_ENUM:
                errors.append(f"{tag} 用例等级 “{lv}” 必须是 高/中/低 或 P0/P1/P2。")
            level_dist[lv] += 1
            if not c.get("module"):
                warnings.append(f"{tag} 缺 module（功能模块），将无法分组合并。")
            req_ids = c.get("requirement_ids", [])
            if isinstance(req_ids, str):
                req_ids = [req_ids] if req_ids.strip() else []
            if not isinstance(req_ids, list):
                errors.append(f"{tag} requirement_ids 必须是字符串数组。")
            elif not req_ids:
                warnings.append(f"{tag} 缺 requirement_ids，无法进入需求追踪矩阵。")
            else:
                requirement_dist.update(str(req_id) for req_id in req_ids if req_id)

            if args.strict_detail:
                precondition = str(c.get("precondition", "")).strip()
                steps = str(c.get("steps", "")).strip()
                expected = str(c.get("expected", "")).strip()
                if len(precondition) < 12:
                    errors.append(f"{tag} 前置条件过于简略，需写明形态/模式/状态/配置或环境。")
                step_lines = [
                    line.strip()
                    for line in steps.splitlines()
                    if line.strip()
                ]
                if len(step_lines) < 3 or len(steps) < 35:
                    errors.append(f"{tag} 步骤不够详细，至少包含设置/操作、观测/采集、记录三个环节。")
                if len(expected) < 20:
                    errors.append(f"{tag} 预期结果过于简略，需补充可判定状态、数据、日志或错误行为。")
                vague_expected = expected.replace(" ", "") in {
                    "正常",
                    "符合预期",
                    "功能正常",
                    "测试通过",
                }
                if vague_expected:
                    errors.append(f"{tag} 预期结果不可只写“{expected}”。")

    if args.strict_detail:
        requirement_count = len(requirement_dist)
        minimum_total = max(80, requirement_count * 3)
        if total < minimum_total:
            errors.append(
                f"详细模式用例总数不足：当前 {total}，至少需要 {minimum_total}"
                f"（max(80, {requirement_count} 个需求×3)）。"
            )
        sparse_requirements = sorted(
            (req_id, count)
            for req_id, count in requirement_dist.items()
            if count < 3
        )
        if sparse_requirements:
            sample = "、".join(
                f"{req_id}({count}条)" for req_id, count in sparse_requirements[:20]
            )
            errors.append(
                f"{len(sparse_requirements)} 个需求覆盖不足 3 条：{sample}"
                + ("……" if len(sparse_requirements) > 20 else "")
            )

    print(f"=== 校验 {args.cases_json} ===")
    print(f"分类 sheet：{len(sheets)}，用例总数：{total}")
    print(f"用例类型分布：{dict(type_dist)}")
    print(f"用例等级分布：{dict(level_dist)}")
    if requirement_dist:
        print(f"需求覆盖密度：{dict(sorted(requirement_dist.items()))}")
    if warnings:
        print(f"\n⚠ {len(warnings)} 条提醒：")
        for w in warnings[:40]:
            print("  -", w)
        if len(warnings) > 40:
            print(f"  …另有 {len(warnings)-40} 条")
    if errors:
        print(f"\n✗ {len(errors)} 条阻断级错误：")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("\n✓ 校验通过，可以生成 xlsx。")


if __name__ == "__main__":
    main()
