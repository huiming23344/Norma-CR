# GO-STYLE-007 函数默认需记录进入、离开与失败日志，工具类函数可简化日志

## 规则说明
- 默认情况下，业务函数应在进入时记录入参关键信息，在正常返回时记录完成日志，在发生错误或异常路径时记录失败日志。
- 失败日志应包含足够上下文（关键参数、错误原因、返回码等），避免仅打印 `error`。
- 工具类或纯函数（如 UUID 生成、简单格式转换、无副作用计算）可简化日志或不记录日志。
- 避免在高频调用的核心路径中打印冗余日志，权衡可观测性与性能。

## 示例
正例：
```go
func HandleOrder(ctx context.Context, orderID string) error {
    logit.Info("handle_order_start", logit.String("order_id", orderID))
    if err := doWork(orderID); err != nil {
        logit.Error("handle_order_failed", logit.String("order_id", orderID), logit.Error(err))
        return err
    }
    logit.Info("handle_order_done", logit.String("order_id", orderID))
    return nil
}
```

反例：
```go
func HandleOrder(ctx context.Context, orderID string) error {
    if err := doWork(orderID); err != nil {
        return err
    }
    return nil
}
```
