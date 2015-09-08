
from constants import *
import os
import platform
import iutil
import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)
#import init_defaultlocal


def run_cmd(command, params):

    return iutil.execWithRedirect(command, params, root = "/mnt/sysimage/",
                                stdout = "/dev/tty5",
                                stderr = "/dev/tty5")

def init_evn():

    run_cmd("scp", ["/etc/FVIweb/fviweb.sh", "/etc/init.d/"])
    run_cmd("mkdir", ["-p", "/etc/vm_tap", "/etc/storagecfg/", "/etc/sy_conf", "/etc/iscsi"])

def init_service_off():

    svs = ["cgconfig", "multipathd", "dnsmasq", "iscsid", "iscsi", "usbipd", "collectd", "jexec", "monit", "init_vmd.sh",
           "init_sys.sh", "vmd", "webd", "xinetd", "rpcbind", "nfs", "nfslock", "NetworkManager", "ksm",
           "ksmtuned", "gfs2", "rgmanager", "qdiskd", "cman", "openais", "corosync", "pacemaker", "dhcpd"]
    for x in svs:
        run_cmd("chkconfig", [x, "off"])

def init_service_on():

    svs = ["ntpd", "postgresql", "fviweb.sh", "init_business"]
    for x in svs:
        run_cmd("chkconfig", [x, "on"])

def init_business():

    init_evn()
    init_service_off()
    init_service_on()

def func(anaconda):

    os.system('/usr/bin/python /mnt/sysimage/post.py /mnt/sysimage')

    # e.g tmp code for update kernel img,
    init_version = "2.6.32-431.el6.x86_64"
    os.system('mkdir -p /mnt/sysimage/root/tmp/')
    os.system('scp /mnt/sysimage/boot/initramfs-%s.img /mnt/sysimage/root/tmp/' % init_version)
    os.chdir("/mnt/sysimage/root/tmp/")
    os.system('gzip -dc initramfs-%s.img | cpio -id' % init_version)
    os.system('rm -rf /mnt/sysimage/root/tmp/initramfs-%s.img' % init_version)
    if os.access("/mnt/sysimage/version", os.F_OK):
        os.system('scp /mnt/sysimage/version /mnt/sysimage/root/tmp/etc/redhat-release')
        os.system('scp /mnt/sysimage/etc/fronware-release /mnt/sysimage/root/tmp/etc/fronware-release')
    else:
        fd = file("/mnt/sysimage/root/tmp/etc/redhat-release", "w")
        fd.write("FronOS")
        fd.close()
        fd = file("/mnt/sysimage/root/tmp/etc/fronware-release", "w")
        fd.write("vServer FronOS")
        fd.close()
    os.system('find . | cpio -o -H newc | gzip -9 > /mnt/sysimage/root/initramfs-%s.img' % init_version)
    os.system('scp /mnt/sysimage/root/initramfs-%s.img /mnt/sysimage/boot/initramfs-%s.img' % (init_version, init_version))
    os.system('rm -rf /mnt/sysimage/root/tmp/ /mnt/sysimage/root/initramfs-%s.img' % init_version)
    f = file("/mnt/sysimage/etc/SerialNumber", "w")
    f.write("%s" % anaconda.sn)
    f.close()
    #os.system('echo %s > /mnt/sysimage/root/tmp/etc/redhat-release' % anaconda.sn)

    run_cmd("python", ["/etc/systemupdate/database/init_db.py"])
    run_cmd("python", ["/etc/init_defaultlocal.py"])
    # e.g only for vsva, must be running after post.py
    run_cmd("python", ["/vsvapost.py"])

    init_business()

    os.system("rm -f /mnt/sysimage/lib/modules/*/kernel/net/bridge/bridge.ko")

