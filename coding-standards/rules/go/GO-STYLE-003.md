---
id: "GO-STYLE-003"
title: "禁止使用全局变量，避免隐式状态和副作用"
language: "go"
domains: [STYLE]
severity: "warning"
prompt_hint: >
  检查代码中是否定义或使用了包级全局变量（var 定义在 package 作用域）： 1）除只读常量（const）和确有必要的不可变配置外，禁止使用可变全局变量；
deprecated: false
path: "coding-standards/rules/go/GO-STYLE-003.md"
---

# GO-STYLE-003 禁止使用全局变量，避免隐式状态和副作用

## 规则说明
- 检查代码中是否定义或使用包级全局变量（`var` 定义在 `package` 作用域）。
- 除只读常量（`const`）和确有必要的不可变配置外，禁止使用可变全局变量。

## 示例
正例：
```go
type Service struct {
    counter int
}

func (s *Service) Inc() {
    s.counter++
}
```

反例：
```go
var counter int

func Inc() {
    counter++
}
```
