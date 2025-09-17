# 热门正股推送

import sys

import pandas as pd
import requests
sys.path.append("..")
from configure.settings import DBSelector
import datetime
from configure.util import send_from_aliyun_ssl
def get_zg_info():
    conn = DBSelector().get_mysql_conn('db_stock','qq')
    cursor = conn.cursor() 
    query = 'select 正股代码,可转债价格,溢价率,剩余规模,剩余时间 from tb_bond_jisilu'
    cursor.execute(query)
    data = cursor.fetchall()
    zg_code_list = []
    price_list =[]
    prenium_rate_list = []
    scale_list = []
    remain_day_list = []
    for item in data:
        zg_code_list.append(item[0])
        price_list.append(round(item[1]))
        prenium_rate_list.append(round(item[2]))
        scale_list.append(round(item[3]))
        remain_day_list.append(item[4])
    df = pd.DataFrame({'zg_code':zg_code_list,'price':price_list,'prenium_rate':prenium_rate_list,'curr_iss_amt':scale_list,'remain_day':remain_day_list})
    return zg_code_list,df

def main():
    zg_code_list,df =  get_zg_info()
    get_hot_dfcf(zg_code_list,df)


def get_hot_dfcf(zg_code_list,df):
    today = datetime.datetime.now().strftime('%Y%m%d')
    conn = DBSelector().get_mysql_conn('db_zdt','qq')
    cursor = conn.cursor()
    query = 'select 代码,名称,涨停统计,入选理由,所属行业 from {}_strong where 代码 in ({})'.format(today,','.join(zg_code_list))
    cursor.execute(query)
    data = cursor.fetchall()
    msg_list = []

    # bond = Bond()
    # bond_df = bond.get_bond_df()
    price_mapper = dict(zip(df['zg_code'], df['price']))
    curr_iss_amt = dict(zip(df['zg_code'], df['curr_iss_amt']))
    prenium_rate = dict(zip(df['zg_code'], df['prenium_rate']))
    remain_day = dict(zip(df['zg_code'], df['remain_day']))
    #
    for item in data:
        code = item[0]
        name = item[1]
        zt_count = item[2]
        reason = item[3]
        industry = item[4]
        obj = {}
        obj['名称'] = name
        obj['涨停'] = zt_count
        obj['现价'] = price_mapper.get(code,0)
        obj['规模']= curr_iss_amt.get(code,0)
        obj['溢价率']=prenium_rate.get(code,0)
        obj['原因'] = reason
        obj['行业'] = industry
        remain_day_value = remain_day.get(code, 0)
        print(code,remain_day_value)
        if curr_iss_amt.get(code,0) > 20:
            continue
        if price_mapper.get(code, 0)>300:
            continue
        if prenium_rate.get(code, 0) > 60:
            continue

        if remain_day_value is None or remain_day_value<1.0:
            continue

        msg_list.append(obj)

    df = pd.DataFrame(msg_list)
    send_content = df.to_html(index=False, border=1, justify='center')
    send_from_aliyun_ssl('{}热门正股'.format(today), send_content, types='html')



if __name__ == "__main__":
    weekday = datetime.datetime.now().weekday()
    if weekday == 5 or weekday == 6:
        # 周六周日不执行
        print('today is weekend')
    else:
        main()
