# -*-coding=utf-8-*-
# 常用的配置信息
import os
import json
from functools import lru_cache
from urllib.parse import quote_plus


def get_config_data(config_file='config.json'):
    json_file = os.path.join(os.path.dirname(__file__), config_file)
    with open(json_file, 'r', encoding='utf8') as f:
        _config = json.load(f)
        return _config


config = get_config_data()


def config_dict(*args):
    result = config
    for arg in args:
        try:
            result = result[arg]
        except Exception:
            print('找不到对应的key')
            return None

    return result


def get_tushare_token():
    """优先从环境变量 TUSHARE_TOKEN 读取，其次 config.json 中的 ts_token。"""
    token = os.environ.get('TUSHARE_TOKEN') or config.get('ts_token')
    if not token:
        raise RuntimeError(
            '未配置 Tushare Token：请设置环境变量 TUSHARE_TOKEN，'
            '或在 configure/config.json 中填写 ts_token'
        )
    return token


@lru_cache(maxsize=1)
def get_tushare_pro():
    import tushare as ts

    token = get_tushare_token()
    ts.set_token(token)
    return ts.pro_api()


def _resolve_db_profile(db_type, local):
    """合并 config.json 与环境变量中的数据库连接信息。"""
    profile = dict(config[db_type][local])
    env_prefix = db_type.upper()
    profile['user'] = os.environ.get(f'{env_prefix}_USER', profile.get('user', ''))
    profile['password'] = os.environ.get(f'{env_prefix}_PASSWORD', profile.get('password', ''))
    profile['host'] = os.environ.get(f'{env_prefix}_HOST', profile.get('host', '127.0.0.1'))
    profile['port'] = int(os.environ.get(f'{env_prefix}_PORT', profile.get('port', 3306 if db_type == 'mysql' else 27017)))
    return profile


class DBSelector(object):
    '''
    数据库选择类
    '''

    def __init__(self):
        self.json_data = config

    def config(self, db_type='mysql', local='qq'):
        profile = _resolve_db_profile(db_type, local)
        return profile['user'], profile['password'], profile['host'], profile['port']

    def _mysql_url(self, db, type_='qq'):
        user, password, host, port = self.config(db_type='mysql', local=type_)
        auth = f'{quote_plus(user)}:{quote_plus(password)}' if password else quote_plus(user)
        return f'mysql+pymysql://{auth}@{host}:{port}/{db}?charset=utf8mb4'

    def get_engine(self, db, type_='qq'):
        from sqlalchemy import create_engine
        try:
            engine = create_engine(self._mysql_url(db, type_))
        except Exception as e:
            print(e)
            return None
        return engine

    def get_mysql_conn(self, db, type_='qq', use_dict=False):
        import pymysql
        user, password, host, port = self.config(db_type='mysql', local=type_)
        try:
            kwargs = dict(
                host=host,
                port=port,
                user=user,
                password=password,
                database=db,
                charset='utf8mb4',
            )
            if use_dict:
                kwargs['cursorclass'] = pymysql.cursors.DictCursor
            conn = pymysql.connect(**kwargs)
        except Exception as e:
            print(e)
            return None
        else:
            return conn

    def mongo(self, location_type='qq', async_type=False):
        '''
        async_type: 异步
        '''
        profile = _resolve_db_profile('mongo', location_type)
        user = profile.get('user', '')
        password = profile.get('password', '')
        host = profile['host']
        port = profile['port']
        database = profile.get('database', 'convertible_bond')
        auth_source = profile.get('auth_source', 'admin')

        if user:
            auth = f'{quote_plus(user)}:{quote_plus(password)}'
            connect_uri = (
                f'mongodb://{auth}@{host}:{port}/{database}'
                f'?authSource={auth_source}'
            )
        else:
            connect_uri = f'mongodb://{host}:{port}/{database}'

        if async_type:
            from motor.motor_asyncio import AsyncIOMotorClient
            client = AsyncIOMotorClient(connect_uri)
        else:
            import pymongo
            client = pymongo.MongoClient(connect_uri)
        return client


if __name__ == '__main__':
    pass
