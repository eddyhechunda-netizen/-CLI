---
name: lark-req-to-testcases
version: 3.0.0
description: 读取飞书云文档、飞书 Wiki 或本地需求，完成需求质量检查、测试用例在线表格生成、执行结果分析、工程测试报告、FAIL 结构化缺陷清单和需求追踪矩阵。也支持只生成测试用例或可直接执行并回填数据的工程测试报告。不会自动提交缺陷，也不会虚构未执行的测试结论。当用户需要“需求质量检查”“根据需求生成测试用例或测试报告”“分析已执行测试用例”“FAIL 转缺陷清单”“生成需求追踪矩阵”时使用。
metadata:
  requires:
    bins: ["lark-cli", "python3"]
---

# 需求文档 → 测试用例在线表格 / 测试报告飞书文档

支持三种入口：

1. **测试用例在线表格**：把每个需求点穷举成可执行、可判定的细粒度用例。
2. **测试报告飞书文档**：生成可直接执行和回填数据的工程测试报告，包含测试目的、
   指标定义、设备工装、测试方法、计算公式、测试记录表、结果汇总、分析和结论。
3. **完整测试闭环**：需求质量检查 → 测试用例 → 执行填写 → 结果报告 →
   FAIL 缺陷清单 → 需求追踪矩阵。

测试用例分支的核心不是机械搬运需求，
而是**把每个需求点穷举展开**：需求里一句"识别距离 1~2m"，要拆成覆盖 0.5/1.0/
1.5/2.0/2.5m、不同角度、不同污损的一组用例。产出是一个多 sheet 的 .xlsx，带
首页自动统计公式，排版与团队标准模板一致。

> **飞书前置条件：** 先阅读
> [`../lark-shared/SKILL.md`](../lark-shared/SKILL.md)、
> [`../lark-doc/references/lark-doc-fetch.md`](../lark-doc/references/lark-doc-fetch.md) 和
> [`../lark-drive/references/lark-drive-upload.md`](../lark-drive/references/lark-drive-upload.md)。
> 读取用户云文档和上传用户云盘默认使用 `--as user`。

## 何时用

用户给了飞书文档/Wiki 链接、需求/PRD（或指向一个本地需求文件），想要测试用例表、
测试用例 Excel 或测试报告文档。典型说法："根据这个需求写测试用例""把 PRD 转成
xlsx""根据需求生成测试报告""读取这个飞书需求，生成后放到云盘"。

如果用户只说“读取需求后生成产物”，询问选择“测试用例”“测试报告”还是“完整闭环”。
如果用户上传的是已经填写结果的测试用例 Excel，直接进入执行结果分析，不再重复读取需求。

## 机器人日志诊断工作流

收到机器人运行日志分析任务时，每份日志必须独立执行以下流程，禁止套用特定电机号、
错误码或历史样本的固定结论：

1. 先从机器状态主节点还原异常发生、主站退出、重启和恢复时间线（TRON2 系列为 snowball，
   人形机器（SN 以 HU_D04 开头）为 mission_engine，二者等价）；只有确认 ECM 异常后
   才进入 EtherCAT 深度分析。
2. ECM 异常必须读取 `references/ethercat_master_diagnosis.md`，并只使用 ethercat
   节点证据定位根因。
3. 扫描全部异常电机打印，记录每个 motor、statusword、code 和时间；不得只分析最后一条，
   也不得遗漏 `code=0x0` 但 statusword 非正常的瞬时告警。
4. 先按时间顺序建立触发链。若电机异常打印后紧接 `Too many loss`，该电机异常必须作为
   主站异常的直接触发原因；后续重启恢复不能反向改判为遥控器掉电。只有异常前没有明确的
   电机、配置、通信或供电错误证据时，才能采用“遥控器手动掉电/上电”模板。
5. 按机器 SN 选择拓扑表，把 motor 映射到 slave；依次核对异常电机状态字、前一从站
   link_status 及 ret、`[88]/[8a]` 帧错误计数、`[8f]/[90]/[91]/[92]` lost link 计数。
   电机驱动故障码（状态字非 0 / `错误代码是 0x%x`）也须按机型选表：TRON2 系列
   （snowball，DACH/SF/WF）查「三、Tron2 电机驱动故障保护机制说明」，人形机器
   （mission_engine，HU_D04）查「三·人形 人形电机驱动故障保护机制说明」，二者故障码
   含义不同（如 0xFF01、0x4400），切勿混用。
6. `link_status=0x5617` 不能脱离 ret、lost link 计数和后续恢复状态单独定性为硬件断线；
   lost link 全为 0 时只能写“无 lost-link 硬件断线证据”。若帧错误计数非零，不得写成
   “所有 EtherCAT 错误计数器均为 0”。
