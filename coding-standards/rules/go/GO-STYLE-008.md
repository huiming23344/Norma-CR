# GO-STYLE-008 日志字段 Key 命名必须全小写并使用下划线分隔

## 规则说明
- Field 的 Key 必须使用全小写字母。
- 多个单词之间使用下划线（`_`）连接，禁止驼峰、短横线或混合命名。
- Key 应具有稳定、明确的语义，避免随意缩写或临时命名。
- 同一业务域内日志字段命名保持一致，便于日志聚合、检索与分析。

## 示例
正例：
```go
logit.Info("start", logit.String("request_id", reqID))
```

反例：
```go
logit.Info("start", logit.String("requestId", reqID))
```
