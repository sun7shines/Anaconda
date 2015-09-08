# -*- coding:utf8 -*-
# network.py - network configuration install data
#
# Matt Wilson <ewt@redhat.com>
# Erik Troan <ewt@redhat.com>
# Mike Fulbright <msf@redhat.com>
# Brent Fox <bfox@redhat.com>
#
# Copyright 2001-2003 Red Hat, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# library public license.
#
# You should have received a copy of the GNU Library Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import string
import isys
import iutil
import socket
import os
#import kudzu
import time
import dbus
from flags import flags

import logging
log = logging.getLogger("anaconda")

from simpleconfig import SimpleConfigFile

import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)


class IPError(Exception):
    pass

class IPMissing(Exception):
    pass

def inStrRange(v, s):
    if string.find(s, v) == -1:
	return 0
    else:
	return 1

def sanityCheckHostname(hostname):
    if len(hostname) < 1:
	return None

    if len(hostname) > 64:
	#return _("Hostname must be 64 or less characters in length.")
        return _(u"主机名的长度必须小于或等于64。")
    
    if not inStrRange(hostname[0], string.ascii_letters):
	#return _("Hostname must start with a valid character in the range "
	#	 "'a-z' or 'A-Z'")
        return _(u"主机名必须以英文字母 'a-z' 或 ‘A-Z’ 开头。")

    for i in range(1, len(hostname)):
	if not inStrRange(hostname[i], string.ascii_letters+string.digits+".-"):
	    #return _("Hostnames can only contain the characters 'a-z', 'A-Z', '-', or '.'")
            return _(u"主机名只能包含字符 ‘a-z’，‘A-Z’ 或 ‘-’。")
    if hostname.find('.')!=-1:
        return _(u"主机名不能包含“.”。")
      
    return None
	    

def networkDeviceCheck(anaconda):
    devs = anaconda.id.network.available()
    if not devs:
        anaconda.dispatch.skipStep("network")


# return if the device is of a type that requires a ptpaddr to be specified
def isPtpDev(devname):
    if (devname.startswith("ctc") or devname.startswith("iucv")):
        return 1
    return 0

# determine whether any active at boot devices are using dhcp
def anyUsingDHCP(devices, anaconda):
    for dev in devices.keys():
        bootproto = devices[dev].get("bootproto").lower()
        if bootproto and bootproto in ['query', 'dhcp']:
            if anaconda.rescue:
                return True
            else:
                onboot = devices[dev].get("onboot")
                if onboot and onboot != "no":
                    return True
    return False

# sanity check an IP string.
def sanityCheckIPString(ip_string):
    if ip_string.strip() == "":
        raise IPMissing, _("IP address is missing.")

    if ip_string.find(':') == -1 and ip_string.find('.') > 0:
        family = socket.AF_INET
        errstr = _("IPv4 addresses must contain four numbers between 0 and 255, separated by periods.")
    elif ip_string.find(':') > 0 and ip_string.find('.') == -1:
        family = socket.AF_INET6
        errstr = _("'%s' is not a valid IPv6 address.") % ip_string
    else:
        raise IPError, _("'%s' is an invalid IP address.") % ip_string

    try:
        socket.inet_pton(family, ip_string)
    except socket.error:
        raise IPError, errstr

def hasActiveNetDev():
    # try to load /tmp/netinfo and see if we can sniff out network info
    netinfo = Network()
    for dev in netinfo.netdevices.keys():
        try:
            ip = isys.getIPAddress(dev)
        except Exception, e:
            log.error("Got an exception trying to get the ip addr of %s: "
                      "%s" %(dev, e))
            continue
        if ip == '127.0.0.1' or ip is None:
            continue
        if isys.getLinkStatus(dev):
            return True
    return False

