#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证 MySQL / MongoDB / Tushare 配置是否可用。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check_tushare():
    from configure.settings import get_tushare_pro

    pro = get_tushare_pro()
    df = pro.cb_basic(fields='ts_code,bond_short_name', limit=3)
    print(f'[Tushare] OK，cb_basic 样本 {len(df)} 条')
    return True


def check_mysql():
    from configure.settings import DBSelector

    conn = DBSelector().get_mysql_conn('db_stock', 'qq')
    if conn is None:
        raise RuntimeError('无法连接 MySQL')
    with conn.cursor() as cursor:
        cursor.execute('SELECT DATABASE()')
        cursor.fetchone()
    conn.close()
    print('[MySQL] OK，db_stock 可连接')
    return True


def check_mongo():
    from configure.settings import DBSelector, config

    db_name = config['mongo']['qq'].get('database', 'convertible_bond')
    client = DBSelector().mongo('qq')
    client.admin.command('ping')
    client[db_name].list_collection_names()
    print(f'[MongoDB] OK，数据库 {db_name} 可访问')
    return True


def main():
    print('=' * 60)
    print('convertible_bond 环境检查')
    print('=' * 60)

    ok = True
    for name, fn in (('Tushare', check_tushare), ('MySQL', check_mysql), ('MongoDB', check_mongo)):
        try:
            fn()
        except Exception as exc:
            ok = False
            print(f'[{name}] FAIL: {exc}')

    print('=' * 60)
    if ok:
        print('全部检查通过')
    else:
        print('部分检查未通过，请根据提示修复后重试')
        sys.exit(1)


if __name__ == '__main__':
    main()