7. 恢复状态必须使用异常发生后的证据：重新发现从站、对应电机重新使能成功、状态字恢复，
   或日志末尾仍失败；故障前的正常启动不能作为恢复依据。
8. 输出前逐项回查：所有异常电机和 statusword/code 均已进入最终结论；问题类型、
   受影响电机/从站、触发原因、后续状态、时间线和排查建议均有原始日志证据。
9. 若只有启动阶段短暂 `ecm err`，随后出现 `ethercat ok/ecm ok`，且没有电机异常、
   `Too many loss`、主站退出、非零 lost link 或其他通信掉线证据，则直接回复
   “这是一个正常日志，无 EtherCAT 通信异常或电机故障”，不要输出异常与错误分析、
   风险与建议或 EtherCAT 主站异常根因。

## 产出长什么样

一个 .xlsx（规格对齐团队真实交付的测试用例表）：
- **首页**：项目信息 + 目录汇总表，用 INDIRECT 公式自动统计各分类用例数、完成率、
  PASS/FAIL（已测 = 有结论的用例数 = PASS+FAIL+NA+NT，完成率 = 已测/总数）
- **分类 sheet**：每 sheet 左上有统计区，第 9 行表头，第 11 行起是穷举出来的用例，
  功能模块自动纵向合并。分类可按**测试视角**（硬件/软件/接口/系统）或按**运动形态**
  （双足/双轮足/双臂…）切——看需求的自然骨架，详见方法论文档
- **可选「概述」sheet**：核心功能一页纸总览（测试项/描述/风险等级/结论）

列布局默认 **slim（12列：…创建人|测试结果|备注）**，即团队实际用的版本；需要附
测试证据时可在 `meta.layout` 设 `"full"`（14列，多测试数据/图片列）。

样式、公式、合并全部由脚本保证与真实模板一致——**你只需专注设计好用例内容**。

## 公共工作流

### 1. 获取并读懂需求

#### 飞书云文档或 Wiki

首次使用先检查用户身份；用户身份不可用时，按 `lark-shared` 发起 docs + drive 业务域授权：

```bash
lark-cli auth status --json --verify
lark-cli auth login --domain docs --domain drive --no-wait --json
```

然后直接把飞书 `/docx/` 或 `/wiki/` 链接交给抽取脚本。脚本内部调用
`lark-cli docs +fetch --doc-format markdown --detail simple --as user`，并从 JSON
响应中提取正文：

```bash
python3 scripts/extract_requirements.py '<飞书文档或Wiki URL>' -o ./requirement.md
```

如果链接类型不明确，先检查：

```bash
lark-cli drive +inspect --url '<飞书URL>' --as user
```

#### 本地文件

用脚本抽取需求文本（PDF 尽量保留表格排版）：

```bash
python3 scripts/extract_requirements.py <需求文件.pdf> -o ./requirement.txt
```

支持 pdf/docx/txt/md。读完通读一遍，在脑子里列出所有需求点、数字阈值、
"若…则…"分支、"支持多种…"的枚举项、量化指标。这些就是穷举的原料。

需求获取完成后，按用户选择进入以下分支。

## 完整闭环第 1 步：需求质量检查

在生成用例前，按 `references/quality_review_schema.md` 检查需求的完整性、明确性、
可测试性、一致性、边界和异常处理。为每条原子需求分配稳定编号 `REQ-001`、
`REQ-002`……，后续用例必须通过 `requirement_ids` 复用这些编号。

把检查结果写入 `./quality_review.json`，生成并创建飞书质量检查报告：

```bash
python3 scripts/build_quality_report_xml.py ./quality_review.json \
  -o ./quality_review.xml
lark-cli docs +create --content @quality_review.xml --as user
```

存在“阻断”问题时，报告中明确提示；除非用户要求继续，否则优先等待需求补充后再生成
最终用例。用户允许带风险继续时，可生成用例，但必须把未明确阈值写入待确认项，不能
擅自补造需求指标。

## 分支 A：生成测试用例在线表格

### A1. 设计用例（本 skill 的核心价值所在）

**这一步最关键，不要偷懒。** 对每个需求点，套用"七问法"逐个展开成多条用例：
正常路径 → 边界值 → 分档枚举 → 异常/失败 → 环境场景 → 干扰鲁棒 → 指标量化。

详细方法、字段填写规范、分类原则见 **`references/case_design_method.md`——
设计用例前必读**。它讲清楚了"一句需求怎么变成 5~7 条用例"，这是产出质量的分水岭。

