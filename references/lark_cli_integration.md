# 飞书 CLI 接入说明

本 Skill 默认使用用户身份读取飞书需求文档。读取后，用户可以选择生成测试用例
`.xlsx` 并上传云盘，或生成测试报告飞书在线文档。

## 前置条件

```bash
lark-cli config init
lark-cli auth login --domain docs --domain drive
```

执行前用以下命令确认 `identities.user.status` 为 `ready`：

```bash
lark-cli auth status --json --verify
```

## 标准链路

```bash
# 1. 读取飞书需求文档或 Wiki
python3 scripts/extract_requirements.py '<飞书URL>' -o ./requirement.md

# 2. Agent 根据 requirement.md 和 case_design_method.md 生成 cases.json

# 3. 校验并生成 Excel
python3 scripts/validate_cases.py ./cases.json
python3 scripts/build_testcase_xlsx.py ./cases.json -o ./测试用例.xlsx

# 4. 上传到指定云盘文件夹
lark-cli drive +upload --file ./测试用例.xlsx \
  --folder-token <FOLDER_TOKEN> --as user
```

测试报告分支：

```bash
# 1. Agent 根据 requirement.md 生成 report.json
python3 scripts/build_test_report_xml.py ./report.json -o ./test_report.xml

# 2. 创建飞书在线文档
lark-cli docs +create --content @test_report.xml --as user
```

不传 `--folder-token` 时上传到用户云盘根目录。目标是 Wiki 节点时，改用
`--wiki-token <WIKI_NODE_TOKEN>`。

## 身份和权限

- 读取用户文档、上传用户云盘统一使用 `--as user`。
- 用户身份过期时，重新执行
  `lark-cli auth login --domain docs --domain drive`。
- 出现缺少 scope 时，使用错误响应里的 `hint` 或按最小权限执行
  `lark-cli auth login --scope '<missing_scope>'`。
- 上传属于写操作；目标位置未明确时先让用户确认。

## 文件格式选择

默认使用 `drive +upload` 保留 `.xlsx` 原文件。只有用户明确要求在线编辑时，才使用
`drive +import --type sheet` 转成飞书电子表格；导入转换可能改变复杂公式或样式。
