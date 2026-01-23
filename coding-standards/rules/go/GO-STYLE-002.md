---
id: 'GO-STYLE-002'
title: '结构体参数传递应优先使用指针，其余类型直接值传递'
language: 'go'
domains: [STYLE]
severity: 'info'
prompt_hint: >
  检查函数参数和返回值的类型使用方式： 1）当参数为结构体（struct）时，优先使用指针传递（*T），以避免不必要的值拷贝， 并确保对结构体字段的修改在调用方可见； 2）当参数为基础类型（int、string、bool 等）或小型、不可变语义的数据时， 应直接使用值传递，避免滥用指针增加复杂性；
deprecated: false
---

# GO-STYLE-002 结构体参数传递应优先使用指针，其余类型直接值传递

## 规则说明
- 检查函数参数和返回值的类型使用方式。
- 当参数为结构体（struct）时，优先使用指针传递（`*T`），避免不必要的值拷贝，并确保对结构体字段的修改在调用方可见。
- 当参数为基础类型（`int`、`string`、`bool` 等）或小型、不可变语义的数据时，应直接使用值传递，避免滥用指针增加复杂性。
- 返回值类型遵循同样原则。

## 示例
正例：
```go
type User struct {
    Name string
}

func UpdateUser(u *User) {
    u.Name = "new-name"
}

func SetRetry(count int) {
    _ = count
}
```

反例：
```go
func UpdateUser(u User) {
    u.Name = "new-name"
}

func SetRetry(count *int) {
    _ = count
}
```