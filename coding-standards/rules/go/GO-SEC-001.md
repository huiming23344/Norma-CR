## GO-SEC-001 敏感配置和凭证必须加密管理

- 配置文件或代码中不得硬编码密钥、token、账号密码
- 请改用环境变量或 KMS 管理，必要时结合 vault
- 日志输出需脱敏，禁用 fmt.Printf("%s", secret)
