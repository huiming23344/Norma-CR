# 使用说明

## 安装
- 克隆仓库，使用 uv 进行依赖管理
- 安装依赖：`uv sync`
- 复制 `.env.example` 为 `.env`，补全 `BASE_URL`/`API_KEY`/`MODEL_NAME` 等

## 运行
```bash
python agent.py \
  --repo /path/to/repo \
  --profile profiles/default.yaml \
  --env-file .env
```
参数优先级：命令行 > 环境变量 > `.env`。未指定 profile 时默认不屏蔽 domain，全部标签启用。

Rate limit：`CR_MAX_QPS`（可选，正数/小数）用于限制标签审查的 QPS；不配置则无限速。

报告输出：Markdown 格式为 `cr_report_<YYYYMMDD_HHMMSS>_<short_sha>_<commit_title>.md`，HTML 格式固定为 `cr_report.html`，写入仓库根目录，或通过 `CR_REPORT_DIR` 覆盖目录。`CR_REPORT_FORMAT=html` 可输出 HTML。`commit_title` 会做文件名安全处理（空格替换、非法字符移除、过长截断）。

规则文件后缀：默认只加载 `.md`，可通过 `CR_RULE_EXTENSIONS` 自定义（逗号或分号分隔）。例如 `CR_RULE_EXTENSIONS=.mdr` 或 `CR_RULE_EXTENSIONS=.md,.mdr`。

## Docker 运行
```bash
docker build -t cr-agent:latest .
docker run --rm -it \
  -v /path/to/repo:/repo \
  --env-file .env \
  -e CR_REPO_PATH=/repo \
  -e CR_PROFILE_PATH=/app/profiles/default.yaml \
  cr-agent:latest
```
`--env-file .env` 会将本地 `.env` 注入容器；也可以改用 `-e` 逐项传参。


## Profile 示例
```yaml
version: 1
repos:
  - name: foo-service
    priority: 10
    match_paths: ["^/Users/you/work/foo-service(/|$)"]
    domains: ["SEC", "PERF"]
    skip_regex: ["^docs/generated/.*", "\\.pb\\.go$"]
    skip_basenames: ["README.md"]
default:
  domains: ["STYLE", "ERROR", "CONFIG"]
```
- `match_paths` 为正则，命中后应用对应 domains/黑名单；`priority` 越小优先级越高。
- `domains` 控制开启哪些标签 agent。
- `skip_regex`/`skip_basenames` 控制过滤文件。

## 规则配置提示
- 规则文档放在 `coding-standards/rules/<lang>/`，并在 Markdown 头部填写 front-matter（`id/title/domains/prompt_hint` 等）。
- 规则文档可被 `code_standard_doc(rule_id)` 工具读取并注入审查流程。
