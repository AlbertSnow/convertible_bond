#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""使用 Tushare Pro 同步可转债行情到 MySQL 表 tb_bond_jisilu。"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from configure.settings import DBSelector, get_tushare_pro


def _strip_code(ts_code: str) -> str:
    return ts_code.split('.')[0] if isinstance(ts_code, str) else ts_code


def _latest_trade_date(pro, pro_api=None) -> str:
    end = datetime.date.today().strftime('%Y%m%d')
    start = (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y%m%d')
    cal = pro.trade_cal(exchange='SSE', start_date=start, end_date=end, is_open='1')
    trade_dates = cal.sort_values('cal_date')['cal_date'].tolist()
    if not trade_dates:
        raise RuntimeError('无法获取交易日历')

    for trade_date in reversed(trade_dates):
        daily = pro.cb_daily(trade_date=trade_date, fields='ts_code')
        if daily is not None and not daily.empty:
            return trade_date

    raise RuntimeError('最近 30 个交易日内均无 cb_daily 数据')


def fetch_bond_snapshot(trade_date: str | None = None) -> pd.DataFrame:
    pro = get_tushare_pro()
    if not trade_date:
        trade_date = _latest_trade_date(pro)

    basic = pro.cb_basic(
        fields='ts_code,bond_short_name,stk_code,stk_short_name,list_date,delist_date,'
               'issue_size,remain_size,conv_price,maturity_date'
    )
    active = basic[basic['delist_date'].isna() | (basic['delist_date'] == '')].copy()

    daily = pro.cb_daily(
        trade_date=trade_date,
        fields='ts_code,trade_date,close,pct_chg,bond_value,bond_over_rate,vol,amount'
    )
    if daily is None or daily.empty:
        raise RuntimeError(f'Tushare cb_daily 无 {trade_date} 数据，请确认交易日或积分权限')

    merged = active.merge(daily, on='ts_code', how='inner')
    merged['可转债代码'] = merged['ts_code'].map(_strip_code)
    merged['可转债名称'] = merged['bond_short_name']
    merged['可转债价格'] = merged['close']
    merged['正股代码'] = merged['stk_code'].map(_strip_code)
    merged['正股名称'] = merged['stk_short_name']
    merged['溢价率'] = merged['bond_over_rate']
    merged['可转债涨幅'] = merged['pct_chg']
    merged['最新转股价'] = merged['conv_price']
    merged['转股价值'] = merged['bond_value']
    merged['评级'] = None
    merged['剩余规模'] = merged['remain_size']
    merged['发行规模'] = merged['issue_size']
    merged['到期时间'] = merged['maturity_date']
    merged['成交额(万元)'] = merged['amount']
    merged['正股涨跌幅'] = None
    merged['正股现价'] = None
    merged['双低'] = merged['可转债价格'] + merged['溢价率']
    merged['强赎日期'] = None
    merged['更新日期'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    columns = [
        '可转债代码', '可转债名称', '可转债价格', '正股名称', '正股代码', '正股现价',
        '正股涨跌幅', '最新转股价', '溢价率', '可转债涨幅', '转股价值', '双低',
        '评级', '剩余规模', '发行规模', '到期时间', '成交额(万元)', '强赎日期', '更新日期',
    ]
    return merged[columns].reset_index(drop=True)


def save_to_mysql(df: pd.DataFrame, remote: str = 'qq'):
    engine = DBSelector().get_engine('db_stock', remote)
    if engine is None:
        raise RuntimeError('无法连接 MySQL db_stock，请先运行 scripts/init_databases.py')

    df.to_sql('tb_bond_jisilu', con=engine, if_exists='replace', index=False)
    print(f'[MySQL] 已写入 db_stock.tb_bond_jisilu，共 {len(df)} 条')


def main():
    trade_date = sys.argv[1] if len(sys.argv) > 1 else None
    print('=' * 60)
    print('Tushare 同步可转债数据 -> tb_bond_jisilu')
    print('=' * 60)

    df = fetch_bond_snapshot(trade_date)
    print(f'交易日: {trade_date or "最新"}，记录数: {len(df)}')
    print(df[['可转债代码', '可转债名称', '可转债价格', '溢价率', '双低']].head(10).to_string(index=False))

    save_to_mysql(df)
    print('=' * 60)
    print('同步完成')
    print('=' * 60)


if __name__ == '__main__':
    main()
