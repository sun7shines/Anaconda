# -*- coding:utf8 -*-
# network_gui.py: Network configuration dialog
#
# Michael Fulbright <msf@redhat.com>
# David Cantrell <dcantrell@redhat.com>
#
# Copyright 2000-2006 Red Hat, Inc.
#
# This software may be freely redistributed under the terms of the GNU
# library public license.
#
# You should have received a copy of the GNU Library Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import string
import gtk
import gobject
from iw_gui import *
import isys
import gui
import network
import checklist
import subprocess
import datacombo

from constants import *
import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)
import installation_type

dve_dvelist = []
devs = []

global_options = [_("Gateway"), _("Primary DNS"), _("Secondary DNS")]
global_option_labels = [_(u"网关"), _(u"主DNS"), _(u"从DNS")]
global_dhcp = True

class NetworkWindow(InstallWindow):        
    windowTitle = N_("Network Configuration")

    def __init__(self, ics):
        InstallWindow.__init__(self, ics)

    def NgetNext(self):
 
        override = 0
        if self.hostnameManual.get_active():
            #global_dhcp=False 
            self.network.hostname_dhcp=False
            hname = string.strip(self.hostnameEntry.get_text())
            neterrors =  network.sanityCheckHostname(hname)
            if neterrors is not None:
                self.handleBadHostname(hname, neterrors)
                raise gui.StayOnScreen
           
            elif len(hname) == 0:
                hname = self.defaulthostname
                #hname = "localhost" # ...better than empty
                #if ((self.getNumberActiveDevices() > 0) and
                if ((len(self.network.dve_dvelist)>0) and
                    self.handleMissingHostname()):
                    raise gui.StayOnScreen

            newHostname = hname
            override = 1
        else:
            self.network.hostname_dhcp=True
            # liu
            #newHostname = "localhost"
            newHostname = self.defaulthostname
            override = 0

       
        if not False:
            tmpvals = {}
            for t in range(len(global_options)):
                try:
                    network.sanityCheckIPString(self.globals[global_options[t]].get_text())
                    tmpvals[t] = self.globals[global_options[t]].get_text()
                except network.IPMissing, msg:
                    #if t < 2 and self.getNumberActiveDevices() > 0:
                    if t<2 and (len(self.network.dve_dvelist)>0):
                        if t==1:
                            tmp=u"主DNS"
                        #if self.handleMissingOptionalIP(global_options[t]):
                        else:
                            tmp=global_options[t]
                        if self.handleMissingOptionalIP(tmp):
                            raise gui.StayOnScreen
                        else:
                            tmpvals[t] = None
                    else:
                            tmpvals[t] = None

                except network.IPError, msg:
                    self.handleIPError(global_options[t], msg)
                    raise gui.StayOnScreen

            self.network.gateway = tmpvals[0]
            self.network.primaryNS = tmpvals[1]
            self.network.secondaryNS = tmpvals[2]
        elif self.id.instClass.name != "kickstart":
            self.network.gateway = None
            self.network.primaryNS = None
            self.network.secondaryNS = None

        self.network.hostname = newHostname
        self.network.hassethostname = True
        self.network.overrideDHCPhostname = override  

        return None
    def getNext(self):
        
        existip = False
        try:
            existip = self.anaconda.has_checked
        except:
            pass
        
        global dve_dvelist

        #self.network.dve_dvelist = dve_dvelist
        self.network.dve_dvelist = []
        active_index = self.devcombo.get_active()
        dev = self.devcombo.get_text(active_index)
        self.anaconda.combo_isset = dev
        global devs
        
        for d in devs:
            if d["DEV"] == dev:
                self.network.br0_ip=d["IPADDR"]
                self.network.br0_pr=d["NETMASK"]
                break
        bootproto = 'dhcp'
        bootproto = 'static'
        self.devices[dev].set(("bootproto", bootproto))
        self.devices[dev].set(('ipaddr','dhcp'))
        self.devices[dev].set(('netmask',''))
        self.network.dve_dvelist.append(dev)
        try:
            if len(self.network.dve_dvelist)>1:
                self.intf.messageWindow(_("Invalid Prefix"),_(u"只能选择一台设备加入交换机。"))
                raise gui.StayOnScreen
        except:
            raise gui.StayOnScreen

        try:
            if len(self.network.dve_dvelist)<1:
                self.intf.messageWindow(_("Invalid Prefix"),_(u"必须选择一台设备加入交换机。"))
                raise gui.StayScreen
        except:
            raise gui.StayOnScreen
          
        """
        iter = self.ethdevices.store.get_iter_first()

        while iter:
            model = self.ethdevices.store
            dev = model.get_value(iter, 1)
            #bootproto = model.get_value(iter, 2)
            bootproto=self.devices[dev].get('bootproto')
            onboot = model.get_value(iter, 0)
        
            if onboot:
            #if True:
                #恢复交换机数据信息
                if bootproto.lower()=="dhcp":
                    self.network.r_button_dhcp=True
                elif bootproto.lower()=="ibft":
                    self.network.r_button_dhcp=True
                elif bootproto.lower()=="static":
                    self.network.r_button_dhcp=False
                    br0_ip=self.devices[dev].get('ipaddr')      
                    br0_pr=self.devices[dev].get('netmask')
                    val=self.devices[dev].get('netmask')
                    if val.find('.')==-1:
                        br0_pr=isys.prefix2netmask(int(val))
                    self.network.br0_ip=br0_ip
                    self.network.br0_pr=br0_pr
 

                #恢复网卡数据信息
                bootproto= 'dhcp'
                self.devices[dev].set(("bootproto",bootproto)) 
                self.devices[dev].set(('ipaddr','dhcp'))
                self.devices[dev].set(('netmask',''))
                
                onboot = "yes"
                
            else:
                onboot = "yes"
            
            if bootproto.lower() == "dhcp":
                bootproto = 'dhcp'
            elif self.devices[dev].get('ipaddr') == "dhcp":
                bootproto = 'dhcp'
            elif len(self.devices[dev].get('ipaddr')) == 0:
                bootproto = 'dhcp'
            elif bootproto.lower() == "ibft":
                bootproto = 'ibft'
            else:
                bootproto = 'static'
            
            self.devices[dev].set(('onboot', 'yes'))
            
            self.devices[dev].set(("ONBOOT", onboot))
            self.devices[dev].set(("bootproto", bootproto))
            iter = self.ethdevices.store.iter_next(iter)
        """
        for d in devs:
            if d["DEV"] == dev:
                continue
            devname = d["DEV"]
            self.devices[devname].set(("IPADDR",d["IPADDR"]))
            self.devices[devname].set(('NETMASK',d["NETMASK"]))
            self.devices[devname].set(("BOOTPROTO",d["BOOTPROTO"]))
            self.devices[devname].set(("ONBOOT",d["ONBOOT"]))
        for x in devs:
            if x.get('BOOTPROTO').lower() == "static" and x.get('IPADDR'):
                existip = True
                self.anaconda.has_checked = True
                break
        if not existip:
            if self.handleMissingIp():
                raise gui.StayOnScreen
            
    
        self.NgetNext()
        
        return None

    def setHostOptionsSensitivity(self):
        # figure out if they have overridden using dhcp for hostname
        if network.anyUsingDHCP(self.devices, self.anaconda):
            self.hostnameUseDHCP.set_sensitive(1)
        
            #if self.hostname != "localhost.localdomain" and self.network.overrideDHCPhostname:
            #if self.hostname != "localhost" and self.network.overrideDHCPhostname:
            if self.hostname != self.defaulthostname and self.network.overrideDHCPhostname:
                self.hostnameManual.set_active(1)
                self.hostnameManual.set_sensitive(1)
            else:
                self.hostnameUseDHCP.set_active(1)
        else:
            self.hostnameManual.set_active(1)
            self.hostnameUseDHCP.set_sensitive(1)

    def setIPTableSensitivity(self):
        numactive = self.getNumberActiveDevices()
        state=True
        #@self.ipTable.set_sensitive(state)
        pass

    def handleMissingIp(self):

        return not self.intf.messageWindow(_("Error With Data"),
                                _(u"您还没有设置“IP地址”，或输入地址后未点击“设置”按\n钮生效，这在某些网络环境下可能会引起错误。"), type="custom", custom_buttons=[_(u"取消"), _(u"继续")])

    def handleMissingHostname(self):
        return not self.intf.messageWindow(_("Error With Data"),
                                _(u"您还没有设置主机名，这在某些网络环境下可能会引起错误。"), type="custom", custom_buttons=[_(u"取消"), _(u"继续")])

    def handleMissingOptionalIP(self, field):
        return not self.intf.messageWindow(_("Error With Data"),
                                _(u"您还没有设置\"%s\"选项，这在某些网络环境下可能会引起错误。") % (field,), type="custom", custom_buttons=[_(u"取消"), _(u"继续")])

    def handleBadHostname(self, hostname, error):
        self.intf.messageWindow(_("Error With Data"),
                                #_("The hostname \"%s\" is not valid for the following reason:\n\n%s") % (hostname, error))
                                _(u"无效的主机名\"%s\" : \n\n%s")%(hostname,error))

    def handleIPMissing(self, field):
        self.intf.messageWindow(_("Error With Data"),
            _("A value is required for the field %s.") % (field,))

    def handleIPError(self, field, msg):
        self.intf.messageWindow(_("Error With %s Data") % (field,),
                                _(u"输入错误！") )

    def handleBroadCastError(self):
        self.intf.messageWindow(_("Error With Data"),
                                #_("The IPv4 information you have entered is "
                                  #"invalid."))
                                _(u"输入的IPv4信息无效。"))


    def handleNoActiveDevices(self):
        return self.intf.messageWindow(_("Error With Data"), _("You have no active network devices.  Your system will not be able to communicate over a network by default without at least one device active."), type="custom", custom_buttons=["gtk-cancel", _("C_ontinue")])
    

    def createIPV4Repr(self, device):
        if device.get('useIPv4') is False:
            return _("Disabled")
        
        if device.get('ipaddr').lower() == 'dhcp':
            ip = 'None'
        elif device.get('bootproto').lower() in ['dhcp']:
            ip = 'None'
        elif device.get('bootproto').lower() in ['ibft']:
            ip = 'IBFT'
        else:
            prefix = str(isys.netmask2prefix(device.get('netmask')))
            ip = "%s/%s" % (device.get('ipaddr'), prefix,)
        
        return ip

   

    def getNumberActiveDevices(self):
        iter = self.ethdevices.store.get_iter_first()
        numactive = 0
        while iter:
            model = self.ethdevices.store
            if model.get_value(iter, 0):
                numactive = numactive + 1
                break
            iter = self.ethdevices.store.iter_next(iter)

        return numactive

    def anyUsingDHCP(self):
        return 0
    
    def setIPv4Manual(self, ipaddr, netmask):
        if ipaddr.lower() == 'dhcp' or ipaddr.lower() == 'ibft':
            return
        if ipaddr is not None:
            self.ipIPv4.set_text(ipaddr)
        
        if netmask is not None:
            self.ipsubnet.set_text(netmask)
            
    def showWirelessTable(self):
        self.enable_wireless = True
        #self.wireless_table.show()
        self.wireless_table.set_sensitive(True)
        #self.toplevel.resize(1, 1)       

    def setESSID(self, essid):
        if essid is not None: 
            self.essid.set_text(essid)     
    def setEncKey(self, key):
        if key is not None:
            self.enc_key.set_text(key)
 
    def hideWirelessTable(self):
        self.enable_wireless = False
        #self.wireless_table.hide()
        self.wireless_table.set_sensitive(False)
        #self.toplevel.resize(1, 1)
    def isPtPEnabled(self):
        return self.enable_ptp
    def showPtPTable(self):
        self.enable_ptp = True
        #self.ptp_table.show()
        self.ptp_table.set_sensitive(True)
        #self.toplevel.resize(1, 1)
    def hidePtPTable(self):
        self.enable_ptp = False
        #self.ptp_table.hide()
        self.ptp_table.set_sensitive(False)
        #self.toplevel.resize(1, 1)
    def setPtP(self, remip):
        if remip is not None:
            self.ptp_address.set_text(remip)
    def selectIPv4Method(self, ipaddr):
        if ipaddr.lower() == 'dhcp':
            self.ipradio_dhcp.set_active(1)
        elif ipaddr.lower() == 'ibft':
            self.ipradio_dhcp.set_active(1)

        elif ipaddr != "":
            self.ipradio_manual.set_active(1)

    def selectIPv4Method_a(self, ipaddr):
        if ipaddr.lower() == 'dhcp':
            self.ipradio_dhcp.set_active(1)
        elif ipaddr.lower() == 'ibft':
            self.ipradio_dhcp.set_active(1)
        elif ipaddr != "":
            self.ipradio_manual.set_active(1)
    def setHardwareAddress(self, mac):
        if mac is None:
            mac = _('unknown')
        self.hardware_address.set_markup("<b>" + _(u"硬件地址: ") + mac + "</b>")
    def editDevice_new(self):
        selection = self.ethdevices.get_selection()
        (model, iter) = selection.get_selected()
        if not iter:
            return None
        dev = model.get_value(iter, 1)
        #bootproto = model.get_value(iter, 2)
        onboot = model.get_value(iter, 0)

        ipaddr = self.devices[dev].get('ipaddr')
        netmask = self.devices[dev].get('netmask')
        bootproto=self.devices[dev].get('bootproto')
        self.setIPv4Manual(ipaddr, netmask)

        if isys.isWireless(dev):
            self.showWirelessTable()
            self.setESSID(self.devices[dev].get('essid'))
            self.setEncKey(self.devices[dev].get('key'))
        else:
            self.hideWirelessTable()

        if network.isPtpDev(dev):
            self.showPtPTable()
            self.setPtP(self.devices[dev].get('remip'))
        else:
            self.hidePtPTable()

        #self.setEnableIPv4(self.devices[dev].get('useIPv4'))
        self.selectIPv4Method(ipaddr)

        if bootproto.lower() == 'dhcp':
            self.ipradio_dhcp.set_active(1)
            self.ipIPv4.set_sensitive(False)
            self.ipsubnet.set_sensitive(False)
            self.ipIPv4.set_text("")
            self.ipsubnet.set_text("")

            #self.ipradio_dhcp.set_active(True)
            self.edit1.set_sensitive(False)
            
        elif bootproto.lower() == 'ibft':
            self.ipradio_dhcp.set_active(1)
            self.ipIPv4.set_sensitive(False)
            self.ipsubnet.set_sensitive(False)
            self.ipIPv4.set_text("")
            self.ipsubnet.set_text("")
            
            ####
            self.edit1.set_sensitive(False)
            
        elif bootproto != "":
            self.ipradio_manual.set_active(1)
            self.ipIPv4.set_sensitive(True)
            self.ipsubnet.set_sensitive(True)
            
            ####
            self.edit1.set_sensitive(True)

        #self.setHardwareAddress(self.devices[dev].get('hwaddr'))
        return
    def getIPv4Method(self):
        #if self.isIPv4Enabled():
        if self.ipradio_dhcp.get_active():
            return 'dhcp'
        elif self.ipradio_manual.get_active():
            return 'static'
    def isWirelessEnabled(self):
        return self.enable_wireless
     
    def isPtPEnabled(self):
        return self.enable_ptp
    def getIPv4Address(self):
        return self.ipIPv4.get_text()
     
    def getIPv4Prefix(self):
        return self.ipsubnet.get_text()
     
     
     
    def setESSID(self, essid):
        if essid is not None:
            self.essid.set_text(essid)
     
    def getESSID(self):
        return self.essid.get_text()
     
    def setEncKey(self, key):
        if key is not None:
            self.enc_key.set_text(key)
     
    def getEncKey(self):
        return self.enc_key.get_text()


    def editDevice(self,data):
        self.okClicked()
        global devs
        dev = {}
        selection = self.ethdevices.get_selection()
        (model, iter) = selection.get_selected()
        if not iter:
            return None
        dev["DEV"] = model.get_value(iter, 1)
        dev["IPADDR"] = self.getIPv4Address()
        dev["NETMASK"] = self.getIPv4Prefix()
        dev["BOOTPROTO"] = "static"
        dev["ONBOOT"] = "yes"
        dev["NETWORK"] = ""
        dev["BROADCAST"] = ""
        try:
            (net, bc) = isys.inet_calcNetBroad(self.getIPv4Address(),self.getIPv4Prefix())
            dev["NETWORK"] = net
            dev["BROADCAST"] = bc
            #devs.append(dev)
            flag = False
            for x in devs:
                if x["DEV"] == dev["DEV"]:
                    x["IPADDR"] = dev["IPADDR"]
                    x["NETMASK"] = dev["NETMASK"]
                    x["BOOTPROTO"] = dev["BOOTPROTO"]
                    x["ONBOOT"] = dev["ONBOOT"]
                    x["NETWORK"] = dev["NETWORK"]
                    x["BROADCAST"] = dev["BROADCAST"]
                    flag = True
                    break
            if not flag:
                devs.append(dev)
        except Exception, e:
            #self.handleBroadCastError()
            pass
        """
        onboot = model.get_value(iter, 0)
        #onboot = True
        bootproto = self.getIPv4Method()
        if bootproto == 'dhcp' or bootproto == 'ibft':
            self.devices[dev].set(('ipaddr', bootproto))
            self.devices[dev].set(('network', ''), ('broadcast', ''))
        elif bootproto == 'static':
            try:
                (net, bc) = isys.inet_calcNetBroad(self.getIPv4Address(),self.getIPv4Prefix())
                self.devices[dev].set(('network', net), ('broadcast', bc))
            except Exception, e:
                #self.handleBroadCastError()
                return
            
            self.devices[dev].set(('ipaddr', self.getIPv4Address()))
            self.devices[dev].set(('netmask', self.getIPv4Prefix()))
        if self.isWirelessEnabled():
            self.devices[dev].set(('essid', self.getESSID()))
            self.devices[dev].set(('key', self.getEncKey()))
        if self.isPtPEnabled():
            self.devices[dev].set(('remip', self.getPtP()))
        self.devices[dev].set(('bootproto', bootproto))
        if onboot:
            self.devices[dev].set(('onboot', 'yes'))
        else:
            self.devices[dev].set(('onboot', 'no'))
        model.set_value(iter, 0, onboot)
        model.set_value(iter, 2, self.createIPV4Repr(self.devices[dev]))
        #editwin.close()
        """
        prefix = str(isys.netmask2prefix(dev["NETMASK"]))
        ip = "%s/%s" % (dev["IPADDR"], prefix)
        model.set_value(iter, 2, ip)
        return
        
    def okClicked(self):
        
        #if self.isIPv4Enabled():
        if self.ipradio_manual.get_active():
            try:
                network.sanityCheckIPString(self.ipIPv4.get_text())
            except network.IPMissing, msg:
                """self.handleIPMissing('IPv4 address')"""
                self.handleIPMissing(u"IPv4 地址")
                #self.valid_input = 1
                return
            except network.IPError, msg:
                #self.handleIPError('IPv4 address', msg)
                self.handleIPError(u"IPv4 地址", msg)
                #self.valid_input = 1
                return

            val = self.ipsubnet.get_text()
            if val.find('.') == -1:
                # user provided a CIDR prefix
                try:
                    if int(val) > 32 or int(val) < 0:
                        self.intf.messageWindow(_("Invalid Prefix"),
                                                   _("IPv4 prefix "
                                         "must be between "
                                         "0 and 32."))
                        #self.valid_input = 1
                        return
                    else:
                        self.ipsubnet.set_text(isys.prefix2netmask(int(val)))
                except:
                    #self.handleIPMissing('IPv4 network mask')
                    self.handleIPMissing(u"IPv4 子网掩码")
                    #self.valid_input = 1
                    return
            else:
                # user provided a dotted-quad netmask
                try:
                    network.sanityCheckIPString(self.ipsubnet.get_text())
                except network.IPMissing, msg:
                    self.handleIPMissing(u"IPv4 子网掩码")
                    #self.valid_input = 1
                    return
                except network.IPError, msg:
                    self.handleIPError(u"IPv4 子网掩码", msg)
                    return

        if self.isPtPEnabled():
            try:
                network.sanityCheckIPString(self.ptp_address.get_text())
            except network.IPMissing, msg:
                self.handleIPMissing('point-to-point IP address')
                return
            except network.IPError, msg:
                self.handleIPError('point-to-point IP address', msg)
                return

    def setsensitive_false(self):    
        self.edit1.set_sensitive(False)
        self.ipIPv4.set_text("")
        self.ipsubnet.set_text("")
        self.ipIPv4.set_sensitive(False)
        self.ipsubnet.set_sensitive(False)
        self.ipradio_dhcp.set_sensitive(False)
        self.ipradio_manual.set_sensitive(False)
        
        ###
        self.edit1.set_sensitive(False)
        
    def setsensitive_true(self):
        self.edit1.set_sensitive(True)
        self.ipIPv4.set_sensitive(True)
        self.ipsubnet.set_sensitive(True)
        self.ipradio_dhcp.set_sensitive(True)
        self.ipradio_manual.set_sensitive(True)
        
        #####
        self.edit1.set_sensitive(True)
        
    def on_cursor_changed_a(self,widget):
        self.editDevice_new()
        return False

    def check_button(self,iter):
        itertmp=self.ethdevices.store.get_iter_first()
        while itertmp:
            if itertmp==iter:
                self.ethdevices.store.set_value(itertmp,0,True)
            else:
                self.ethdevices.store.set_value(itertmp,0,False)
            itertmp=self.ethdevices.store.iter_next(itertmp)
    def onbootToggleCB(self, row, data):
        global dve_dvelist
        model = self.ethdevices.get_model()
        iter = model.get_iter((string.atoi(data),))
        val = model.get_value(iter, 0)
        dev = model.get_value(iter, 1)
        if val:
            onboot = "yes"
            bootproto = 'dhcp'
            self.devices[dev].set(("bootproto", bootproto))
            self.devices[dev].set(('ipaddr','dhcp'))
            self.devices[dev].set(('netmask',''))
            model.set_value(iter, 0, onboot)
            model.set_value(iter, 2, self.createIPV4Repr(self.devices[dev]))
            self.editDevice_new()
            """u"修改于5月15日"self.setsensitive_false()"""
            if dev in dve_dvelist:
                pass
            else:
                # liuweifeng
                dve_dvelist.append(dev)
              
        else:
            onboot = "no"
            self.editDevice_new()
            """self.setsensitive_true()"""
            if dev in dve_dvelist:
                dve_dvelist.remove(dev)
               
        self.devices[dev].set(("ONBOOT", onboot))    
        return

    def isactive(self,dev):
        
        cmd = ['ethtool',dev]
        output=subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=open('/dev/null', 'w')
                                )

        out = output.stdout.read()
        lines=out.split("\n") 
        for line in lines:
            if line.find("Link detected") != -1:
                if line.find("yes") != -1:
                    return True
                if line.find("no") != -1:
                    return False 
        return False
    def getactivedevs(self,devnames): 
        s = []
        for x in devnames:
            if self.isactive(x):
                s.append(x)
        for x in devnames:
            if x not in s:
                s.append(x)    
        return s
    
    def setupDevices(self):
        global dve_dvelist
        global devs
        devnames = self.devices.keys()
        devnames.sort()
        s = self.getactivedevs(devnames)
        devnames = s
        store = gtk.TreeStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING,
                              gobject.TYPE_STRING, gobject.TYPE_STRING)

        self.ethdevices = NetworkDeviceCheckList(2, store, clickCB=self.onbootToggleCB)
        self.ethdevices.connect("cursor-changed",self.on_cursor_changed_a)
        num = 0
        if len(self.network.dve_dvelist)==0:
            # 设置默认IP 6-26-2013 添加
            device = devnames[0]
            if num == 0:
                if device not in dve_dvelist:
                    dve_dvelist.append(device)
            self.devices[device].set(("ONBOOT", "yes"))
            self.devices[device].set(("bootproto", "static"))
            self.ethdevices.append_row((device, "10.0.0.1/24"), True)
            dev = {}
            dev["DEV"] = device
            dev["IPADDR"] = "10.0.0.1"
            dev["NETMASK"] = "255.255.255.0"
            dev["BOOTPROTO"] = "static"
            dev["ONBOOT"] = "yes"
            dev["NETWORK"] = ""
            dev["BROADCAST"] = ""
            try:
                (net, bc) = isys.inet_calcNetBroad("10.0.0.1","255.255.255.0")
                dev["NETWORK"] = net
                dev["BROADCAST"] = bc
                devs.append(dev)
            except Exception, e:
                return
            num += 1
            
            for device in devnames[1:]:
                if num == 0:
                    if device not in dve_dvelist:
                        dve_dvelist.append(device)
                    onboot = "yes"
                    self.devices[device].set(("ONBOOT", onboot))

                    onboot = self.devices[device].get("ONBOOT")
                    if ((num == 0 and not onboot) or onboot == "yes"):
                        active = True
                    else:
                        active = False

                    bootproto = 'dhcp'
                    self.devices[device].set(("bootproto", bootproto))
                    ipv4 = self.createIPV4Repr(self.devices[device])
                    self.ethdevices.append_row((device, ipv4), active)

                    num += 1
                else:
                    onboot="no"    
                    self.devices[device].set(("ONBOOT",onboot))
                    active=False
                    bootproto='dhcp'
                    self.devices[device].set(("bootproto",bootproto))
                    ipv4 = self.createIPV4Repr(self.devices[device])
                    self.ethdevices.append_row((device, ipv4), active)
                    num +=1
        else:
            for device in devnames:                            
                if device in dve_dvelist:
                    active = True
                    if self.network.r_button_dhcp==True:        #主要时恢复网卡的数据
                        bootproto='dhcp'
                    else:
                        bootproto='static'
                        self.devices[device].set(('ipaddr',self.network.br0_ip))
                        self.devices[device].set(('netmask',self.network.br0_pr))
                    self.devices[device].set(("bootproto",bootproto))
                    
                else:
                    active = False

               
                ipv4 = self.createIPV4Repr(self.devices[device])
                self.ethdevices.append_row((device, ipv4), active)

              
        self.ethdevices.set_column_title(0, (_(u"加入交换机")))
        self.ethdevices.set_column_sizing (0, gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.ethdevices.set_column_title(1, (_("Device")))
        self.ethdevices.set_column_sizing (1, gtk.TREE_VIEW_COLUMN_FIXED)
        self.ethdevices.set_column_title(2, (_("IPv4/Netmask")))
        self.ethdevices.set_column_sizing (2, gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.ethdevices.set_column_min_width(0,0)
        self.ethdevices.set_column_max_width(0,0)
        self.ethdevices.set_column_min_width(1,100)
        self.ethdevices.set_column_min_width(2,95)
        self.ethdevices.set_headers_visible(True)

        self.ignoreEvents = 1
        iter = self.ethdevices.store.get_iter_first()
        selection = self.ethdevices.get_selection()
        selection.set_mode(gtk.SELECTION_BROWSE)
        selection.select_iter(iter)
        self.ignoreEvents = 0
        return self.ethdevices

    def changeDevCombo(self,data):
        
        #如果已经处理网卡数据，改变加入交换机的网卡时要重新设置对应网卡数据
        active_index = self.devcombo.get_active()
        dev = self.devcombo.get_text(active_index)
        try:
            if self.anaconda.combo_isset!=self.devcombo.get_text(active_index):
                self.anaconda.has_checked = False
                
        except:
            self.anaconda.has_checked = False


    def make_switch_box(self,hbox):
        devnames = self.devices.keys()
        devnames.sort()
        s = self.getactivedevs(devnames)
        devnames = s
        
        switchbox = gtk.HBox()
        label = gtk.Label()
        label.set_markup("<span  foreground='#333333'><b>加入交换机的网卡:</b></span>")
        switchbox.pack_start(label,False,False,0)
        self.devcombo = datacombo.DataComboBox()
        self.devcombo.connect("changed",self.changeDevCombo)
        for dev in devnames:
            self.devcombo.append(dev,dev)
        try:
            setcombo_flag = self.anaconda.combo_isset
        except:
            setcombo_flag = False
        try:
            if not setcombo_flag:
                #self.devcombo.set_active_text('eth1')
                self.devcombo.set_active(0)
            else:
                #self.devcombo.set_active(1)
                self.devcombo.set_active_text(setcombo_flag)
        except:
            pass
        #if setcombo_flag:
        #    raise NameError,setcombo_flag
        switchbox.pack_start(self.devcombo,False,False,0)
        hbox.pack_start(switchbox,False,False,3)

    def make_ip_box(self,hbox):
        
        ipbox = gtk.VBox()
        l=gtk.Label()
        l.set_markup("<span  foreground='#333333'><b>IPv4设置:</b></span>")
        l.set_alignment(0.0,0.0)
        tmphbox = gtk.HBox()
        tmphbox.pack_start(l,False,False,0)
        ipbox.pack_start(tmphbox,False,False,2)
        
        tmphbox = gtk.HBox()        
        self.ipradio_dhcp=gtk.RadioButton(None,u"自动设置")
        
        l = self.ipradio_dhcp.get_children()[0]
        lstr = "<span  foreground='#333333'><b>"+l.get_text()+"</b></span>"
        l.set_markup(lstr)
        
        tmphbox.pack_start(self.ipradio_dhcp,True,True,0)
        ipbox.pack_start(tmphbox,False,False,2)
        
        tmphbox = gtk.HBox()
        self.ipradio_manual=gtk.RadioButton(self.ipradio_dhcp,u"手动设置")
        
        l = self.ipradio_manual.get_children()[0]
        lstr = "<span  foreground='#333333'><b>"+l.get_text()+"</b></span>"
        l.set_markup(lstr)
        
        tmphbox.pack_start(self.ipradio_manual,True,True,0)
        ipbox.pack_start(tmphbox,False,False,2)
        
        tmphbox=gtk.HBox(False,0)
        iplabel_IP=gtk.Label()
        iplabel_IP.set_markup("<span  foreground='#333333'><b>IP地址:</b></span>")
        iplabel_IP.set_width_chars(7)
        iplabel_IP.set_alignment(1.0, 0.5)
        tmphbox.pack_start(iplabel_IP,False,False,15)
        self.ipIPv4=gtk.Entry()
        self.ipIPv4.set_width_chars(28)
        align2=gtk.Alignment(0,0,0,0)
        align2.add(self.ipIPv4)
        tmphbox.pack_start(align2,False,False,0)
        ipbox.pack_start(tmphbox,False,False,2)
        
        tmphbox1=gtk.HBox(False,0)
        iplabel_subnet=gtk.Label()
        iplabel_subnet.set_markup("<span  foreground='#333333'><b>子网掩码:</b></span>")
        iplabel_subnet.set_width_chars(7)
        iplabel_subnet.set_alignment(1.0, 0.5)
        tmphbox1.pack_start(iplabel_subnet,False,False,15)
        self.ipsubnet=gtk.Entry()
        self.ipsubnet.set_width_chars(28)
        align4=gtk.Alignment(0,0,0,0)
        align4.add(self.ipsubnet)
        tmphbox1.pack_start(align4,False,False,0)

        self.edit1=gtk.Button(_(u"设置"))
        l = self.edit1.get_children()[0]
        #lstr = "<span  foreground='#666666'><b>"+l.get_text()+"</b></span>"
        #l.set_markup(lstr)
        
        self.edit1.connect("clicked",self.editDevice)
        
        # 手动设置模式，按钮可用 
        # self.edit1.set_sensitive(self.ipradio_manual.get_action())
        
        self.edit1.set_size_request(40,25)
        align_edit1=gtk.Alignment(0.5,0.5,0,0)
        align_edit1.add(self.edit1)
        tmphbox1.pack_start(align_edit1,False,False,5)

        """ip_help_label_subnet=gtk.Label(u"(注意：必须点击“设置”按钮，IP配置才会生效！)")"""
        ip_help_label_subnet=gtk.Label()
        lstr = "<span  foreground='#333333'><b>(注意：必须点击\"设置\"按钮，IP配置才会生效！)</b></span>"
        ip_help_label_subnet.set_markup(lstr)
        tmphbox1.pack_start(ip_help_label_subnet,False,False,10)

        ipbox.pack_start(tmphbox1,False,False,2)
        hbox.pack_start(ipbox,False,False,0)
        self.ipradio_dhcp.connect("toggled",self.ipv4_changed)
        self.ipradio_manual.connect("toggled",self.ipv4_changed)
            
        ##########################################################################    
        self.enable_wireless=False
        self.wireless_table=gtk.Table(2,3,False)
        label1=gtk.Label("ESSID")
        label1.set_width_chars(18)
        align_label1=gtk.Alignment(0,0,0,0)
        align_label1.add(label1)
        
        label2=gtk.Label("Encryption Key")
        label2.set_width_chars(18)
        align_label2=gtk.Alignment(0,0,0,0)
        align_label2.add(label2)
        
        self.ency_key=gtk.Entry()
        self.ency_key.set_width_chars(32)
        align_ency=gtk.Alignment(0,0,0,0)
        align_ency.add(self.ency_key)
        
        self.essid=gtk.Entry()
        self.essid.set_width_chars(32)
        align_essid=gtk.Alignment(0,0,0,0)
        align_essid.add(self.essid)
        
        self.wireless_table.attach(align_label1,0,1,0,1)
        self.wireless_table.attach(align_essid,1,2,0,1)
        self.wireless_table.attach(align_label2,0,1,1,2)
        self.wireless_table.attach(align_ency,1,2,1,2)
        
        self.enable_ptp=1
        self.ptp_table=gtk.Table(2,3,False)
        label3=gtk.Label("Point to Point(IP)")
        label3.set_width_chars(18)
        align_label3=gtk.Alignment(0,0,0,0)
        align_label3.add(label3)
        
        self.ptp_address=gtk.Entry()
        self.ptp_address.set_width_chars(32)
        align_ptp=gtk.Alignment(0,0,0,0)
        align_ptp.add(self.ptp_address)
        self.ptp_table.attach(align_label3,0,1,0,1)
        self.ptp_table.attach(align_ptp,1,2,0,1)

    def _setManualIPv4Sensitivity(self, sensitive):
        self.ipsubnet.set_sensitive(sensitive)
        self.ipIPv4.set_sensitive(sensitive)
        self.edit1.set_sensitive(sensitive)
#        if sensitive:
#            l = self.edit1.get_children()[0]
#            #lstr = "<span  foreground='#333333'><b>"+l.get_text()+"</b></span>"
#            #l.set_markup(lstr)
#        else:
#            l = self.edit1.get_children()[0]
#            #lstr = "<span  foreground='#666666'><b>"+l.get_text()+"</b></span>"
#            #l.set_markup(lstr)
#            
        
    def ipv4_changed(self,args):
        if False==self.ipradio_manual.get_active():
            self.ipIPv4.set_text("")
            self.ipsubnet.set_text("")
        self._setManualIPv4Sensitivity(self.ipradio_manual.get_active())
    

    def hostnameUseDHCPCB(self, widget, data):
        self.network.overrideDHCPhostname = 0
        #liu dhcp
        #self.hostnameEntry.set_text("localhost")
        self.hostnameEntry.set_text(self.defaulthostname)
        self.hostnameEntry.set_sensitive(not widget.get_active())
    def hostnameManualCB(self, widget, data):
        self.network.overrideDHCPhostname = 1
        if widget.get_active():
            self.hostnameEntry.grab_focus()
            
    def make_other_box(self,hbox):
        
        vbox = gtk.VBox()
        tmphbox = gtk.HBox()
        l = gtk.Label()
        """l.set_markup("<b>%s</b>" %(_("其他设置:"),))"""
        l.set_markup("<span  foreground='#333333'><b>其他设置:</b></span>")
        tmphbox.pack_start(l,False,False,0)
        vbox.pack_start(tmphbox,False,False,3)

        options = {}
        for i in range(len(global_options)):
            tmphbox = gtk.HBox()
            text = "%s:" %(global_option_labels[i],)
            lstr = "<span  foreground='#333333'><b>"+text+"</b></span>"
            label = gtk.Label()
            label.set_markup(lstr)
            
            #label.set_property("use-underline", True)
            label.set_alignment(1.0, 0.5)
            label.set_width_chars(7)
            tmphbox.pack_start(label,False,False,15)
            align = gtk.Alignment(0, 0.5)
            options[i] = gtk.Entry()
            options[i].set_width_chars(28)
            align.add(options[i])
            label.set_mnemonic_widget(options[i])

            tmphbox.pack_start(align,False,False,0)
            vbox.pack_start(tmphbox,False,False,2)

        self.globals = {}
        for t in range(len(global_options)):
            self.globals[global_options[t]] = options[t]

        if self.network.hostname_dhcp==True:
            self.hostnameUseDHCP.set_active(True)
        else:
            self.hostnameManual.set_active(True)
        self.hostnameEntry.set_text(self.network.hostname)
 
        if False:
            self.globals[_("Gateway")].set_text("")
            self.globals[_("Primary DNS")].set_text("")
            self.globals[_("Secondary DNS")].set_text("")
            self.globals[_("Gateway")].set_sensitive(False)
            self.globals[_("Primary DNS")].set_sensitive(False)
            self.globals[_("Secondary DNS")].set_sensitive(False)
        else:
            self.globals[_("Gateway")].set_sensitive(True)
            self.globals[_("Primary DNS")].set_sensitive(True)
            self.globals[_("Secondary DNS")].set_sensitive(True)

            if self.network.gateway:
                self.globals[_("Gateway")].set_text(self.network.gateway)
            if self.network.primaryNS:
                self.globals[_("Primary DNS")].set_text(self.network.primaryNS)
            if self.network.secondaryNS:
                self.globals[_("Secondary DNS")].set_text(self.network.secondaryNS)

        #####################
        # 网卡加入交换机
        
        #swvbox = gtk.VBox()
        #shbox = gtk.HBox()
        #self.make_switch_box(shbox)
        #swvbox.pack_end(shbox, False, False,10)
        
        ######################

        hbox.pack_start(vbox, False, False)
        #hbox.pack_start(swvbox, False, False,10)
    def make_hostname_box(self,hbox):
        hostbox=gtk.VBox()
    
        tmphbox = gtk.HBox()
        l = gtk.Label()
        """"l.set_markup("<b>%s</b>" %(_(u"主机名设置:"),))"""
        l.set_markup("<span  foreground='#333333'><b>主机名设置:</b></span>")
        tmphbox.pack_start(l,False,False)
        hostbox.pack_start(tmphbox,False,False,3)

        tmphbox=gtk.HBox()
        self.hostnameUseDHCP = gtk.RadioButton(label=_(u"自动设置"))
        
        l = self.hostnameUseDHCP.get_children()[0]
        lstr = "<span  foreground='#333333'><b>"+l.get_text()+"</b></span>"
        l.set_markup(lstr)
        
        self.hostnameUseDHCP.connect("toggled", self.hostnameUseDHCPCB, None)
        tmphbox.pack_start (self.hostnameUseDHCP, False, False)
        hostbox.pack_start(tmphbox, False, False,2)

        tmphbox=gtk.HBox()
        
        self.hostnameManual = gtk.RadioButton(group=self.hostnameUseDHCP, label=_(u"手动设置"))
        
        l = self.hostnameManual.get_children()[0]
        lstr = "<span  foreground='#333333'><b>"+l.get_text()+"</b></span>"
        l.set_markup(lstr)
        
        tmphbox.pack_start(self.hostnameManual, False, False,0)
        self.hostnameEntry = gtk.Entry()
        self.hostnameEntry.connect('insert-text',self.hinsert_text)
        self.hostnameEntry.set_width_chars(28)
        tmphbox.pack_start(self.hostnameEntry, False, False,10)
        tmphbox.pack_start(gtk.Label(_(u'(例如：localhost)')), False, False,50)
        self.hostnameManual.connect("toggled", self.hostnameManualCB, None)
        hostbox.pack_start(tmphbox, False, False,2)
        
        hbox.pack_start(hostbox, False, False)

    def hinsert_text(self,entry,new_text, new_text_length, position):
        if len(entry.get_text())+len(new_text)>64:
            entry.stop_emission('insert-text')
        str = string.ascii_letters+string.digits+"-"
        for c in new_text:
            if c not in str:
                entry.stop_emission('insert-text')
        
    def make_tree_box(self,hbox):
        
        treebox = gtk.VBox()
        
        tmphbox = gtk.HBox()
        l = gtk.Label()
        """"l.set_markup("<b>%s</b>" %(_(u"网络设备:"),))"""
        l.set_markup("<span foreground='#333333'><b>网络设备:</b></span>")
        tmphbox.pack_start(l,False,False,0)
        treebox.pack_start(tmphbox,False,False,3)
        
        devhbox = gtk.HBox(False)
        
        self.devlist = self.setupDevices()
        devlistSW = gtk.ScrolledWindow()
        devlistSW.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        devlistSW.set_shadow_type(gtk.SHADOW_IN)
        devlistSW.add(self.devlist)
        devlistSW.set_size_request(320, 75)
        devhbox.pack_start(devlistSW, False)
        
        
        text = u"提示：\n对选择加入交换机的网卡进行设置IP，将生效为交换机的IP！\n对未选择加入交换机的网卡进行设置IP，将生效为网卡的IP！\n如果重新退回本界面,并改变加入交换机的网卡,则会重置改变的网卡的IP配置,需要重新设置IP!"
        ltmp = gtk.Label()
        lstr = "<span foreground='#333333'><b>"+text+"</b></span>"
        ltmp.set_markup(lstr)
        
        
        devhbox.pack_start(ltmp,False,False,60)
        treebox.pack_start(devhbox,False,False,3)

        hbox.pack_start(treebox, False)
        
    def getScreen(self, anaconda):
        global dve_dvelist
        self.intf = anaconda.intf
        self.id = anaconda.id
        self.anaconda = anaconda
        
        isBlack = False
        '''
        f = open("/root/isotype")
        lines = f.readlines()
        f.close()
    
        for x in lines:
            if x.find("vServer") != -1 or x.find("vCenter") != -1:
                isBlack = True
                break
        '''
        import fvi
        x = fvi.get_iso_type()
        if x.find("vServer") != -1 or x.find("vCenter") != -1:
            isBlack = True 
            
        if isBlack:
            bgcolor = "#333333"
            fontcolor = "#e6e6e6"
        else:
            bgcolor = "#cccccc"
            fontcolor = "#333333"
        
        eboximage = gtk.EventBox()
        eboximage.set_app_paintable(True)
        eboximage.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse(bgcolor))
        eboximage.set_size_request(1024,100)
        
        fixed = gtk.Fixed()
        i = gtk.Image()
        path = "/usr/share/anaconda/pixmaps/icon7_net_configration.png"
        i.set_from_file(path)
        i.show()
        fixed.put(i,45,15)
        label1 = gtk.Label()
        lstr = "<span font_desc='16' weight='bold' foreground='"+fontcolor+"'><b>网络配置:</b></span>"
        label1.set_markup(lstr)
        fixed.put(label1,160,23)
        label2 = gtk.Label()
        lstr = "<span font_desc=' 11.5' weight='bold' foreground='"+fontcolor+"'><b>网卡加入交换机，配置网卡及交换机的信息。</b></span>"
        label2.set_markup(lstr)
        fixed.put(label2,160,58)
        eboximage.add(fixed) 
        eboximage.show_all()

        box = gtk.VBox(False)
        box.pack_start(eboximage,expand=False,fill=False)
        
        
        self.network = anaconda.id.network
        tmp = self.anaconda.isotype+'-'+self.anaconda.sn
        aim = ""
        good_str = string.ascii_letters+string.digits+"-"
        for c in tmp:
            if c in good_str:
                aim = aim+c
        aim = aim[:64]
        
        try:
            if not self.network.hassethostname:
                self.network.hostname = aim
        except:
            self.network.hostname = aim
            
        #self.network.hostname = aim
        self.defaulthostname = self.network.hostname
        
        self.devices = self.network.available()
        if len(self.network.dve_dvelist)==0:
            pass
        else:
            dve_dvelist=self.network.dve_dvelist
            self.devices=self.network.netdevices
        if not self.devices:
            return None

        self.numdevices = len(self.devices.keys())

        self.hostname = self.network.hostname
        #############################################
        boxall = gtk.VBox()
        hbox1 = gtk.HBox(False)
        self.make_tree_box(hbox1)
        boxall.pack_start(hbox1,False,3)
        boxall.grab_focus()
        
        
        #################################################### liuweifeng

        hbox1 = gtk.HBox()
        self.make_switch_box(hbox1)
        boxall.pack_start(hbox1,False,3)
        
        #############################################################
        
        ##############################################
        
        hbox1=gtk.HBox(False)
        self.make_ip_box(hbox1)
        boxall.pack_start(hbox1,False,3)
       
        self.editDevice_new()    


        ###################################################################### 

        if not self.devices:
            return None

        self.numdevices = len(self.devices.keys())

        self.hostname = self.network.hostname
        
        hbox1 = gtk.HBox(False)
        self.make_hostname_box(hbox1)
        boxall.pack_start(hbox1, False, False,3)
        
        #############################################################
    
        hbox1 = gtk.HBox(False)
        self.make_other_box(hbox1)
        boxall.pack_start(hbox1, False, False,3)
        
        fix = gtk.Fixed()
        fix.put(boxall,40,8)
        box.pack_start(fix,True,True)
        #######################################################
        self.hostnameEntry.set_sensitive(not self.hostnameUseDHCP.get_active())
        """return box"""
        ebox = gtk.EventBox()
        ebox.add(box)
        ebox.set_app_paintable(True)
        ebox.set_border_width(0)
        ebox.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#e6e6e6"))
        return ebox


class NetworkDeviceEditWindow:
    def __init__(self, netwin):
        self.netwin = netwin
        self.xml = gtk.glade.XML(gui.findGladeFile('netpostconfig.glade'))

        # Pull in a ton of widgets.
        self.toplevel = self.xml.get_widget("net_post_config_win")
        gui.addFrame(self.toplevel)
        self.button_ok = self.xml.get_widget("button_ok")
        self.button_cancel = self.xml.get_widget("button_cancel")

        self.configure_dev = self.xml.get_widget("configure_dev")
        self.hardware_address = self.xml.get_widget("hardware_address")

        self.enable_ipv4 = self.xml.get_widget("enable_ipv4")
        self.dhcp_ipv4 = self.xml.get_widget("dhcp_ipv4")
        self.manual_ipv4 = self.xml.get_widget("manual_ipv4")
        self.ipv4_address_label = self.xml.get_widget("ipv4_address_label")
        self.ipv4_prefix_label = self.xml.get_widget("ipv4_prefix_label")
        self.ipv4_address = self.xml.get_widget("ipv4_address")
        self.ipv4_slash = self.xml.get_widget("ipv4_slash_label")
        self.ipv4_prefix = self.xml.get_widget("ipv4_prefix")

        

        self.toplevel.connect("destroy", self.destroy)
        self.button_ok.connect("clicked", self.okClicked)
        self.button_cancel.connect("clicked", self.cancelClicked)

        self.enable_ipv4.connect("toggled", self.ipv4_toggled)
        self.dhcp_ipv4.connect("toggled", self.ipv4_changed)
        self.manual_ipv4.connect("toggled", self.ipv4_changed)
        
        self.enable_wireless = False
        self.wireless_table = self.xml.get_widget("wireless_table")
        self.essid = self.xml.get_widget("essid")
        self.enc_key = self.xml.get_widget("enc_key")

        self.enable_ptp = 1
        self.ptp_table = self.xml.get_widget("ptp_table")
        self.ptp_address = self.xml.get_widget("ptp_ip")

        self.valid_input = 1

    def getInputValidationResults(self):
        # 1=invalid input
        # 2=valid input
        # 3=cancel pressed
        return self.valid_input

    def show(self):
        self.toplevel.show_all()

    def run(self):
        self.toplevel.run()

    def close(self):
        self.toplevel.destroy()

    def setTitle(self, title):
        self.toplevel.set_title(_('Edit Device ') + title)

    def setDescription(self, desc):
        if desc is None:
            desc = _('Unknown Ethernet Device')

        self.configure_dev.set_markup("<b>" + desc[:70] + "</b>")

    def setHardwareAddress(self, mac):
        if mac is None:
            mac = _('unknown')

        self.hardware_address.set_markup("<b>" + _(u"硬件地址: ") + mac + "</b>")

    def isWirelessEnabled(self):
        return self.enable_wireless

    def isPtPEnabled(self):
        return self.enable_ptp

    def showWirelessTable(self):
        self.enable_wireless = True
        self.wireless_table.show()
        self.toplevel.resize(1, 1)

    def hideWirelessTable(self):
        self.enable_wireless = False
        self.wireless_table.hide()
        self.toplevel.resize(1, 1)

    def showPtPTable(self):
        self.enable_ptp = True
        self.ptp_table.show()
        self.toplevel.resize(1, 1)

    def hidePtPTable(self):
        self.enable_ptp = False
        self.ptp_table.hide()
        self.toplevel.resize(1, 1)

    def setIPv4Manual(self, ipaddr, netmask):
        if ipaddr.lower() == 'dhcp' or ipaddr.lower() == 'ibft':
            return

        if ipaddr is not None:
            self.ipv4_address.set_text(ipaddr)

        if netmask is not None:
            self.ipv4_prefix.set_text(netmask)

    def getIPv4Address(self):
        return self.ipv4_address.get_text()

    def getIPv4Prefix(self):
        return self.ipv4_prefix.get_text()

    

    def setESSID(self, essid):
        if essid is not None: 
            self.essid.set_text(essid)

    def getESSID(self):
        return self.essid.get_text()

    def setEncKey(self, key):
        if key is not None:
            self.enc_key.set_text(key)

    def getEncKey(self):
        return self.enc_key.get_text()

    def setPtP(self, remip):
        if remip is not None:
            self.ptp_address.set_text(remip)

    def getPtP(self):
        return self.ptp_address.get_text()

    def setEnableIPv4(self, enable_ipv4):
        if enable_ipv4 is True:
            self.enable_ipv4.set_active(1)
        elif enable_ipv4 is False:
            self.enable_ipv4.set_active(0)


    def selectIPv4Method(self, ipaddr):
        if ipaddr.lower() == 'dhcp':
            self.dhcp_ipv4.set_active(1)
        elif ipaddr.lower() == 'ibft':
            self.dhcp_ipv4.set_active(1)
        elif ipaddr != "":
            self.manual_ipv4.set_active(1)


    def isIPv4Enabled(self):
        return self.enable_ipv4.get_active()

    def getIPv4Method(self):
        if self.isIPv4Enabled():
            if self.dhcp_ipv4.get_active():
                return 'dhcp'
            elif self.manual_ipv4.get_active():
                return 'static'
            
    # Basic callbacks.
    def destroy(self, args):
        self.toplevel.destroy()


    def cancelClicked(self, args):
        self.valid_input = 3
        self.toplevel.destroy()

    def _setManualIPv4Sensitivity(self, sensitive):
        self.ipv4_address_label.set_sensitive(sensitive)
        self.ipv4_prefix_label.set_sensitive(sensitive)
        self.ipv4_address.set_sensitive(sensitive)
        self.ipv4_slash.set_sensitive(sensitive)
        self.ipv4_prefix.set_sensitive(sensitive)

    def _setIPv4Sensitivity(self, sensitive):
        self.dhcp_ipv4.set_sensitive(sensitive)
        self.manual_ipv4.set_sensitive(sensitive)

        # But be careful to only set these sensitive if their corresponding
        # radiobutton is selected.
        if self.manual_ipv4.get_active():
            self._setManualIPv4Sensitivity(sensitive)

    # Called when the IPv4 and IPv6 CheckButtons are modified.
    def ipv4_toggled(self, args):
        self._setIPv4Sensitivity(self.enable_ipv4.get_active())

    # Called when the dhcp/auto/manual config RadioButtons are modified.
    def ipv4_changed(self, args):
        if False==self.manual_ipv4.get_active():
            self.ipv4_address.set_text("")      
        self.ipv4_prefix.set_text("")
        self._setManualIPv4Sensitivity(self.manual_ipv4.get_active())


class NetworkDeviceCheckList(checklist.CheckList):
    def toggled_item(self, data, row):
        checklist.CheckList.toggled_item(self, data, row)

        if self.clickCB:
            rc = self.clickCB(data, row)
    
    def __init__(self, columns, store, clickCB=None):
        checklist.CheckList.__init__(self, columns=columns,
                     custom_store=store)

        self.clickCB = clickCB
