# 可转债配债

import datetime
import time
import requests
import pandas as pd
import sys
import re

sys.path.append('..')
from configure.util import send_message_via_wechat
from configure.settings import DBSelector
import datetime


def get_page(url):
    data = {'cb_type_Y': 'Y'}
    count = 0
    resp = False
    response = None
    while count < 5:
        try:
            response = requests.post(url, data=data)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            count += 1
        else:
            resp = True
            break

    if not resp:
        raise Exception("Failed to fetch data after multiple attempts")

    result = response.json()
    pages = result.get('rows')
    result_list = []

    for row in pages:
        cell = row['cell']
        stock_code = row['id']
        cell['stock_code'] = str(stock_code)
        result_list.append(cell)
    df = pd.DataFrame(result_list)
    df['progress_nm'] = df['progress_nm'].map(mapper_func)
    return df

def mapper_func(value):
    if re.search('申购',value):
        return '申购'
    else:
        return value

def mysqldumper(df):
    now = datetime.datetime.now()
    current = now.strftime('%Y%m%d %H:%M:%S')
    current_date = now.strftime('%Y%m%d')
    df['crawled_at'] = current
    engine = DBSelector().get_engine('db_bond_rights_offering', type_='qq')
    # print(df.head())
    df.to_sql('rights_offering_{}'.format(current_date), engine, if_exists='replace', index=True)
    with engine.begin() as conn:
        # SQLite语法：给user_id列添加主键
        table_name = 'rights_offering_{}'.format(current_date)
        conn.execute('ALTER TABLE {} ADD PRIMARY KEY (`index`);'.format(table_name))

def main():
    ts = int(time.time() * 1000)

    url = 'https://www.jisilu.cn/data/cbnew/pre_list/?___jsl=LST___t={}'.format(ts)
    try:
        df = get_page(url)
    except Exception as e:
        # wechat 
        send_message_via_wechat(f"可转债配债数据获取失败: {e}")
        return

    mysqldumper(df)


if __name__ == "__main__":
    main()
