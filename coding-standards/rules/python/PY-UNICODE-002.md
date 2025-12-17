# PY-UNICODE-002 IO 必须指定编码

## 背景
Python 默认编码依赖系统设置，未指定编码读取或写入文本文件时容易产生乱码或不可预测行为。

## 要求
- 使用 `open()` 时显式传入 `encoding="utf-8"` 等值。
- 与外部系统交互（网络、文件、数据库）时，需说明编码假设。

## 示例
```python
with open(path, "w", encoding="utf-8") as fp:
    fp.write(text)
```