class NetworkDevice(SimpleConfigFile):
    def __str__(self):
        s = ""
        s = s + "DEVICE=" + self.info["DEVICE"] + "\n"
        keys = self.info.keys()
        keys.sort()
        keys.remove("DEVICE")
        if "DESC" in keys:
            keys.remove("DESC")
        if "KEY" in keys:
            keys.remove("KEY")

        # Don't let onboot be turned on unless we have config information
        # to go along with it
        if self.get('bootproto').lower() != 'dhcp' and not self.get('ipaddr'):
            forceOffOnBoot = 1
        else:
            forceOffOnBoot = 0

        if self.get('USEIPV6'):
            forceOffOnBoot = 0

        onBootWritten = 0
        for key in keys:
            if key in ("USEIPV4", "USEIPV6"): # XXX: these are per-device, but not written out
                continue
            if key == 'ONBOOT' and forceOffOnBoot:
                s = s + key + "=" + 'no' + "\n"
            # make sure we include autoneg in the ethtool line
            elif key == 'ETHTOOL_OPTS' and self.info[key].find("autoneg")== -1:
                s = s + key + """="autoneg off %s"\n""" % (self.info[key])
            elif self.info[key] is not None:
                s = s + key + "=" + self.info[key] + "\n"

            if key == 'ONBOOT':
                onBootWritten = 1
                if forceOffOnBoot or self.info[key].lower() == 'no':
                    s = s + "HOTPLUG=no\n"

        if not onBootWritten:
            s = s + 'ONBOOT=no\n'
            s = s + "HOTPLUG=no\n"

        return s

    def __init__(self, dev):
        self.info = { "DEVICE" : dev,
                      "ONBOOT": "no" }
	if dev.startswith('ctc'):
	    self.info["TYPE"] = "CTC"
	elif dev.startswith('iucv'):
	    self.info["TYPE"] = "IUCV"

class Network:
    def __init__(self):
        self.ksdevice = None
	self.firstnetdevice = None
        self.netdevices = {}
        self.gateway = ""
        self.primaryNS = ""
        self.secondaryNS = ""
        self.domains = []
	self.isConfigured = 0
        self.hostname = "localhost"
        self.query = False

        self.dve_dvelist = [] 
        self.br0_ip = ""
        self.br0_pr = ""
        self.r_button_dhcp = False

        # if we specify a hostname and are using dhcp, do an override
        # originally used by the gui but overloaded now
	# we also test in places if the hostname is localhost.localdomain
	# to see if its been override. Need some consolidation in future.
	self.overrideDHCPhostname = 0
          
        self.hostname_dhcp=True
        if flags.rootpath:
            self.isConfigured = 1

        try:
            f = open("/tmp/netinfo", "r")
        except:
            pass
        else:
            lines = f.readlines()
	    f.close()
            info = {}
	    self.isConfigured = 1
            for line in lines:
                netinf = string.splitfields(line, '=')
                if len(netinf) >= 3:
                    info[netinf[0]] = '='.join([string.strip(s) for s in netinf[1:]])
                elif len(netinf) >= 2:
                    info [netinf[0]] = string.strip(netinf[1])
            self.netdevices [info["DEVICE"]] = NetworkDevice(info["DEVICE"])
            self.firstnetdevice = info["DEVICE"]
            for key in ("IPADDR", "NETMASK", "BOOTPROTO", "ONBOOT", "MTU",
                        "NETTYPE", "SUBCHANNELS", "PORTNAME", "CTCPROT",
                        "PEERID", "ESSID", "KEY", "IPV6ADDR", "IPV6_AUTOCONF",
                        "OPTIONS", "ARP", "MACADDR"):
                if info.has_key(key):
                    self.netdevices [info["DEVICE"]].set((key, info[key]))

            self.netdevices [info["DEVICE"]].set(('useIPv4', flags.useIPv4))
            self.netdevices [info["DEVICE"]].set(('useIPv6', flags.useIPv6))

            if info.has_key("GATEWAY"):
                self.gateway = info["GATEWAY"]
            if info.has_key("DOMAIN"):
                self.domains.append(info["DOMAIN"])
            if info.has_key("HOSTNAME"):
                self.hostname = info["HOSTNAME"]
	    if not info.has_key("BOOTPROTO"):
                if not info.has_key("IPADDR"):
                    self.netdevices [info["DEVICE"]].set(('useIPv4', False))
                if not (info.has_key("IPV6ADDR") and info.has_key("IPV6_AUTOCONF")):
                    self.netdevices [info["DEVICE"]].set(('useIPv6', False))

	try:
	    f = open("/etc/resolv.conf", "r")
	except:
	    pass
	else:
	    lines = f.readlines()
	    f.close()
	    for line in lines:
		resolv = string.split(line)
		if resolv and resolv[0] == 'nameserver':
		    if self.primaryNS == "":
			self.primaryNS = resolv[1]
		    elif self.secondaryNS == "":
			self.secondaryNS = resolv[1]

	# now initialize remaining devices
	# XXX we just throw return away, the method initialize a
	# object member so we dont need to
	available_devices = self.available()

	if len(available_devices) > 0:
	    # set first device to start up onboot
	    oneactive = 0
	    for dev in available_devices.keys():
		try:
		    if available_devices[dev].get("onboot") == "yes":
			oneactive = 1
			break
		except:
		    continue

	    if not oneactive:
		self.netdevices[self.firstnetdevice].set(("onboot", "yes"))

            for device in self.netdevices.keys():
                hwaddr = isys.getMacAddress(device)
                if hwaddr and hwaddr != "00:00:00:00:00:00" and hwaddr != "ff:ff:ff:ff:ff:ff":
                    self.netdevices[device].set(("hwaddr", hwaddr))
	    # assign description to each device based on kudzu information
