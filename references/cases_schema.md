# 用例数据 JSON Schema

`build_testcase_xlsx.py` 和 `validate_cases.py` 共用的输入格式。Claude 设计完
用例后，把它们组织成这个 JSON，脚本负责渲染成 xlsx。**内容与排版解耦**——你只管
写好用例，公式/样式/合并交给脚本。

## 顶层结构

```json
{
  "meta": { ... },        // 项目元信息，写进首页
  "sheets": [ ... ]       // 测试分类，每个一个 sheet
}
```

## meta（首页元信息）

```json
"meta": {
  "project_id": "TRON2-V5",     // 项目编号，也用于首页横幅标题
  "version": "r-2.1.22",        // 版本信息
  "testers": "@Eddy@Logen",     // 测试人员，可留 "@待填写"
  "layout": "slim"              // 列布局：slim(12列,默认) | full(14列,含测试数据/图片)
}
```

全部可选，缺省留空；`layout` 缺省 `slim`（团队交付标准）。

## sheets[]（分类）

```json
{
  "name": "双足运动形态",     // sheet 标签名（必填，唯一）
  "title": "双足运动形态",    // sheet 内 A1 标题，渲染时自动追加“测试”
  "result_header": "测试结果", // K列标题，可选（真实文件有"Tron2测试结果"等写法）
  "note_header": "备注",      // L列标题，可选（亦可"测试问题记录""记录"）
  "cases": [ ... ]            // 该分类下的用例数组
}
```

## cases[]（单条用例）

```json
{
  "module": "外观尺寸",                   // 功能模块，连续相同值会自动纵向合并
  "name": "整机外观",                     // 用例名称【必填】，建议"主题-场景"二段式
  "precondition": "1.机器处于完整装配下线状态\n2.机器双臂呈伸直状态",
  "steps": "1.目测机器外观有无明显划痕、色差、间隙",  // 多步用 \n 换行【必填】
  "expected": "整机外观无明显色差、无明显划痕、无明显间隙",  // 可判定的预期【必填】
  "type": "外观检查",     // 缺省"功能测试"
  "status": "正常",       // 缺省"正常"
  "level": "高",          // 缺省"中"
  "creator": "@Jeav"      // 创建人昵称，可空
  "requirement_ids": ["REQ-001"], // 对应需求编号，用于追踪矩阵
  "requirement_text": "识别距离应为1~2m" // 可选，保留需求摘要
}
```

### 字段约束

| 字段 | 必填 | 枚举/格式 |
|------|:---:|----------|
| `module` | 建议 | 自由文本；同一子系统连续用例填相同值以触发合并 |
| `name` | ✅ | 自由文本，sheet 内唯一 |
| `precondition` | | 自由文本，多条用 `\n` |
| `steps` | ✅ | 编号步骤，`\n` 分隔 |
| `expected` | ✅ | 自由文本，含量化阈值/可观测特征更佳 |
| `type` | | 功能测试 / 性能测试 / 安全性测试 / 接口测试 / 可靠性测试 / 异常测试 / 耐久测试 / 稳定性测试 / 外观检查 / 其他测试 |
| `status` | | 正常 / 待更新 / 已废弃 |
| `level` | ✅枚举 | 高 / 中 / 低（概述用 P0 / P1 / P2） |
| `creator` | | 自由文本 |
| `requirement_ids` | 建议 | 字符串数组；一条用例可覆盖多个需求 |
| `requirement_text` | | 对应需求摘要，便于离线追踪 |

还有几个**可选**列字段，一般生成时留空（供测试阶段填）：
`result`（测试结果，填 PASS/FAIL/N/A/N/T/NOT YET）、`test_data`、`media`、`note`。

slim 布局会保留 G~J 的管理字段但默认隐藏，日常执行界面直接展示 A~F、K、L。K 列
带固定结果下拉和颜色规则，适合导入飞书在线电子表格后直接填写。

## 完整最小示例

见同目录上层 `assets/example_cases.json`。

## overview（可选「概述」sheet）

在 JSON 顶层加 `overview`，会在首页后插入一张核心功能扁平速览表（详细 sheet 的
精简对照视图）。不加则不生成。

```json
"overview": {
  "title": "TRON2整机核心功能概述",
  "items": [
    {"group": "外观检查", "item": "机器外观检查",
     "desc": "检查本体结构件外观无划痕、无留胶、无磕碰裂痕",
     "risk": "P0", "result": "PASS", "note": ""},
    {"group": "双臂形态", "item": "开关机功能",
     "desc": "关机状态短按0.5s+长按3s开机，灯显白灯闪烁→蓝灯常亮",
     "risk": "P0", "result": "PASS", "note": ""}
  ]
}
```

- `group` 连续相同自动纵向合并（如多条"双臂形态"归一组）
- `risk` 用 P0/P1/P2；`result` 用 PASS/FAIL/NA（自动着色）
- 适合做核心功能验收的一页纸总览，详细用例仍放在各分类 sheet

## 校验

```bash
python scripts/validate_cases.py cases.json
```

输出用例总数、类型分布、等级分布，并对缺必填字段、等级越界、名称重复等给出
提醒。等级分布若严重偏向单一档位，往往是边界/异常维度没拆够的信号。

生成的 Excel 会包含隐藏 sheet `_追踪数据`，保存用例与需求编号的映射。测试人员
正常填写可见 sheet 即可，不要删除该隐藏 sheet；执行结果分析依赖它生成追踪矩阵。
