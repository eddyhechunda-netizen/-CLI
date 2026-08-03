# 需求质量检查 JSON Schema

```json
{
  "meta": {
    "title": "TRON2柔顺控制需求质量检查报告",
    "project": "TRON2柔顺控制",
    "version": "需求V1.0",
    "source": "飞书需求文档链接"
  },
  "summary": {
    "requirement_count": 12,
    "issue_count": 4,
    "blocker_count": 1,
    "score": 82
  },
  "requirements": [
    {
      "id": "REQ-001",
      "module": "重力补偿",
      "text": "末端残余力≤5N",
      "testable": true,
      "risk": "P0"
    }
  ],
  "findings": [
    {
      "id": "RQ-001",
      "requirement_id": "REQ-002",
      "severity": "阻断",
      "category": "缺少验收标准",
      "problem": "负载辨识仅描述准确，未给出允许误差",
      "suggestion": "补充质量和质心辨识的允许误差及统计口径"
    }
  ],
  "open_questions": ["负载辨识允许误差是多少？"],
  "conclusion": "核心流程可测试，但需先补齐阻断项。"
}
```

## 检查维度

- 完整性：前置条件、输入、行为、输出、异常分支是否齐全。
- 明确性：是否存在“快速、稳定、友好、适当、尽量”等模糊词。
- 可测试性：是否有可观测结果和明确判定标准。
- 一致性：术语、范围、状态和数值是否冲突。
- 边界性：数字范围、超时、精度和容量是否定义边界行为。
- 异常性：失败、断电、超限、丢失和恢复流程是否说明。

`severity` 使用：阻断 / 严重 / 一般 / 提示。`score` 范围为 0~100。
