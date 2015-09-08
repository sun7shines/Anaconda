# -*- coding: utf-8 -*-

import os
import time
import syslog
import commands

import devices_info

def cmd_exe(cmd):
    
    flag , output = commands.getstatusoutput(cmd)
    otx = []
    if output.strip():
        otx = output.split('\n')
    if flag is 0:
        return (not flag,{'stdout':otx,'stderr':[]})
    else :
        return (not flag,{'stdout':[],'stderr':otx})

def get_pvs():

    pvs = []
    #local in /usr/sbin/pvdisplay
    cmd = "/usr/sbin/pvdisplay" 
    output = cmd_exe(cmd)
    if not output[0]:
        return pvs
    
    is_pv_flag = False
    for line in output[1]["stdout"]:
        if "PV Name" in line:
            is_pv_flag = True
            pv = {}
            pv["device"] = line.strip().split()[-1]
            pv["vgname"] = ""
            pvs.append(pv)
            continue
        if is_pv_flag and "VG Name" in line:
            is_pv_flag = False
            if len(line.split()) == 3:
                pv["vgname"] = line.strip().split()[-1]
    return pvs

def get_harddisklst():
    
    device_obj = devices_info.StorageDevice()
    devices_ptinfo = device_obj.get_devices_ptinfo()
    
    
    del_wwids = []
    exist_wwids = []
    for x in devices_ptinfo:
        x["wwid"] = get_harddisk_wwid(x["hard_disk"])
        if x["wwid"]:
            if x["wwid"] in del_wwids:
                # 第二次重复出现同样的WWID
                continue
            if x["wwid"] in exist_wwids:
                # 第一次重复出现同样的WWID
                del_wwids.append(x["wwid"])
                continue
            # 无重复的WWID
            exist_wwids.append(x["wwid"])
    
    for wwid in del_wwids:
        del_hds = []
        true_hd = ""
        for x in devices_ptinfo:
            if x["wwid"] != wwid:
                continue
            if x["hard_disk"].startswith("/dev/mapper/"):
                true_hd = x["hard_disk"]
                continue
            del_hds.append(x)
        if true_hd:
            # 有映射设备的硬盘重复
            for x in del_hds:
                if x in devices_ptinfo:
                    devices_ptinfo.remove(x)
        else:
            # 无映射设备的硬盘重复
            num = 0
            for x in del_hds:
                if num == 0:
                    # 顺位第一个硬盘命名保留
                    continue
                num += 1
                if x in devices_ptinfo:
                    devices_ptinfo.remove(x)
                    
    return devices_ptinfo

def get_harddisk_wwid(hdname):
    
    # e.g get wwid
    cmd = "/lib/udev/scsi_id --whitelisted --device="+hdname
    result = cmd_exe(cmd)
    wwid = ""
    if result[0]:
        if result[1]["stdout"]:
            wwid = result[1]["stdout"][0].strip()
    return wwid

def delete_vgs(destroyDisks):

    pvs = get_pvs()
    devices = get_harddisklst()

    harddisk = ''

    for pv in pvs: 
        for dev in devices:
            if pv['device'] in dev['partitions']:
                harddisk = dev['hard_disk']
                if harddisk and harddisk.strip().split('/')[-1] in destroyDisks:
                    cmd = 'vgremove -f ' + pv['vgname'].strip()
                    os.system(cmd)
                    cmd = 'pvremove -ff ' + pv['device'].strip()
                    os.system(cmd)

    return ''

def destroy_disks(destroyDisks):

    delete_vgs(destroyDisks)
    for xxdisk in destroyDisks:
        cmd = 'dd if=/dev/zero of=/dev/%s bs=512 count=1 ' % (xxdisk)
        os.system(cmd)
  