#	    probedevs = kudzu.probe(kudzu.CLASS_NETWORK, kudzu.BUS_UNSPEC, 0)
#	    for netdev in probedevs:
#		device = netdev.device
#		if device in self.netdevices.keys():
#		    desc = netdev.desc
#		    if desc is not None and len(desc) > 0:
#			self.netdevices[device].set(("desc", desc))

                    # hwaddr for qeth doesn't make sense (#135023)
#                    if netdev.driver == "qeth":
#                        continue
                    # add hwaddr
#                    hwaddr = isys.getMacAddress(device)
#                    if hwaddr and hwaddr != "00:00:00:00:00:00" and hwaddr != "ff:ff:ff:ff:ff:ff":
#                        self.netdevices[device].set(("hwaddr", hwaddr))

    def getDevice(self, device):
	return self.netdevices[device]

    def getFirstDeviceName(self):
	return self.firstnetdevice

    def available(self):
        ksdevice = None
        if flags.cmdline.has_key("ksdevice"):
            ksdevice = flags.cmdline["ksdevice"]

        f = open("/proc/net/dev")
        lines = f.readlines()
        f.close()
        # skip first two lines, they are header
        lines = lines[2:]
        for line in lines:
            dev = string.strip(line[0:6])
            if dev != "lo" and dev[0:3] != "sit" and not self.netdevices.has_key(dev):
		if self.firstnetdevice is None:
		    self.firstnetdevice = dev

                self.netdevices[dev] = NetworkDevice(dev)

                try:
                    hwaddr = isys.getMacAddress(dev)
                    if rhpl.getArch() != "s390" and hwaddr and hwaddr != "00:00:00:00:00:00" and hwaddr != "ff:ff:ff:ff:ff:ff":
                        self.netdevices[dev].set(("hwaddr", hwaddr))

                        if not ksdevice:
                            continue
                        if ksdevice == 'link' and isys.getLinkStatus(dev):
                            self.ksdevice = dev
                        elif ksdevice == dev:
                            self.ksdevice = dev
                        elif ksdevice.find(':') != -1:
                            if ksdevice.upper() == hwaddr:
                                self.ksdevice = dev
                except Exception, e:
                    log.error("exception getting mac addr: %s" %(e,))

        if ksdevice and self.netdevices.has_key(ksdevice):
            self.firstnetdevice = ksdevice

        return self.netdevices

    def setHostname(self, hn):
	self.hostname = hn

    def setDNS(self, ns):
        dns = ns.split(',')
        if len(dns) >= 1:
            self.primaryNS = dns[0]
        if len(dns) >= 2:
            self.secondaryNS = dns[1]

    def setGateway(self, gw):
        self.gateway = gw

    def lookupHostname(self):
	# can't look things up if they don't exist!
	if not self.hostname or self.hostname == "localhost":
            return None
	if not self.primaryNS:
            return
        myns = self.primaryNS

	if not self.isConfigured:
	    for dev in self.netdevices.values():
                usemethod = dev.get('bootproto').lower()

                while True:
                    if (usemethod == "ibft" and dev.get('onboot') == "yes"):
                        try:
                            if anaconda.id.iscsi.fwinfo["iface.bootproto"].lower() == "dhcp":
                                usemethod = "dhcp"
                                continue
                            else:
                                hwaddr = isys.getMacAddress(dev)
                                if hwaddr != anaconda.id.iscsi.fwinfo["iface.hwaddress"]:
                                    log.error("The iBFT configuration does not belong to device %s,"
                                              "falling back to dhcp", dev.get('device'))
                                    usemethod = "dhcp"
                                    continue

                                isys.configNetDevice(dev.get('device'),
                                                     anaconda.id.iscsi.fwinfo["iface.ipaddress"],
                                                     anaconda.id.iscsi.fwinfo["iface.subnet_mask"],
                                                     anaconda.id.iscsi.fwinfo["iface.gateway"])
                                self.isConfigured = 1
                        except:
                            log.error("failed to configure network device %s using "
                                      "iBFT information, falling back to dhcp", dev.get('device'))
                            usemethod = "dhcp"
                            continue
                    elif (usemethod == "dhcp" and
                        dev.get('onboot') == "yes"):
                        ret = isys.dhcpNetDevice(dev.get('device'), dev.get('dhcpclass'))
