#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""初始化 MySQL 库表与 MongoDB 集合（参考 WorkSpace 基础设施配置）。"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MYSQL_DATABASES = [
    'db_stock',
    'double_low_bond',
    'double_low_full',
    'db_bond_ochl',
    'db_bond_rights_offering',
    'bond_overview',
    'db_bond_daily',
    'db_jisilu',
    'db_daily',
    'db_zdt',
    'db_bond',
]

TB_CB_INDEX_SQL = '''
CREATE TABLE IF NOT EXISTS `tb_cb_index` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `日期` DATE,
  `指数` DOUBLE,
  `成交额(亿元)` DOUBLE,
  `涨跌` DOUBLE,
  `涨跌额` DOUBLE,
  `转债数目` DOUBLE,
  `剩余规模` DOUBLE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''

TB_BOND_AVG_YJL_SQL = '''
CREATE TABLE IF NOT EXISTS `tb_bond_avg_yjl` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `Date` DATE,
  `溢价率均值` DOUBLE,
  `溢价率最大值` DOUBLE,
  `溢价率最小值` DOUBLE,
  `溢价率中位数` DOUBLE,
  `转债数目` INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''

TB_BOND_ANALYSIS_SQL = '''
CREATE TABLE IF NOT EXISTS `tb_bond_analysis` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `date` DATE,
  `转债跌大于正股数量` INT,
  `可转债涨幅大于0` INT,
  `可转债涨幅小于0` INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''

TB_BASIC_INFO_SQL = '''
CREATE TABLE IF NOT EXISTS `tb_basic_info` (
  `code` VARCHAR(10) PRIMARY KEY,
  `name` VARCHAR(32),
  `outstanding` DOUBLE,
  `totals` DOUBLE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
'''


def init_mysql():
    import pymysql
    from configure.settings import DBSelector

    db = DBSelector()
    user, password, host, port = db.config('mysql', 'qq')
    print(f'[MySQL] 连接 {user}@{host}:{port}')

    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        charset='utf8mb4',
    )
    cursor = conn.cursor()

    for database in MYSQL_DATABASES:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{database}` "
            f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        print(f'  ✓ 数据库 {database}')

    conn.commit()

    cursor.execute('USE `db_stock`')
    for ddl in (TB_CB_INDEX_SQL, TB_BOND_AVG_YJL_SQL, TB_BOND_ANALYSIS_SQL, TB_BASIC_INFO_SQL):
        cursor.execute(ddl)
    conn.commit()
    print('  ✓ db_stock 核心表已就绪（tb_cb_index / tb_bond_avg_yjl / tb_bond_analysis / tb_basic_info）')

    cursor.close()
    conn.close()


def init_mongo():
    from configure.settings import DBSelector, config

    profile = config['mongo']['qq']
    db_name = profile.get('database', 'convertible_bond')
    client = DBSelector().mongo('qq')
    db = client[db_name]

    for collection in ('bond_ticks', 'bond_redemption', 'bond_redeem_countdown'):
        if collection not in db.list_collection_names():
            db.create_collection(collection)
        print(f'  ✓ MongoDB 集合 {db_name}.{collection}')

    client.admin.command('ping')
    print(f'[MongoDB] 连接正常，数据库: {db_name}')


def main():
    print('=' * 60)
    print('初始化 convertible_bond 存储')
    print('=' * 60)

    try:
        init_mysql()
    except Exception as exc:
        print(f'[MySQL] 初始化失败: {exc}')
        print('  提示: 请确认 MySQL 已启动（brew services start mysql）')
        sys.exit(1)

    try:
        init_mongo()
    except Exception as exc:
        print(f'[MongoDB] 初始化失败: {exc}')
        sys.exit(1)

    print('=' * 60)
    print('存储初始化完成。下一步: python scripts/sync_bond_jisilu.py')
    print('=' * 60)


if __name__ == '__main__':
    main()
