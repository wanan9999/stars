import argparse
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import requests

MARKER_START = "<!-- star-history-chart:start -->"
MARKER_END = "<!-- star-history-chart:end -->"


def fetch_all_stargazers(owner: str, repo: str, token: str) -> list[datetime]:
    print(f"正在获取 {owner}/{repo} Star 历史...")
    headers = {
        "Accept": "application/vnd.github.v3.star+json",
        "Authorization": f"Bearer {token}",
    }
    stars: list[datetime] = []
    page = 1
    while True:
        resp = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/stargazers",
            headers=headers,
            params={"per_page": 100, "page": page},
            timeout=30,
        )
        if resp.status_code != 200:
            print(f"请求失败: {resp.status_code} - {resp.text}")
            break
        data = resp.json()
        if not data:
            break
        for item in data:
            stars.append(datetime.fromisoformat(item["starred_at"].replace("Z", "+00:00")))
        print(f"  第 {page} 页 -> 已获取 {len(stars)} 个 Star")
        page += 1
    print(f"总计获取 {len(stars)} 个 Star")
    return stars


def resolve_output_path(output_dir: str | Path, filename: str | None, image_format: str) -> Path:
    if filename and filename.strip():
        name = filename.strip()
        if not Path(name).suffix:
            name = f"{name}.{image_format}"
    else:
        name = f"stars.{image_format}"
    return Path(output_dir) / name


def build_chart_markdown(readme_path: Path, image_path: Path, alt_text: str) -> str:
    readme_dir = readme_path.parent.resolve()
    image_resolved = image_path.resolve()
    try:
        rel = image_resolved.relative_to(readme_dir)
        image_ref = rel.as_posix()
    except ValueError:
        image_ref = image_resolved.as_posix()
    if not image_ref.startswith((".", "/")):
        image_ref = f"./{image_ref}"
    return f"![{alt_text}]({image_ref})"


def update_readme(readme_path: Path, image_path: Path, alt_text: str) -> None:
    readme_path = Path(readme_path)
    markdown_line = build_chart_markdown(readme_path, image_path, alt_text)
    block = f"\n{MARKER_START}\n{markdown_line}\n{MARKER_END}\n"

    content = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    pattern = re.compile(
        rf"\n?{re.escape(MARKER_START)}[\s\S]*?{re.escape(MARKER_END)}\n?",
        re.MULTILINE,
    )
    content = pattern.sub("", content)
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(content.rstrip() + block, encoding="utf-8")
    print(f"已更新 README: {readme_path}")


def generate_modern_chart(
    stars: list[datetime],
    owner: str,
    repo: str,
    output_dir: str | Path = ".",
    language: str = "zh",
    image_format: str = "svg",
    filename: str | None = None,
) -> dict[str, str | int] | None:
    if not stars:
        print("无 Star 数据，跳过图表生成")
        return None

    if image_format not in {"svg", "png"}:
        raise ValueError("image_format must be 'svg' or 'png'")

    df = pd.DataFrame(stars, columns=["starred_at"])
    df["date"] = df["starred_at"].dt.date.astype(str)
    daily = df.groupby("date").size().reset_index(name="daily")
    daily = daily.sort_values("date").reset_index(drop=True)
    daily["total"] = daily["daily"].cumsum()
    total_stars = int(daily["total"].iloc[-1])

    title = f"{owner}/{repo} Star 增长趋势" if language == "zh" else f"{owner}/{repo} Star History"
    y_title = "累计 Star 数" if language == "zh" else "Total Stars"
    alt_text = title

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["total"],
            mode="lines",
            line=dict(color="#238636", width=4, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(35, 134, 54, 0.10)",
        )
    )
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=30, family="Arial Black"),
            x=0.5,
            y=0.96,
        ),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(color="#24292f", family="Segoe UI, Arial, sans-serif"),
        height=650,
        width=1200,
        margin=dict(l=80, r=50, t=100, b=80),
        showlegend=False,
        xaxis=dict(
            title="日期" if language == "zh" else "Date",
            gridcolor="#e4e8eb",
            linecolor="#d0d7de",
            tickfont=dict(size=13),
        ),
        yaxis=dict(
            title=y_title,
            gridcolor="#e4e8eb",
            linecolor="#d0d7de",
            tickfont=dict(size=13),
        ),
    )
    fig.add_annotation(
        x=daily["date"].iloc[-1],
        y=daily["total"].iloc[-1] * 1.02,
        text=f"<b>{total_stars:,}</b>",
        showarrow=False,
        font=dict(size=22, color="#238636"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#238636",
        borderwidth=2,
        borderpad=6,
    )

    image_path = resolve_output_path(output_dir, filename, image_format)
    image_path.parent.mkdir(parents=True, exist_ok=True)
    scale = 2 if image_format == "svg" else 3
    fig.write_image(str(image_path), scale=scale, width=1200, height=650)

    print("图表生成完成")
    print(f"  {image_format.upper()}: {image_path}")

    return {
        "image_path": str(image_path),
        "image_format": image_format,
        "total_stars": total_stars,
        "alt_text": alt_text,
    }


def write_github_outputs(result: dict[str, str | int] | None) -> None:
    output_file = os.getenv("GITHUB_OUTPUT")
    if not output_file or not result:
        return
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"image-path={result['image_path']}\n")
        f.write(f"image-format={result['image_format']}\n")
        f.write(f"total-stars={result['total_stars']}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate GitHub repository star history chart")
    parser.add_argument("--owner", required=True, help="Repository owner")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument("--token", default=None, help="GitHub token (defaults to GITHUB_TOKEN env)")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh", help="Chart language")
    parser.add_argument("--format", choices=["svg", "png"], default="svg", help="Output image format")
    parser.add_argument("--output-dir", default=".", help="Output directory for chart file (default: repo root)")
    parser.add_argument(
        "--filename",
        default="",
        help="Output filename, e.g. stars.svg (default: stars.{format})",
    )
    parser.add_argument("--readme-path", default="README.md", help="README file to append chart markdown")
    parser.add_argument(
        "--commit-to-readme",
        choices=["true", "false"],
        default="true",
        help="Append chart markdown to README (default: true)",
    )
    args = parser.parse_args()

    token = args.token or os.getenv("GITHUB_TOKEN")
    if not token:
        print("请提供 GITHUB_TOKEN 或通过 --token 传入")
        return 1

    stars = fetch_all_stargazers(args.owner, args.repo, token)
    result = generate_modern_chart(
        stars,
        args.owner,
        args.repo,
        args.output_dir,
        args.lang,
        args.format,
        args.filename or None,
    )
    if not result:
        return 1

    if args.commit_to_readme == "true":
        update_readme(
            Path(args.readme_path),
            Path(result["image_path"]),
            str(result["alt_text"]),
        )

    write_github_outputs(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