#                        if ret is None:
#                            continue
#                        myns = ret
                        self.isConfigured = 1
                        break
                    elif (dev.get('ipaddr') and dev.get('netmask') and
                          self.gateway is not None and dev.get('onboot') == "yes"):
                        try:
                            isys.configNetDevice(dev.get('device'),
                                                 dev.get('ipaddr'),
                                                 dev.get('netmask'),
                                                 self.gateway)
                            self.isConfigured = 1
                            break
                        except SystemError:
                            log.error("failed to configure network device %s when "
                                      "looking up host name", dev.get('device'))

                    #try it only once
                    break

            if self.isConfigured and not flags.rootpath:
                f = open("/etc/resolv.conf", "w")
                f.write("nameserver %s\n" % myns)
                f.close()
                isys.resetResolv()
                isys.setResolvRetry(1)

	if not self.isConfigured:
            log.warning("no network devices were available to look up host name")
            return None

	try:
            (family, socktype, proto, canonname, sockaddr) = \
                socket.getaddrinfo(self.hostname, None, socket.AF_INET)[0]
            (ip, port) = sockaddr
	except:
            try:
                (family, socktype, proto, canonname, sockaddr) = \
                    socket.getaddrinfo(self.hostname, None, socket.AF_INET6)[0]
                (ip, port, flowinfo, scopeid) = sockaddr
            except:
	        return None

	return ip

    def nameservers(self):
        return (self.primaryNS, self.secondaryNS)

    def dnsString(self):
        str = ""
        for ns in self.nameservers():
            if not ns:
                continue
            if str: str = str + ","
            str = str + ns
        return str
            

    def writeKS(self, f):
	devNames = self.netdevices.keys()
	devNames.sort()
    
        if len(devNames) == 0:
            return

        for devName in devNames:
            dev = self.netdevices[devName]

            if dev.get('bootproto').lower() == 'dhcp' or  dev.get('bootproto').lower() == 'ibft' or dev.get('ipaddr'):
                f.write("network --device %s" % dev.get('device'))

                if dev.get('MTU') and dev.get('MTU') != 0:
                    f.write(" --mtu=%s" % dev.get('MTU'))

		onboot = dev.get("onboot")
		if onboot and onboot == "no":
		    f.write(" --onboot no")
                if dev.get('bootproto').lower() == 'dhcp':
                    f.write(" --bootproto dhcp")
                    if dev.get('dhcpclass'):
			f.write(" --dhcpclass %s" % dev.get('dhcpclass'))
		    if self.overrideDHCPhostname:
			if (self.hostname and
			    self.hostname != "localhost"):
			    f.write(" --hostname %s" % self.hostname)
                elif dev.get('bootproto').lower() == 'ibft':
                    f.write(" --bootproto ibft")
                else:
                    f.write(" --bootproto static --ip %s --netmask %s" % 
                       (dev.get('ipaddr'), dev.get('netmask')))

		    if self.gateway is not None:
			f.write(" --gateway %s" % (self.gateway,))

		    if self.dnsString():
                        f.write(" --nameserver %s" % (self.dnsString(),))
                        
		    if (self.hostname and
			self.hostname != "localhost"):
			f.write(" --hostname %s" % self.hostname)

                f.write("\n");

    def write(self, instPath=None, devices=None):

