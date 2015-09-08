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

import installation_type
from constants import *
import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)

dve_dvelist = []
"""global_options = [_(u"网关"), _(u"主DNS"), _(u"从DNS")]
global_option_labels = [_("_Gateway"), _("_Primary DNS"), _("_Secondary DNS")]"""
global_options = [_("Gateway"), _("Primary DNS"), _("Secondary DNS")]
#global_option_labels = [_(u"网  关"), _(u"主 DNS"), _(u"从 DNS")]
global_option_labels = [_(u"网关"), _(u"主DNS"), _(u"从DNS")]
global_dhcp = True

class NetworkWindow(InstallWindow):		
    windowTitle = N_("Network Configuration")

    def __init__(self, ics):
	InstallWindow.__init__(self, ics)

    def NgetNext(self):
        override = 0
        if self.hostnameManual.get_active():
            self.network.hostname_dhcp=False
            hname = string.strip(self.hostnameEntry.get_text())
            neterrors =  network.sanityCheckHostname(hname)
            if neterrors is not None:
                self.handleBadHostname(hname, neterrors)
                raise gui.StayOnScreen
            elif len(hname) == 0:
                hname = self.defaulthostname #"localhost" # ...better than empty
                #if ((len(self.network.dve_dvelist)>0) and
                #    self.handleMissingHostname()):
                if self.handleMissingHostname():
                    raise gui.StayOnScreen

            newHostname = hname
            override = 1
        else:
            self.network.hostname_dhcp=True
            newHostname = self.defaulthostname #"localhost"
            override = 0

       
        if not False:
            tmpvals = {}
            for t in range(len(global_options)):
                try:
                    network.sanityCheckIPString(self.globals[global_options[t]].get_text())
                    tmpvals[t] = self.globals[global_options[t]].get_text()
                except network.IPMissing, msg:
                    #if t<2 and (len(self.network.dve_dvelist)>0):
                    if t<2:
                        if t==1:
                            tmp=u"主DNS"
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
        for x in self.devices:
            if self.devices[x].get('bootproto').lower() == "static" and self.devices[x].get('ipaddr'):
                existip = True
                break
        if not existip:
            if self.handleMissingIp():
                raise gui.StayOnScreen

        iter = self.ethdevices.store.get_iter_first()
        while iter:
            model = self.ethdevices.store
            dev = model.get_value(iter, 1)
            bootproto=self.devices[dev].get('bootproto')
            onboot = model.get_value(iter, 0)

		
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
            onboot="yes"
            self.devices[dev].set(("ONBOOT", onboot))
            self.devices[dev].set(("bootproto", bootproto))
            iter = self.ethdevices.store.iter_next(iter)

	
        self.NgetNext()
        return None

    def setHostOptionsSensitivity(self):
        # figure out if they have overridden using dhcp for hostname
	if network.anyUsingDHCP(self.devices, self.anaconda):
	    self.hostnameUseDHCP.set_sensitive(1)

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
	self.ipTable.set_sensitive(state)

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
                                _(u"无效的主机名\"%s\" : \n\n%s")%(hostname,error))

    def handleIPMissing(self, field):
        self.intf.messageWindow(_("Error With Data"),
            _("A value is required for the field %s.") % (field,))

    def handleIPError(self, field, msg):
        self.intf.messageWindow(_("Error With %s Data") % (field,),
                                _(u"输入错误！") )

    def handleBroadCastError(self):
        self.intf.messageWindow(_("Error With Data"),
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
	self.wireless_table.set_sensitive(True)
	
    def setESSID(self, essid):
        if essid is not None: 
            self.essid.set_text(essid)	 
    def setEncKey(self, key):
        if key is not None:
            self.enc_key.set_text(key)
 
    def hideWirelessTable(self):
        self.enable_wireless = False
	self.wireless_table.set_sensitive(False)
    def isPtPEnabled(self):
        return self.enable_ptp
    def showPtPTable(self):
        self.enable_ptp = True
	self.ptp_table.set_sensitive(True)
    def hidePtPTable(self):
        self.enable_ptp = False
	self.ptp_table.set_sensitive(False)
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
	#self.hardware_address.set_markup("<b>" + _(u"硬件地址: ") + mac + "</b>")
    def editDevice_new(self):
    	selection = self.ethdevices.get_selection()
        (model, iter) = selection.get_selected()
        if not iter:
            return None
        dev = model.get_value(iter, 1)
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

        self.selectIPv4Method(ipaddr)

        if bootproto.lower() == 'dhcp':
            self.ipradio_dhcp.set_active(1)
	    self.ipIPv4.set_sensitive(False)
	    self.ipsubnet.set_sensitive(False)
	    self.ipIPv4.set_text("")
	    self.ipsubnet.set_text("")
	    
        elif bootproto.lower() == 'ibft':
	    self.ipradio_dhcp.set_active(1)
	    self.ipIPv4.set_sensitive(False)
	    self.ipsubnet.set_sensitive(False)
	    self.ipIPv4.set_text("")
	    self.ipsubnet.set_text("")
	elif bootproto != "":
	    self.ipradio_manual.set_active(1)
	    self.ipIPv4.set_sensitive(True)
	    self.ipsubnet.set_sensitive(True)

	#self.setHardwareAddress(self.devices[dev].get('hwaddr'))
        return
    def getIPv4Method(self):
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
	selection = self.ethdevices.get_selection()
	(model, iter) = selection.get_selected()
	if not iter:
	    return None
	dev = model.get_value(iter, 1)
	onboot = model.get_value(iter, 0)
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
		    #self.valid_input = 1
		    return

        if self.isPtPEnabled():
            try:
                network.sanityCheckIPString(self.ptp_address.get_text())
            except network.IPMissing, msg:
                self.handleIPMissing('point-to-point IP address')
                #self.valid_input = 1
                return
            except network.IPError, msg:
                self.handleIPError('point-to-point IP address', msg)
                #self.valid_input = 1
                return

    def setsensitive_false(self):    
        self.edit1.set_sensitive(False)
	self.ipIPv4.set_text("")
	self.ipsubnet.set_text("")
	self.ipIPv4.set_sensitive(False)
	self.ipsubnet.set_sensitive(False)
	self.ipradio_dhcp.set_sensitive(False)
	self.ipradio_manual.set_sensitive(False)
    def setsensitive_true(self):
        self.edit1.set_sensitive(True)
	self.ipIPv4.set_sensitive(True)
	self.ipsubnet.set_sensitive(True)
	self.ipradio_dhcp.set_sensitive(True)
	self.ipradio_manual.set_sensitive(True)
    def on_cursor_changed_a(self,widget):
	self.editDevice_new()
        return False
	
    def setupDevices(self):
        # 检查是否已经配置网True
        try:
            has_set = self.anaconda.has_setupDevices
        except:
            has_set = False
        
        devnames = self.devices.keys()
        devnames.sort()

        store = gtk.TreeStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING,
                             gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.ethdevices = NetworkDeviceCheckList(2, store)    
        self.ethdevices.connect("cursor-changed",self.on_cursor_changed_a)
        device = devnames[0]
        x = 0
        if not has_set:
            x = 1
            self.anaconda.has_setupDevices = True
            self.devices[device].set(("ONBOOT", "yes"))
            self.devices[device].set(("bootproto", "static"))
            self.devices[device].set(("ipaddr","10.0.0.1"))
            self.devices[device].set(("netmask","255.255.255.0"))
            self.ethdevices.append_row((device, "10.0.0.1/24"), True)
            try:
                (net, bc) = isys.inet_calcNetBroad("10.0.0.1","255.255.255.0")
                self.devices[device].set(("network",net))
                self.devices[device].set(("broadcast",bc))
            except Exception, e:
                return
        else:
            pass
        
        for device in devnames[x:]:
            onboot="yes"    
            self.devices[device].set(("ONBOOT",onboot))
            active=False
            if self.network.first_come==1:
                bootproto='dhcp'
                self.devices[device].set(("bootproto",bootproto))
            else:
                pass

            ipv4 = self.createIPV4Repr(self.devices[device])
            self.ethdevices.append_row((device, ipv4), active)

        if self.network.first_come==1:
            self.network.first_come=0      
        self.ethdevices.set_column_title(0, (_(u"加入交换机")))
        self.ethdevices.set_column_sizing (0, gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.ethdevices.set_column_title(1, (_("Device")))
        self.ethdevices.set_column_sizing (1, gtk.TREE_VIEW_COLUMN_FIXED)
        self.ethdevices.set_column_title(2, (_("IPv4/Netmask")))
        self.ethdevices.set_column_sizing (2, gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.ethdevices.set_column_min_width(0,100)
        self.ethdevices.set_column_min_width(1,100)
        self.ethdevices.set_column_min_width(2,95)
        self.ethdevices.set_headers_visible(True)
        l0=self.ethdevices.get_column(0)
        l0.set_visible(False)
        self.ignoreEvents = 1
        iter = self.ethdevices.store.get_iter_first()
        selection = self.ethdevices.get_selection()
        selection.set_mode(gtk.SELECTION_BROWSE)
        selection.select_iter(iter)
        self.ignoreEvents = 0
        return self.ethdevices

    # NetworkWindow tag="netconf"
    
            

    def ipv4_add(self,ipv4_box):
        self.hardware_address=gtk.Label(u"硬件地址:")
	align1=gtk.Alignment(0,0,0,0)
        """label_1.set_markup("<b>%s</b>" %(_(u"只能选择一个网卡加入交换机！"),))
	ipv4_box.pack_start(align1,False)"""
        ipv4_label=gtk.Label()
        ipv4_label.set_markup("<b>%s</b>" %(_(u"IPv4设置："),))
	ipv4_label.set_alignment(0.0,0.0)
	ipv4_box.pack_start(ipv4_label,False,False,0)

	self.ipradio_dhcp=gtk.RadioButton(None,u"自动设置")
	ipv4_box.pack_start(self.ipradio_dhcp,True,True,0)
	self.ipradio_manual=gtk.RadioButton(self.ipradio_dhcp,u"手动设置")
	ipv4_box.pack_start(self.ipradio_manual,True,True,0)

	iphbox=gtk.VBox(False,0)
	iphbox.set_spacing(4)

        tmphbox=gtk.HBox(False,0)
        """tmphbox.set_spacing(4)"""
	"""align1=gtk.Alignment(0,0,0,0)"""
	iplabel_IP=gtk.Label(u" IP地址 :  ")
	iplabel_IP.set_width_chars(8)
	"""align1.add(iplabel_IP)"""
	tmphbox.pack_start(iplabel_IP,False,False,0)
	self.ipIPv4=gtk.Entry()
	self.ipIPv4.set_width_chars(30)
	align2=gtk.Alignment(0,0,0,0)
	align2.add(self.ipIPv4)
	tmphbox.pack_start(align2,False,False,0)
	iphbox.pack_start(tmphbox,False,False,0)
        
        tmphbox1=gtk.HBox(False,0)
        """tmphbox1.set_spacing(4)"""
	iplabel_subnet=gtk.Label(u" 子网掩码 :  ")
	iplabel_subnet.set_width_chars(8)
	"""align3=gtk.Alignment(0,0,0,0)
	align3.add(iplabel_subnet)"""
	tmphbox1.pack_start(iplabel_subnet,False,False,0)
	self.ipsubnet=gtk.Entry()
	self.ipsubnet.set_width_chars(30)
	align4=gtk.Alignment(0,0,0,0)
	align4.add(self.ipsubnet)
	tmphbox1.pack_start(align4,False,False,0)

        self.edit1=gtk.Button(_(u"设置"))
        self.edit1.connect("clicked",self.editDevice)
        self.edit1.set_size_request(50,-1)
        align_edit1=gtk.Alignment(0,0,0,0)
        align_edit1.add(self.edit1)
        tmphbox1.pack_start(align_edit1,False,False,0)

        ip_help_label_subnet=gtk.Label(u"(注意：必须点击“设置”按钮，IP配置才会生效！)")
        tmphbox1.pack_start(ip_help_label_subnet,False,False,0)

        iphbox.pack_start(tmphbox1,False,False,0)
	ipv4_box.pack_start(iphbox,False,False,0)
	self.ipradio_dhcp.connect("toggled",self.ipv4_changed)
	self.ipradio_manual.connect("toggled",self.ipv4_changed)
        
        
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
    def ipv4_changed(self,args):
	if False==self.ipradio_manual.get_active():
	    self.ipIPv4.set_text("")
	    self.ipsubnet.set_text("")
	self._setManualIPv4Sensitivity(self.ipradio_manual.get_active())
    

    def hostnameUseDHCPCB(self, widget, data):
        self.network.overrideDHCPhostname = 0
        self.hostnameEntry.set_text(self.defaulthostname)
        self.hostnameEntry.set_sensitive(not widget.get_active())
    def hostnameManualCB(self, widget, data):
        self.network.overrideDHCPhostname = 1
        if widget.get_active():
            self.hostnameEntry.grab_focus()

    def make_ip_box(self,hbox):
        
        ipbox = gtk.VBox()
        l=gtk.Label()
        l.set_markup("<b>%s</b>" %(_(u"IPv4设置："),))
        l.set_alignment(0.0,0.0)
        tmphbox = gtk.HBox()
        tmphbox.pack_start(l,False,False,0)
        ipbox.pack_start(tmphbox,False,False,3)

        tmphbox = gtk.HBox()        
        self.ipradio_dhcp=gtk.RadioButton(None,u"自动设置")
        tmphbox.pack_start(self.ipradio_dhcp,True,True,0)
        ipbox.pack_start(tmphbox,False,False,3)
        
        tmphbox = gtk.HBox()
        self.ipradio_manual=gtk.RadioButton(self.ipradio_dhcp,u"手动设置")
        tmphbox.pack_start(self.ipradio_manual,True,True,0)
        ipbox.pack_start(tmphbox,False,False,3)
        
        tmphbox=gtk.HBox(False,0)
        iplabel_IP=gtk.Label(u"IP地址:")
        iplabel_IP.set_width_chars(7)
        iplabel_IP.set_alignment(1.0, 0.5)
        tmphbox.pack_start(iplabel_IP,False,False,15)
        self.ipIPv4=gtk.Entry()
        self.ipIPv4.set_width_chars(28)
        align2=gtk.Alignment(0,0,0,0)
        align2.add(self.ipIPv4)
        tmphbox.pack_start(align2,False,False,0)
        ipbox.pack_start(tmphbox,False,False,3)
        
        tmphbox1=gtk.HBox(False,0)
        iplabel_subnet=gtk.Label(u"子网掩码:")
        iplabel_subnet.set_width_chars(7)
        iplabel_subnet.set_alignment(1.0, 0.5)
        tmphbox1.pack_start(iplabel_subnet,False,False,15)
        self.ipsubnet=gtk.Entry()
        self.ipsubnet.set_width_chars(28)
        align4=gtk.Alignment(0,0,0,0)
        align4.add(self.ipsubnet)
        tmphbox1.pack_start(align4,False,False,0)

        self.edit1=gtk.Button(_(u"设置"))
        self.edit1.connect("clicked",self.editDevice)
        self.edit1.set_size_request(40,25)
        align_edit1=gtk.Alignment(0.5,0.5,0,0)
        align_edit1.add(self.edit1)
        tmphbox1.pack_start(align_edit1,False,False,5)

        ip_help_label_subnet=gtk.Label(u"(注意：必须点击“设置”按钮，IP配置才会生效！)")
        tmphbox1.pack_start(ip_help_label_subnet,False,False,10)

        ipbox.pack_start(tmphbox1,False,False,3)
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
   
    def make_other_box(self,hbox):
        
        vbox = gtk.VBox()
        tmphbox = gtk.HBox()
        l = gtk.Label()
        l.set_markup("<b>%s</b>" %(_("其他设置:"),))
        tmphbox.pack_start(l,False,False,0)
        vbox.pack_start(tmphbox,False,False,3)

        options = {}
        for i in range(len(global_options)):
            tmphbox = gtk.HBox()
            label = gtk.Label("%s:" %(global_option_labels[i],))
            label.set_property("use-underline", True)
            label.set_alignment(1.0, 0.5)
            label.set_width_chars(7)
            tmphbox.pack_start(label,False,False,15)
            align = gtk.Alignment(0, 0.5)
            options[i] = gtk.Entry()
            options[i].set_width_chars(28)
            align.add(options[i])
            label.set_mnemonic_widget(options[i])

            tmphbox.pack_start(align,False,False,0)
            vbox.pack_start(tmphbox,False,False,3)

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

        hbox.pack_start(vbox, False, False)
        
    def make_hostname_box(self,hbox):
        
        hostbox=gtk.VBox()
    
        tmphbox = gtk.HBox()
        l = gtk.Label()
        l.set_markup("<b>%s</b>" %(_(u"主机名设置:"),))
        tmphbox.pack_start(l,False,False)
        hostbox.pack_start(tmphbox,False,False,3)

        tmphbox=gtk.HBox()
        self.hostnameUseDHCP = gtk.RadioButton(label=_(u"自动设置"))
        self.hostnameUseDHCP.connect("toggled", self.hostnameUseDHCPCB, None)
        tmphbox.pack_start (self.hostnameUseDHCP, False, False)
        hostbox.pack_start(tmphbox, False, False,3)

        tmphbox=gtk.HBox()
        
        self.hostnameManual = gtk.RadioButton(group=self.hostnameUseDHCP, label=_(u"手动设置"))
        tmphbox.pack_start(self.hostnameManual, False, False,0)
        self.hostnameEntry = gtk.Entry()
        self.hostnameEntry.set_width_chars(28)
        self.hostnameEntry.connect('insert-text',self.hinsert_text)
        tmphbox.pack_start(self.hostnameEntry, False, False,10)
        tmphbox.pack_start(gtk.Label(_(u'(例如：localhost)')), False, False,50)
        self.hostnameManual.connect("toggled", self.hostnameManualCB, None)
        hostbox.pack_start(tmphbox, False, False,3)

        hbox.pack_start(hostbox, False, False)

    def hinsert_text(self,entry,new_text, new_text_length, position):
        if len(entry.get_text())+len(new_text)>64:
            entry.stop_emission('insert-text')
        str = string.ascii_letters+string.digits+".-"
        for c in new_text:
            if c not in str:
                entry.stop_emission('insert-text')

    def make_tree_box(self,hbox):
        
        treebox = gtk.VBox()
        
        tmphbox = gtk.HBox()
        l = gtk.Label()
        l.set_markup("<b>%s</b>" %(_(u"网络设备:"),))
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
        
        treebox.pack_start(devhbox,False,False,3)

        hbox.pack_start(treebox, False)
 
    def getScreen(self, anaconda):
        self.intf = anaconda.intf
        self.id = anaconda.id
        self.anaconda = anaconda
        ############################################
        
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
        lstr = "<span font_desc=' 16' weight='bold' foreground='"+fontcolor+"'><b>网络配置:</b></span>"
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

        if not self.devices:
            return None

        self.numdevices = len(self.devices.keys())

        self.hostname = self.network.hostname
        ##############################################
        """devhbox = gtk.HBox(False)
        devhbox.set_spacing(12)

        self.devlist = self.setupDevices()

	devlistSW = gtk.ScrolledWindow()
        devlistSW.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        devlistSW.set_shadow_type(gtk.SHADOW_IN)
        devlistSW.add(self.devlist)
	devlistSW.set_size_request(-1, 100)
	devhbox.pack_start(devlistSW, False)
        

        l = gtk.Label()
        l.set_markup("<b>%s</b>" %(_(u"网络设备：\n"),))
	frame=gtk.Frame()
        frame.set_label_widget(l)
	frame.add(devhbox)
        frame.set_shadow_type(gtk.SHADOW_NONE)
	box1.pack_start(frame, False)
	box.pack_start(box1, False)"""

        boxall = gtk.VBox()
        hbox1 = gtk.HBox(False)
        self.make_tree_box(hbox1)
        boxall.pack_start(hbox1,False,5)
 
        ##################################################################	
        """box2=gtk.VBox(False)
        box2.set_spacing(8)
        self.ipv4_add(box2)
        box.pack_start(box2,False)"""
        hbox1=gtk.HBox(False)
        self.make_ip_box(hbox1)
        boxall.pack_start(hbox1,False,5) 
       
        self.editDevice_new()	

        ###################################################################### 

        if not self.devices:
            return None

        self.numdevices = len(self.devices.keys())

        self.hostname = self.network.hostname
        """hostbox=gtk.VBox()
        hostbox.set_spacing(6)  

        tmphbox=gtk.HBox()
        self.hostnameUseDHCP = gtk.RadioButton(label=_("_automatically via DHCP"))
        self.hostnameUseDHCP.connect("toggled", self.hostnameUseDHCPCB, None)
        tmphbox.pack_start (self.hostnameUseDHCP, False, False)
        hostbox.pack_start(tmphbox, False, False)

        tmphbox=gtk.HBox()
        self.hostnameManual = gtk.RadioButton(group=self.hostnameUseDHCP, label=_("_manually"))
        tmphbox.pack_start(self.hostnameManual, False, False)
        self.hostnameEntry = gtk.Entry()
        self.hostnameEntry.set_width_chars(28)
        tmphbox.pack_start(self.hostnameEntry, False, False)
        tmphbox.pack_start(gtk.Label(_(u'(例如：localhost)')), False, False)
        self.hostnameManual.connect("toggled", self.hostnameManualCB, None)
        hostbox.pack_start(tmphbox, False, False)
        
        l = gtk.Label()
        l.set_markup("<b>%s</b>" %(_(u"主机名设置：\n"),))
        frame=gtk.Frame()
        frame.set_label_widget(l)
        frame.add(hostbox)
        frame.set_shadow_type(gtk.SHADOW_NONE)
        box.pack_start(frame, False, False)"""

        hbox1 = gtk.HBox(False)
        self.make_hostname_box(hbox1)
        boxall.pack_start(hbox1, False, False,5)
        ######################################################################
        """self.ipTable = gtk.Table(len(global_options), 2)
        options = {}
        for i in range(len(global_options)):
            label = gtk.Label("%s:" %(global_option_labels[i],))
            label.set_property("use-underline", True)
            label.set_alignment(0.0, 0.0)
            self.ipTable.attach(label, 0, 1, i, i+1, gtk.FILL, 0)
            align = gtk.Alignment(0, 0.5)
            options[i] = gtk.Entry()
            options[i].set_width_chars(32)
            align.add(options[i])
            label.set_mnemonic_widget(options[i])

            self.ipTable.attach(align, 1, 2, i, i+1, gtk.FILL, 0)

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

        l = gtk.Label()
        l.set_markup("<b>%s</b>" %(_("其他设置：\n"),))
        frame=gtk.Frame()
       
        if False:
            pass
        else:
            frame.set_label_widget(l)

        if False:
            pass
        else:
            frame.add(self.ipTable)

        frame.set_shadow_type(gtk.SHADOW_NONE)
        box.pack_start(frame, False, False)"""
        hbox1 = gtk.HBox(False)
        self.make_other_box(hbox1)
        boxall.pack_start(hbox1, False, False,5)
        
        fix = gtk.Fixed()
        fix.put(boxall,40,20)
        box.pack_start(fix,True,True) 
        ####################################################################
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
        #import pdb
	#pdb.set_trace()
        if mac is None:
            mac = _('unknown')

        #self.hardware_address.set_markup("<b>" + _(u"硬件地址: ") + mac + "</b>")

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

    #def setEnableIPv6(self, enable_ipv6):
    #    if enable_ipv6 is True:
    #        self.enable_ipv6.set_active(1)
    #    elif enable_ipv6 is False:
    #        self.enable_ipv6.set_active(0)

    def selectIPv4Method(self, ipaddr):
        if ipaddr.lower() == 'dhcp':
            self.dhcp_ipv4.set_active(1)
        elif ipaddr.lower() == 'ibft':
            self.dhcp_ipv4.set_active(1)
        elif ipaddr != "":
            self.manual_ipv4.set_active(1)

    #def selectIPv6Method(self, ipv6_autoconf, ipv6addr):
    #    if ipv6_autoconf.lower() == 'yes':
    #        self.auto_ipv6.set_active(1)
    #    elif ipv6addr.lower() == 'dhcp':
    #        self.dhcp_ipv6.set_active(1)
    #    elif ipv6addr != "":
    #        self.manual_ipv6.set_active(1)

    def isIPv4Enabled(self):
        return self.enable_ipv4.get_active()

    def getIPv4Method(self):
        if self.isIPv4Enabled():
            if self.dhcp_ipv4.get_active():
                return 'dhcp'
            elif self.manual_ipv4.get_active():
                return 'static'

    #def isIPv6Enabled(self):
    #    return self.enable_ipv6.get_active()

    #def getIPv6Method(self):
    #    if self.isIPv6Enabled():
    #        if self.auto_ipv6.get_active():
    #            return 'auto'
    #        elif self.dhcp_ipv6.get_active():
    #            return 'dhcp'
    #        elif self.manual_ipv6.get_active():
    #            return 'static'

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

    #def _setManualIPv6Sensitivity(self, sensitive):
    #    self.ipv6_address_label.set_sensitive(sensitive)
    #    self.ipv6_prefix_label.set_sensitive(sensitive)
    #    self.ipv6_address.set_sensitive(sensitive)
    #    self.ipv6_slash.set_sensitive(sensitive)
    #    self.ipv6_prefix.set_sensitive(sensitive)

    def _setIPv4Sensitivity(self, sensitive):
        self.dhcp_ipv4.set_sensitive(sensitive)
        self.manual_ipv4.set_sensitive(sensitive)

        # But be careful to only set these sensitive if their corresponding
        # radiobutton is selected.
        if self.manual_ipv4.get_active():
            self._setManualIPv4Sensitivity(sensitive)

    #def _setIPv6Sensitivity(self, sensitive):
    #    self.auto_ipv6.set_sensitive(sensitive)
    #    self.dhcp_ipv6.set_sensitive(sensitive)
    #    self.manual_ipv6.set_sensitive(sensitive)

        # But be careful to only set these sensitive if their corresponding
        # radiobutton is selected.
    #    if self.manual_ipv6.get_active():
    #        self._setManualIPv6Sensitivity(sensitive)

    # Called when the IPv4 and IPv6 CheckButtons are modified.
    def ipv4_toggled(self, args):
        self._setIPv4Sensitivity(self.enable_ipv4.get_active())

    #def ipv6_toggled(self, args):
    #    self._setIPv6Sensitivity(self.enable_ipv6.get_active())

    # Called when the dhcp/auto/manual config RadioButtons are modified.
    def ipv4_changed(self, args):
        if False==self.manual_ipv4.get_active():
            self.ipv4_address.set_text("")      
	    self.ipv4_prefix.set_text("")
        self._setManualIPv4Sensitivity(self.manual_ipv4.get_active())

    #def ipv6_changed(self, args):
    #    self._setManualIPv6Sensitivity(self.manual_ipv6.get_active())


class NetworkDeviceCheckList(checklist.CheckList):
    def toggled_item(self, data, row):
	checklist.CheckList.toggled_item(self, data, row)

	if self.clickCB:
	    rc = self.clickCB(data, row)
    
    def __init__(self, columns, store, clickCB=None):
	checklist.CheckList.__init__(self, columns=columns,
				     custom_store=store)

	self.clickCB = clickCB
