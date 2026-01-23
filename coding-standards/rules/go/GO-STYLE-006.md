---
id: "GO-STYLE-006"
title: "业务逻辑中禁止使用 o1、value1 等无语义命名"
language: "go"
domains: [STYLE]
severity: "info"
prompt_hint: >
  检查业务逻辑代码（非通用工具函数、非算法/示例代码）中的变量、参数和返回值命名： 1）禁止使用 o1、o2、v1、value1、tmp1 等无明确业务语义的命名； 2）命名应体现业务含义、角色或来源（如 userID、instanceMeta、diskInfos、targetHost）； 3）在对比、映射、聚合等业务处理中，应区分来源与语义（如 old/new、src/dst、expected/actual）； 4）仅在极短作用域、且语义高度明确的场景下（如 for 循环索引 i、j）可例外。 若在业务逻辑中发现无语义编号式命名，应提示重命名以提升可读性与可维护性。
deprecated: false
path: "coding-standards/rules/go/GO-STYLE-006.md"
---

# GO-STYLE-006 业务逻辑中禁止使用 o1、value1 等无语义命名

## 规则说明
- 检查业务逻辑代码中的变量、参数和返回值命名。
- 禁止使用 `o1`、`o2`、`v1`、`value1`、`tmp1` 等无明确业务语义的命名。
- 命名应体现业务含义、角色或来源（如 `userID`、`instanceMeta`、`diskInfos`、`targetHost`）。
- 在对比、映射、聚合等业务处理中，应区分来源与语义（如 `old/new`、`src/dst`、`expected/actual`）。
- 仅在极短作用域且语义高度明确的场景下（如 `for` 循环索引 `i`、`j`）可例外。

## 示例
正例：
```go
func DiffUsers(oldUsers, newUsers []User) []User {
    return nil
}
```

反例：
```go
func DiffUsers(o1, o2 []User) []User {
    return nil
}
```
