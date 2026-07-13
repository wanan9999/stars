# GitHub Star History Chart

为 GitHub 仓库生成 Star 增长趋势图，并**默认自动追加到 README.md 末尾**以 Markdown 形式渲染展示。

仓库：[wanan9999/stars](https://github.com/wanan9999/stars)

## 功能

- 通过 GitHub API 拉取完整 Star 历史
- 生成 1200×650 趋势图，支持 **SVG / PNG 二选一**（默认 SVG）
- 支持中文 / 英文图表
- **默认**将图表写入 `README.md` 末尾并自动 git commit + push
- 重复运行时会替换已有图表区块，不会无限追加

## 快速使用

```yaml
permissions:
  contents: write

jobs:
  chart:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - name: Generate star history
        uses: wanan9999/stars@v1
        with:
          owner: ${{ github.repository_owner }}
          repo: ${{ github.event.repository.name }}
```

Action 会生成仓库根目录下的 `stars.svg`（或 `stars.png`），并在 README 末尾追加：

```markdown
<!-- star-history-chart:start -->
![owner/repo Star 增长趋势](./stars.svg)
<!-- star-history-chart:end -->
```

自定义输出路径示例：

```yaml
- uses: wanan9999/stars@v1
  with:
    owner: ${{ github.repository_owner }}
    repo: ${{ github.event.repository.name }}
    image-format: png
    output-dir: ./assets
    filename: star-chart.png
```

## Inputs

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `owner` | 是 | — | 仓库所有者 |
| `repo` | 是 | — | 仓库名称 |
| `token` | 否 | `GITHUB_TOKEN` | GitHub Token |
| `language` | 否 | `zh` | 图表语言：`zh` / `en` |
| `image-format` | 否 | `svg` | 输出格式：`svg` / `png` |
| `output-dir` | 否 | `.` | 图表输出目录（默认仓库根目录） |
| `filename` | 否 | `stars.{format}` | 输出文件名，如 `stars.svg` |
| `readme-path` | 否 | `README.md` | 要更新的 README 路径 |
| `commit-to-readme` | 否 | `true` | 是否写入 README 并提交 |
| `commit-message` | 否 | `docs: update star history chart` | Git 提交信息 |

## Outputs

| 输出 | 说明 |
|------|------|
| `image-path` | 生成的图表文件路径 |
| `image-format` | 图表格式（`svg` 或 `png`） |
| `total-stars` | 当前 Star 总数 |

## 调用 Reusable Workflow

```yaml
permissions:
  contents: write

jobs:
  star:
    uses: wanan9999/stars/.github/workflows/generate-star.yml@v1
    with:
      owner: ${{ github.repository_owner }}
      repo: ${{ github.event.repository.name }}
      image-format: svg
```

## 环境要求

- Python **3.12+**
- Workflow 需 `permissions: contents: write` 以支持自动提交
- 使用前需 `actions/checkout@v7`

## 本地运行

```bash
pip install -r requirements.txt
export GITHUB_TOKEN=your_token
python action/main.py \
  --owner octocat \
  --repo Hello-World \
  --format svg \
  --commit-to-readme true
```

## 发布版本

1. 推送代码到 GitHub
2. 创建 Tag：`git tag v1.0.0 && git push origin v1.0.0`
3. 在 Releases 中发布 `v1.0.0`
4. 消费者引用：`uses: wanan9999/stars@v1`

## Token 说明

- 生成**当前仓库**的 Star 图：默认 `GITHUB_TOKEN` 即可
- 生成**其他仓库**或**私有仓库**的 Star 图：需传入具备 `public_repo` 或 `repo` 权限的 PAT

## 项目结构

```
stars/
├── action.yml              # Composite Action 定义
├── action/main.py          # 核心逻辑
├── requirements.txt
├── app.py                  # 本地 CLI 入口
├── examples/               # 消费者 Workflow 示例
└── .github/workflows/      # 自测与 Reusable Workflow
```

## License

MIT
