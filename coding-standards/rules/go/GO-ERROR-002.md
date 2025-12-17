# GO-ERROR-002 错误必须包含上下文

## 背景
在 Go 中返回裸露的 `error` 会导致调用方难以定位问题来源。应使用 `fmt.Errorf`, `errors.Wrap` 或自定义类型加入上下文信息。

## 要求
- 捕获底层错误后再次返回时，新增模块/参数信息。
- 禁止仅返回 `err` 或 `errors.New("failed")` 之类无上下文的描述。

## 示例
```go
// 推荐
if err := os.Remove(path); err != nil {
    return fmt.Errorf("clean cache %s: %w", path, err)
}
```