判断穷举是否到位的标尺：普通可测试需求至少 3 条；核心功能、安全保护、接口和量化
指标通常 6~10 条。拿成熟模板做参照，一个中等复杂度的硬件需求点（如"状态指示灯有
四种状态"）通常能产出 8~12 条用例。如果一个需求点只写了 1~2 条，多半是边界、
异常、场景维度没拆开，回去对照七问法补。机器人详细模式的总量下限为
`max(80, 原子需求数×3)`。

### A2. 组织成 JSON

把设计好的用例写成结构化 JSON（格式见 `references/cases_schema.md`，
范本见 `assets/example_cases.json`）。按测试视角分 sheet，同一子系统的用例
`module` 字段填相同值（脚本会自动纵向合并）。每条用例必须填写
`requirement_ids`，引用需求质量检查阶段生成的稳定需求编号。

写到当前工作目录下的 `./cases.json`。后续上传命令只接受 cwd 下的相对路径，
因此最终 xlsx 也应生成在当前工作目录。

### A3. 校验

```bash
python3 scripts/validate_cases.py ./cases.json

# 机器人详细模式：同时检查总量、需求覆盖密度和字段可执行性
python3 scripts/validate_cases.py ./cases.json --strict-detail
```

看用例总数和**类型/等级分布**。如果清一色"功能测试/高"，说明没拆出性能、
安全、异常维度，也没做等级区分——这是质量不达标的信号，回第 2 步补。
修掉所有阻断级错误（缺必填字段、等级越界）。

### A4. 生成 xlsx

```bash
python3 scripts/build_testcase_xlsx.py ./cases.json -o ./<输出.xlsx>
```

输出路径建议放在用户的工作目录，文件名贴合项目（如 `TRON2-自动回充测试用例.xlsx`）。

### A5. 自检

打开生成的文件抽查，或用脚本快速核对结构。**关键自检点**：
- sheet 数、各 sheet 用例数是否符合预期
- 首页公式是否能算（可选：用 `libreoffice --headless --convert-to xlsx` 重算后读回，
  确认首页用例数 = 各 sheet 之和）
- 用例是否真的"穷举"了——随机挑几个需求点，回查是否覆盖了边界和异常

### A6. 导入为飞书在线电子表格

导入是写操作。用户已明确要求交付在线测试用例时执行；否则先确认目标位置。优先先预览请求：

```bash
# 导入到用户云盘根目录，转换为在线电子表格
lark-cli drive +import --file ./<输出.xlsx> --type sheet --name "<在线表格标题>" --as user --dry-run
lark-cli drive +import --file ./<输出.xlsx> --type sheet --name "<在线表格标题>" --as user

# 导入到指定文件夹
lark-cli drive +import --file ./<输出.xlsx> --type sheet \
  --folder-token <FOLDER_TOKEN> --name "<在线表格标题>" --as user
```

`.xlsx` 是渲染和备份中间产物，默认交付 `drive +import --type sheet` 返回的在线
`/sheets/` 链接。导入后应确认标题、sheet 顺序、隐藏列、合并单元格和结果下拉仍然存在。
同时必须为首页、统计区、表头、字段说明和全部用例数据区补齐飞书原生四边框：
黑色、实线、细线。不能只依赖 XLSX 内的边框，因为导入在线表格时边框样式可能丢失。
边框范围必须精确覆盖实际用例末行，不得给表尾空白行批量加框。

向用户交付时，简要说明：飞书在线表格链接、分了几类、共多少条用例、覆盖了哪些维度，
以及测试结果列该怎么填（用 PASS/FAIL/N/A/N/T 才能触发首页统计）。

生成的 Excel 包含隐藏 sheet `_追踪数据`。不要删除它；执行分析会用它恢复
“需求 → 用例”的映射。

## 分支 B：生成测试报告飞书文档

这里生成的是**执行就绪的工程测试报告**。报告不仅说明测什么，还必须让执行人员知道
使用什么设备、如何操作、测量几次、记录哪些字段、如何计算指标，以及最终如何判定。
需求文档没有提供真实执行数据时，禁止编造 PASS/FAIL、缺陷数量、通过率或实测结论；
报告状态应明确标记为“待执行/待验证”，实测单元格使用“待记录/待计算”。

### B1. 设计报告内容

设计前阅读 `references/test_report_method.md`，严格按以下主章节组织：

- 测试目的
- 测试定义
- 测试设备与工装
- 测试方法（有序步骤、点位/样本、重复次数、采集方式）
- 计算与判定方法（公式、变量、单位、统计口径、阈值）
- 测试记录（按模式/指令/工况拆分的可填写表格）
- 测试结果汇总（平均值、最大值、标准差、成功率等）
- 结果分析（对比维度、异常定位和影响因素）
- 测试结论与待确认项

把内容组织成 `references/report_schema.md` 定义的 JSON，范本见
`assets/example_report.json`，写到 `./report.json`。

