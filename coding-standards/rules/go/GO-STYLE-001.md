# GO-STYLE-001 函数参数超过4个时必须使用结构体封装传参

## 规则说明
- 当函数或方法参数数量大于 4 个时，必须使用结构体封装传参（例如 Options/Params/Request）。
- 允许保留 `context.Context` 作为首参，其余业务参数总数仍不得超过 4 个；如超过则必须封装。
- 避免为绕开改动而新增无意义参数；应重构为结构体并保证字段命名清晰，可选字段使用指针或明确零值策略，并在注释中说明关键约束与默认行为。

## 示例
正例：
```go
type CreateUserParams struct {
    Name   string
    Age    int
    Role   string
    Active bool
}

func CreateUser(ctx context.Context, p CreateUserParams) error {
    return nil
}
```

反例：
```go
func CreateUser(ctx context.Context, name string, age int, role string, active bool, region string) error {
    return nil
}
```
