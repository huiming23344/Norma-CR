# GO-CONC-001 并发共享数据需同步

## 背景
多个 goroutine 同时访问共享数据而缺乏同步，会导致数据竞争。务必使用 channel、mutex 或原子操作来保护共享状态。

## 要求
- 对 map、slice 或自定义结构体的写操作必须加锁。
- 长时间持有锁时，需说明原因并避免阻塞其他 goroutine。

## 示例
```go
var mu sync.Mutex
mu.Lock()
stats[key]++
mu.Unlock()
```