#        import pdb;pdb.set_trace()
        if devices is None:
            devices = self.netdevices.values()

        if len(devices) == 0:
            return

        # make sure the directory exists
        if not os.path.isdir("%s/etc/sysconfig/network-scripts" %(instPath,)):
            iutil.mkdirChain("%s/etc/sysconfig/network-scripts" %(instPath,))

        # /etc/sysconfig/network-scripts/ifcfg-*
        useIPv6 = "no"
#        for dev in self.netdevices.values():
        for dev in devices:
            device = dev.get("device")
            fn = "%s/etc/sysconfig/network-scripts/ifcfg-%s" % (instPath,
                                                                device)
            f = open(fn, "w")
            os.chmod(fn, 0644)
            if len(dev.get("DESC")) > 0:
                f.write("# %s\n" % (dev.get("DESC"),))

            # if bootproto is dhcp, unset any static settings (#218489)
            if dev.get('BOOTPROTO').lower() in ['dhcp', 'ibft']:
                dev.unset('IPADDR')
                dev.unset('NETMASK')
                dev.unset('GATEWAY')

            # handle IPv6 settings correctly for the ifcfg file
            ipv6addr = dev.get('IPV6ADDR').lower()
            ipv6prefix = dev.get('IPV6PREFIX').lower()

            dev.unset('IPV6ADDR')
            dev.unset('IPV6PREFIX')

            if ipv6addr == 'dhcp':
                dev.set(('IPV6INIT', 'yes'))
            elif ipv6addr != '' and ipv6addr is not None:
                dev.set(('IPV6INIT', 'yes'))

                if ipv6prefix != '' and ipv6prefix is not None:
                    dev.set(('IPV6ADDR', ipv6addr + '/' + ipv6prefix))
                else:
                    dev.set(('IPV6ADDR', ipv6addr))

            if dev.get('IPV6_AUTOCONF').lower() == 'yes':
                dev.set(('IPV6INIT', 'yes'))

            f.write(str(dev))

            # write out the hostname as DHCP_HOSTNAME if given (#81613)
            if (dev.get('bootproto').lower() == 'dhcp' and self.hostname and
                self.overrideDHCPhostname):
                f.write("DHCP_HOSTNAME=%s\n" %(self.hostname,))
            if dev.get('dhcpclass'):
                f.write("DHCP_CLASSID=%s\n" % dev.get('dhcpclass'))

            if dev.get('MTU') and dev.get('MTU') != 0:
                f.write("MTU=%s\n" % dev.get('MTU'))

            f.close()

            if dev.get("key"):
                fn = "%s/etc/sysconfig/network-scripts/keys-%s" % (instPath,
                                                                   device)
                f = open(fn, "w")
                os.chmod(fn, 0600)
                f.write("KEY=%s\n" % dev.get('key'))
                f.close()

            if dev.get("useIPv6"):
                useIPv6 = "no"

