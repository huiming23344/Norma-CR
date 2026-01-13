# GO-STYLE-004 闭包逻辑应保持简短，函数内定义的 func 不得超过 5 行

## 规则说明
- 检查函数内部定义的匿名函数或闭包（func literal）。
- 闭包体逻辑应保持内聚和简洁，原则上不超过 5 行有效代码。
- 若闭包包含复杂控制流、业务判断或多步处理，应抽取为具名函数。
- 发现函数内定义的 func 逻辑超过 5 行时，应提示拆分为独立函数。

## 示例
正例：
```go
for _, id := range ids {
    go func(id string) {
        process(id)
    }(id)
}
```

反例：
```go
go func(id string) {
    if err := stepOne(id); err != nil {
        handle(err)
        return
    }
    if err := stepTwo(id); err != nil {
        handle(err)
        return
    }
    finish(id)
}(id)
```
