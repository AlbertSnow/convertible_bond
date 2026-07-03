# -*- coding: utf-8 -*-
# @Time : 2021/4/2 20:02
# @File : Base.py
# @Author : Rocky C@www.30daydo.com

import sys

sys.path.append('..')
from configure.settings import get_tushare_pro

pro = get_tushare_pro()
__all__ = ('pro',)