#        for dev in self.netdevices.values():#==================================
#            device = dev.get("device")
#            fn = "%s/etc/sysconfig/network-scripts/ifcfg-%s" % (instPath,device

        for dev in self.netdevices.values():
            device = dev.get("device")
            dv = str(dev)
            dv_ls = dv.split("\n")
            dv_ll = ""
            for i in range(0,len(dv_ls)):
                if "HWADDR" in dv_ls[i]:
                    dv_ll = dv_ls[i]
            fn = "%s/etc/sysconfig/network-scripts/ifcfg-%s"%(instPath,device)
            f = open(fn)
            dh_num = 0
            while True:
                line = f.readline()
                if len(line) == 0:
                    break
                if "dhcp" in line:
                    dh_num = 1
                    break
            f.close()
            if dh_num == 1:
                conf = "DEVICE=%s\nTYPE=Ethernet\nONBOOT=yes\n%s\nBOOTPROTO=none\nUSERCTL=no\n" % (device, dv_ll)
                f = open(fn, "w")
                os.chmod(fn, 0644)
                if len(dev.get("DESC")) > 0:
                    f.write("# %s\n" % (dev.get("DESC"),))
                f.write(conf)
                f.close()

        for dev in self.netdevices.values():
            device = dev.get("device")
            dv = str(dev)
            dv_ls = dv.split("\n")
            dv_ll = ""
            for i in range(0,len(dv_ls)):
                if "HWADDR" in dv_ls[i]:
                    dv_ll = dv_ls[i]
#            dv_device_ls = dv_ls[0].split("=")
#            dv_device = dv_device_ls[1]
            if device in self.dve_dvelist:

