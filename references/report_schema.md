# 工程测试报告 JSON Schema

`build_test_report_xml.py` 使用以下结构生成飞书 DocxXML：

```json
{
  "meta": {
    "title": "点位复现精度测试报告",
    "project": "机器人点位复现精度",
    "version": "待填写",
    "source": "飞书需求文档链接",
    "status": "待执行",
    "author": "@待填写"
  },
  "purpose": "验证拖动示教点位在自动运行时的复现精度。",
  "definition": [
    {
      "term": "点位复现精度",
      "description": "实际到达位置与示教基准位置之间的空间偏差。"
    }
  ],
  "equipment": [
    {
      "item": "光学动作捕捉设备",
      "specification": "精度和校准状态待确认",
      "purpose": "采集末端三维坐标和姿态"
    }
  ],
  "method": {
    "overview": "分别使用 MoveJ 和 MoveP 返回示教点并测量偏差。",
    "steps": [
      "开启拖动示教模式并移动末端",
      "保存当前点位作为基准点",
      "执行返回指令并采集实际位置"
    ],
    "sampling": "选取 5 个不同空间点位，每个点位重复 5 次。",
    "data_collection": "记录基准坐标、实际坐标、三轴偏差和空间偏差。",
    "scripts": ["MoveJ 下发脚本：待附加", "MoveP 下发脚本：待附加"]
  },
  "calculations": [
    {
      "metric": "单次空间位置偏差",
      "formula": "d = √(Δx² + Δy² + Δz²)",
      "variables": "Δx、Δy、Δz 为三个方向的位置偏差，单位 mm。",
      "evaluation": "平均偏差评价精度，标准差评价稳定性，验收阈值待确认。"
    }
  ],
  "record_sections": [
    {
      "title": "MoveJ 点位记录",
      "description": "记录各示教点的关节角和重复测量数据。",
      "columns": ["点位", "基准X/mm", "基准Y/mm", "基准Z/mm", "实测X/mm", "实测Y/mm", "实测Z/mm", "偏差d/mm", "备注"],
      "rows": [
        ["点位1", "待记录", "待记录", "待记录", "待记录", "待记录", "待记录", "待计算", ""]
      ]
    }
  ],
  "result_summaries": [
    {
      "title": "MoveJ 结果汇总",
      "columns": ["点位", "重复次数", "平均偏差/mm", "最大偏差/mm", "标准差/mm", "结论"],
      "rows": [
        ["点位1", "5", "待计算", "待计算", "待计算", "待执行"]
      ]
    }
  ],
  "analysis": [
    "比较不同运动方式在相同点位下的平均偏差和标准差。",
    "定位偏差较大点位与机器人姿态、负载、控制参数或测量方式的关系。"
  ],
  "risks": [
    {
      "risk": "测量设备精度不足",
      "impact": "测试结果无法反映真实复现精度",
      "mitigation": "使用校准合格设备并记录校准信息"
    }
  ],
  "open_questions": ["点位复现精度验收阈值待确认"],
  "conclusion": "当前报告状态为待执行。完成数据采集和统计后，根据平均偏差、最大偏差和标准差填写最终结论。"
}
```

必填字段：

- `meta.title`
- `purpose`
- `equipment`
- `method.steps`
- `calculations`
- `record_sections`
- `result_summaries`
- `analysis`
- `conclusion`

表格的 `columns` 与每行 `rows` 长度必须一致。无实测数据时使用“待记录”“待计算”
和“待执行”，不得生成 PASS/FAIL 或通过率。