### B2. 渲染飞书 DocxXML

```bash
python3 scripts/build_test_report_xml.py ./report.json -o ./test_report.xml
```

脚本负责 XML 转义、表格、标题层级和“待执行”声明。生成后必须检查记录表能否直接
用于执行，结果汇总是否与原始记录对应，公式和字段是否足以支撑最终结论。

### B3. 创建飞书在线文档

创建文档是写操作。用户已明确要求生成报告时可以执行；目标文件夹未指定时创建在
用户默认文档位置：

```bash
lark-cli docs +create --content @test_report.xml --as user

# 创建到指定文件夹或 Wiki 父节点
lark-cli docs +create --content @test_report.xml \
  --parent-token <PARENT_TOKEN> --as user
```

较长报告如果单次创建触发参数限制，按 `lark-doc-create-workflow.md` 先创建标题和
章节骨架，再使用 `docs +update` 逐节写入。创建完成后读取返回的
`data.document.url` 交付给用户。

## 执行填写与结果闭环

用户完成测试后，应在 Excel 的测试结果列填写 `PASS` / `FAIL` / `N/A` / `N/T`；
FAIL 用例必须尽量在备注列填写实际现象、日志或错误码。

收到已填写结果的 Excel 后，阅读 `references/execution_workflow.md` 并执行：

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

### 自动结果报告

用执行数据创建飞书在线文档：

```bash
lark-cli docs +create --content @execution_report.xml --as user
```

报告必须以实际填写结果为准，展示总数、完成率、PASS/FAIL/N/A/N/T、失败用例、
需求追踪状态和缺陷摘要。不得把未执行用例计为通过。

### FAIL 转结构化缺陷清单

每条 FAIL 用例生成一条缺陷草稿，包含标题、需求 ID、模块、前置条件、复现步骤、
预期结果、实际结果、严重程度、优先级和版本字段。严重程度和优先级可根据用例等级
给出初始建议，但“重现规律”和各版本字段不确定时留空。

**只生成 `缺陷清单.xlsx`，不得自动提交 TAPD、飞书任务或其他缺陷平台。**
提交前必须由用户补齐并确认。

### 需求追踪矩阵

`需求追踪矩阵.xlsx` 汇总每条需求关联的用例、PASS/FAIL/未执行数量和状态：

- `PASS`：关联用例全部通过
- `FAIL`：至少一条关联用例失败
- `PARTIAL`：部分已执行或包含 N/A/N/T
- `NOT YET`：全部未执行

## 环境依赖

脚本依赖 `openpyxl`（生成 xlsx）；PDF 抽取优先用系统 `pdftotext`
（poppler-utils），无则用 `pdfplumber`。若缺：

```bash
pip install openpyxl pdfplumber          # 若 pip 报 externally-managed，
python3 -m venv .venv && .venv/bin/pip install openpyxl pdfplumber  # 用 venv
```

docx 需求另需 `python-docx`。

## 适配不同模板

默认复刻的是"首页+四分类"标准模板。若客户模板的列序、配色、分类不同，
改 `scripts/build_testcase_xlsx.py` 顶部的常量（`COLUMNS`/配色/字体如 `F_TITLE`(标题字体，
默认宋体14加粗)/`FIELD_HINTS`/`RESULT_LEGEND`），规格说明见 `references/template_spec.md`。改完重跑往返验证：
用一份已知数据生成、读回、对比结构，确保没改坏。

## 关键参考

- `references/case_design_method.md` — **用例设计七问法**（设计前必读）
- `references/cases_schema.md` — JSON 输入格式
- `references/template_spec.md` — 模板版面/公式/样式规格
- `references/test_report_method.md` — 工程测试报告设计方法
- `references/report_schema.md` — 测试报告 JSON 输入格式
- `references/quality_review_schema.md` — 需求质量检查数据格式
- `references/execution_workflow.md` — 执行结果、缺陷和追踪矩阵生成流程
- `references/ethercat_master_diagnosis.md` — **EtherCAT 主站(ECM)异常诊断依据**：日志分析判定主站异常后，只分析 ethercat 节点打印，按本文件的定位方法（状态字/link_status/lost link cnt）、按机器形态（SN 前缀 DACH 双臂 2.1 / SF 双足 2.2 / WF 轮足 2.3 / HU_D04 人形 2.4）选用的网络拓扑与从站号对照表、以及按机型选用的驱动故障码保护规则（TRON2 系列查「三」、人形 HU_D04/mission_engine 查「三·人形」）给唯一根因（依据飞书 wiki 沉淀）
- `assets/example_cases.json` — JSON 范本
- `assets/example_report.json` — 测试报告 JSON 范本
- `assets/example_quality_review.json` — 需求质量检查范本