#        for device in self.dve_dvelist: ######################
                fn = "%s/etc/sysconfig/network-scripts/ifcfg-%s" % (instPath,device)
                if len(self.dve_dvelist) > 1:
                    conf = "DEVICE=%s\nTYPE=Ethernet\nUSERCTL=no\n%s\nONBOOT=yes\nMASTER=bond0\nSLAVE=yes\nBOOTPROTO=none\n"%(device, dv_ll)
                else:
                    conf = "DEVICE=%s\nTYPE=Ethernet\nUSERCTL=no\n%s\nONBOOT=yes\nBOOTPROTO=none\nBRIDGE=switch0\n"%(device, dv_ll)
                f = open(fn, "w")
                os.chmod(fn, 0644)
                if len(dev.get("DESC")) > 0:
                    f.write("# %s\n" % (dev.get("DESC"),))
                f.write(conf)
                f.close()
        if len(self.dve_dvelist) > 1:
            fn = "%s/etc/sysconfig/network-scripts/ifcfg-bond0"%instPath
            conf = "DEVICE=bond0\nTYPE=Ethernet\nONBOOT=yes\nBOOTPROTO=none\nUSERCTL=no\nBRIDGE=switch0\n"
            f = open(fn, "w")
            os.chmod(fn, 0644)
            if len(dev.get("DESC")) > 0:
                f.write("# %s\n" % (dev.get("DESC"),))
            f.write(conf)
            f.close()

            fn = "%s/etc/modprobe.d/bond.conf"%instPath
            strs = "alias bond0 bonding\noptions bond0 mode=active-backup miimon=100\n"
            f = open(fn, "w")
            os.chmod(fn, 0644)
            f.write(strs)
            f.close()

        if len(self.dve_dvelist) > 0:
            fn = "%s/etc/sysconfig/network-scripts/ifcfg-switch0"%instPath
            IPADDR = self.br0_ip#"192.168.1.50"####################
            NETMASK = self.br0_pr#"255.255.255.0"##################
            if NETMASK == "24":
                NETMASK = "255.255.255.0"
            if not self.r_button_dhcp:
                if len(IPADDR) > 0 and len(NETMASK) > 0:
                    ir = IPADDR.split(".")
                    nk = NETMASK.split(".")
                    network = []
                    for i in range(0,len(ir)):
                        network.append(str(int(ir[i])&int(nk[i])))
                    NETWORK = ".".join(network)
                    for i in range(0, len(ir)):
                        if int(nk[i]) > 0:
                            nk[i] = "0"
                        else:
                            nk[i] = "255"
                    bt = []
                    for i in range(0, len(ir)):
                        bt.append(str(int(nk[i])|int(network[i])))
                    BROADCAST = ".".join(bt)
                    if self.gateway:
                        gateway_l = "GATEWAY=%s"%self.gateway
                    else:
                        gateway_l = ""
                    conf = "DEVICE=switch0\nIPADDR=%s\nNETMASK=%s\nNETWORK=%s\nBROADCAST=%s\nONBOOT=yes\nBOOTPROTO=static\nUSERCTL=no\n%s\n"%(IPADDR, NETMASK, NETWORK, BROADCAST, gateway_l)
                else:
                    conf = "DEVICE=switch0\nONBOOT=yes\nBOOTPROTO=dhcp\nUSERCTL=no\n"
            else:
                conf = "DEVICE=switch0\nONBOOT=yes\nBOOTPROTO=dhcp\nUSERCTL=no\n"

            f = open(fn, "w")
            os.chmod(fn, 0644)
            if len(dev.get("DESC")) > 0:
                f.write("# %s\n" % (dev.get("DESC"),))
            f.write(conf)
            f.close()

        #===============================================================
        # write hostname file

        #f = file("%s/hostname" %(instPath) ,"w")
        #f.write("%s %s\n127.0.0.1  localhost.localdomain  localhost\n::1  localhost6.localdomain6 localhost6" %(self.ipv4_addr,self.newHostname))
        #f.close()
        #==========================================================


        # /etc/sysconfig/network
        f = open(instPath + "/etc/sysconfig/network", "w")
        f.write("NETWORKING=yes\n")
        f.write("NETWORKING_IPV6=%s\n" % (useIPv6,))
        f.write("HOSTNAME=")

        # use instclass hostname if set(kickstart) to override
        if self.hostname:
            f.write(self.hostname + "\n")
        else:
            f.write("localhost\n")
        if self.gateway:
            f.write("GATEWAY=%s\n" % (self.gateway,))
        f.close()

        # /etc/hosts
        f = open(instPath + "/etc/hosts", "w")
        localline = ""

        log.info("self.hostname = %s", self.hostname)
        ip = self.lookupHostname()

        # If the hostname is not resolvable, tie it to 127.0.0.1
        if not ip and self.hostname != "localhost":
            localline += self.hostname + " "
            l = string.split(self.hostname, ".")
            if len(l) > 1:
                localline += l[0] + " "

        localline += "localhost localhost\n"
        f.write("# Do not remove the following line, or various programs\n")
        f.write("# that require network functionality will fail.\n")
        f.write("127.0.0.1\t\t" + localline)
        f.write("::1\t\tlocalhost6.localdomain6 localhost6\n")

        if ip:
            nameline = "%s\t\t%s" % (ip, self.hostname)
            n = string.split(self.hostname, ".")
            if len(n) > 1:
                nameline = nameline + " " + n[0]
            f.write("%s\n" %(nameline,))

        # If the hostname was not looked up, but typed in by the user,
        # domain might not be computed, so do it now.
        if self.domains == ["localdomain"] or not self.domains:
            if '.' in self.hostname:
                # chop off everything before the leading '.'
                domain = self.hostname[(string.find(self.hostname, '.') + 1):]
                self.domains = [domain]

        # /etc/resolv.conf
        f = open(instPath + "/etc/resolv.conf", "w")

        #if self.domains != ['localdomain'] and self.domains:
        #    f.write("search %s\n" % (string.joinfields(self.domains, ' '),))

        for ns in self.nameservers():
            if ns:
                f.write("nameserver %s\n" % (ns,))

        f.close()

    def getKSDevice(self):
        if self.ksdevice is None:
            return None

        try:
            return self.netdevices[self.ksdevice]
        except:
            return None

    def bringUp(self, devices=None):
        self.write("", devices=devices)

        bus = dbus.SystemBus()
        nm = bus.get_object(isys.NM_SERVICE, isys.NM_MANAGER_PATH)
        props = dbus.Interface(nm, isys.DBUS_PROPS_IFACE)

        i = 0
        while i < 45:
            state = props.Get(isys.NM_SERVICE, "State")
            if int(state) == isys.NM_STATE_CONNECTED:
                isys.resetResolv()
                return True
            i += 1
            time.sleep(1)

        state = props.Get(isys.NM_SERVICE, "State")
        if int(state) == isys.NM_STATE_CONNECTED:
            isys.resetResolv()
            return True

        return False

