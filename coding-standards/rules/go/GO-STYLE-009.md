# GO-STYLE-009 函数内重复打印同一日志字段时应复用上下文，避免重复添加 Field

## 规则说明
- 同一函数作用域内多条日志需要输出相同 Field 时，应避免反复添加字段。
- 推荐使用派生 logger、预构建 fields 或统一上下文（如 With/Bind/Context logger）方式复用公共字段。
- 公共字段应覆盖函数生命周期内稳定不变的上下文（如 `request_id`、`instance_id`、`host_name`）。
- 仅在字段值随步骤变化时，在具体日志语句中单独补充或覆盖。

## 示例
正例：
```go
logger := logit.With(logit.String("request_id", reqID))
logger.Info("step_start")
logger.Info("step_done")
```

反例：
```go
logit.Info("step_start", logit.String("request_id", reqID))
logit.Info("step_done", logit.String("request_id", reqID))
```
