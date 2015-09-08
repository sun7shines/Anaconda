# -*- coding:utf8 -*-

import os.path

def get_iso_type():
    #目前为配合u盘安装，如果读不到isotype,默认为vServer类型。
    return 'vBox.x86_64'
