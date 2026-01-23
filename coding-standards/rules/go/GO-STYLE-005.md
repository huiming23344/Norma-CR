---
id: "GO-STYLE-005"
title: "禁止使用 map 的指针类型，直接使用 map 值传递"
language: "go"
domains: [STYLE]
severity: "info"
prompt_hint: >
  检查代码中是否出现 map 的指针类型（*map[K]V）作为参数、返回值或结构体字段： 1）Go 中的 map 本身是引用语义，值传递时仅复制 header，底层数据仍然共享； 2）使用 *map 不会带来性能收益，反而增加心智负担和空指针风险； 3）如需在函数中修改 map 内容，直接传递 map 即可； 4）若需要整体替换 map（重新分配），应通过返回值显式返回，而不是使用 map 指针。 若发现 *map 的使用，应提示改为直接使用 map，并说明其引用语义特性。
deprecated: false
path: "coding-standards/rules/go/GO-STYLE-005.md"
---

# GO-STYLE-005 禁止使用 map 的指针类型，直接使用 map 值传递

## 规则说明
- 检查是否出现 `*map[K]V` 作为参数、返回值或结构体字段。
- Go 中 map 本身为引用语义，值传递时仅复制 header，底层数据仍共享。
- 使用 `*map` 无性能收益，反而增加心智负担和空指针风险。
- 如需在函数中修改 map 内容，直接传递 map 即可。
- 若需要整体替换 map（重新分配），应通过返回值显式返回，而不是使用 map 指针。

## 示例
正例：
```go
func AddCounter(stats map[string]int, key string) {
    stats[key]++
}
```

反例：
```go
func AddCounter(stats *map[string]int, key string) {
    (*stats)[key]++
}
```
