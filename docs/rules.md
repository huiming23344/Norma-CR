# Coding Standards

集中管理代码规范的注册表与文档。规则数据会自动注入审查 prompt，并可通过工具读取 Markdown 文档。

## 目录结构
- `registry.yaml`：规则注册表（语言 + 域 + 文档路径 + prompt_hint 等）。
- `rules/<lang>/`：规则说明文档（Markdown）。

## registry 字段说明
```yaml
- id: GO-STYLE-001          # 唯一标识
  deprecated: false         # 可选，true 则不会作为模型输入
  title: "导出符号必须提供注释，保持可读性"
  language: go              # 仅支持 go/python
  severity: info            # 可选，占位供后续拓展
  domains: [STYLE]          # 适用的 domain 列表
  path: "coding-standards/rules/go/GO-STYLE-001.md"  # 可选，规则文档
  prompt_hint: >            # 可选，强烈建议填写，供模型优先参考
    检查新增/修改的导出类型、函数、常量和接口是否带有 Go 风格注释（以名称开头）。
    确保注释解释用途、关键约束以及并发/性能注意事项，避免信息缺失。
```
`id/title/severity/prompt_hint` 会直接作为模型输入；如有 `path`，agent 可调用 `code_standard_doc(rule_id)` 读取全文；`deprecated:true` 的规则会在注入时被过滤。

## 规则在审查流程中的使用
1. 规则加载：`cr_agent/rules/loader.py` 解析 `registry.yaml`，过滤 `deprecated`，按语言+domain 聚合为 `RulesCatalog`。
2. Prompt 注入：`cr_agent/file_review.py` 在每个标签 agent prompt 中注入适用规则（语言+domain），并提示可调用 `code_standard_doc(rule_id)` 获取文档。
3. 报告输出：`cr_agent/reporting.py` 会在带 rule_id 的问题里展示 rule title/prompt_hint 等说明。

## 创建新规则
1. 在 `coding-standards/rules/<lang>/` 下添加 Markdown 文档（可选）。
2. 在 `registry.yaml` 增加一条规则记录，填入 `id/title/domains`，视需要添加 `prompt_hint` 和 `path`。
3. 如规则已废弃，设置 `deprecated: true`，即保留记录但不再注入模型。
4. 可以运行tool文件夹中的list_rules.py来检查已经导入的rules
