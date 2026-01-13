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
