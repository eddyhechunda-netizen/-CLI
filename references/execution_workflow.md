# 测试执行闭环

## 输入约束

执行人员应在生成的测试用例 Excel 中填写：

- 测试结果：`PASS` / `FAIL` / `N/A` / `N/T`。
- 备注：FAIL 时填写实际现象、日志、错误码或数据。
- 不要删除隐藏 sheet `_追踪数据`，否则无法建立需求追踪关系。

## 生成执行产物

```bash
python3 scripts/analyze_execution_results.py ./已执行测试用例.xlsx \
  -o ./execution_analysis.json

python3 scripts/build_execution_report_xml.py ./execution_analysis.json \
  -o ./execution_report.xml

python3 scripts/build_defect_xlsx.py ./execution_analysis.json \
  -o ./缺陷清单.xlsx

python3 scripts/build_traceability_xlsx.py ./execution_analysis.json \
  -o ./需求追踪矩阵.xlsx
```

创建飞书执行报告：

```bash
lark-cli docs +create --content @execution_report.xml --as user
```

缺陷清单只生成草稿，不自动提交到 TAPD 或其他平台。提交前必须补齐实际结果、重现规律、
软件/主站/分电板/驱动器版本和整机版本，并由用户确认。
