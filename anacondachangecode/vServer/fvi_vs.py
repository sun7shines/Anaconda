# -*- coding:utf8 -*-

import os.path
def get_iso_type():
    #目前为配合u盘安装，如果读不到isotype,默认为vServer类型。
    #使用u盘安装后，u盘的挂载目录会改变,，不再是/mnt/sysimage/，会防止这种情况发生，依赖其他的软件包，改为
    #这种方式，直接使用FW方式
    return 'vServer.x86_64'
