#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可转债量化分析 - 本地启动入口

无需 MySQL 即可运行演示：拉取集思录指数 + AkShare 可转债行情，并筛选双低标的。
完整定时任务（如 task_double_low.py）仍需配置 config.json 中的数据库与数据源。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def fetch_jsl_index() -> dict:
    import requests

    url = "https://www.jisilu.cn/data/cbnew/cb_index_quote/"
    headers = {
        "Host": "www.jisilu.cn",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.jisilu.cn/data/cbnew/",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_bond_list(limit: int = 20) -> "object":
    import akshare as ak

    df = ak.bond_zh_cov()
    return df.head(limit)


def screen_double_low(df, premium_max: float = 10.0, price_max: float = 120.0, top_n: int = 10):
    import pandas as pd

    rename_map = {
        "债券代码": "可转债代码",
        "债券简称": "可转债名称",
        "转股溢价率": "溢价率",
        "债现价": "可转债价格",
    }
    work = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}).copy()

    for col in ("溢价率", "可转债价格"):
        if col not in work.columns:
            raise KeyError(f"缺少字段 {col}，当前列: {list(work.columns)}")

    work["溢价率"] = pd.to_numeric(work["溢价率"], errors="coerce")
    work["可转债价格"] = pd.to_numeric(work["可转债价格"], errors="coerce")
    filtered = work[
        (work["溢价率"] <= premium_max) & (work["可转债价格"] <= price_max)
    ].copy()
    filtered["双低值"] = filtered["可转债价格"] + filtered["溢价率"]
    cols = [c for c in ("可转债代码", "可转债名称", "可转债价格", "溢价率", "双低值") if c in filtered.columns]
    return filtered.sort_values("双低值").head(top_n)[cols]


def main():
    parser = argparse.ArgumentParser(description="可转债量化分析 - 本地演示")
    parser.add_argument("--top", type=int, default=10, help="双低筛选展示条数")
    parser.add_argument("--premium", type=float, default=10.0, help="溢价率上限(%)")
    parser.add_argument("--price", type=float, default=120.0, help="转债价格上限")
    args = parser.parse_args()

    print("=" * 60)
    print("可转债量化分析 - 本地运行")
    print("=" * 60)

    print("\n[1/2] 集思录可转债等权指数")
    try:
        index = fetch_jsl_index()
        print(f"  当前指数: {index.get('cur_index')}")
        print(f"  涨跌幅:   {index.get('cur_increase_rt')}%")
        print(f"  成交额:   {index.get('amount')} 亿元")
        print(f"  转债数量: {index.get('count')}")
    except Exception as exc:
        print(f"  获取失败: {exc}")

    print("\n[2/2] AkShare 可转债双低筛选")
    try:
        bonds = fetch_bond_list(limit=500)
        picks = screen_double_low(
            bonds,
            premium_max=args.premium,
            price_max=args.price,
            top_n=args.top,
        )
        if picks.empty:
            print("  当前条件下无符合条件的转债")
        else:
            print(picks.to_string(index=False))
    except Exception as exc:
        print(f"  获取失败: {exc}")
        print("  提示: 请确认已安装依赖 (pip install -r requirements.txt)")

    print("\n" + "=" * 60)
    print("更多功能:")
    print("  python run.py                          # 本演示")
    print("  python datahub/cb_index.py             # 指数入库(需 MySQL)")
    print("  python task_weekly_drop.py             # 周跌幅排行(需 MySQL)")
    print("  jupyter notebook analysis/             # Jupyter 分析 notebooks")
    print("=" * 60)


if __name__ == "__main__":
    main()
