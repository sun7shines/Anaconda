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
import network_gui
from constants import *
import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)

#dve_dvelist = []
global_options = [_("Gateway"), _("Primary DNS"), _("Secondary DNS")]
global_option_labels = [_("_Gateway"), _("_Primary DNS"), _("_Secondary DNS")]
global_dhcp = True
class NetworkNextWindow(InstallWindow):		
    windowTitle = N_("Network Configuration")

    def __init__(self, ics):
	InstallWindow.__init__(self, ics)

    def getNext(self):
        #global dve_dvelist
        #global global_dhcp
        #import pdb
        #pdb.set_trace()

        """br0_ip = string.strip(self.ipv4_a.get_text())
        br0_pr = string.strip(self.subnet_a.get_text())
        print br0_ip,br0_pr
        if len(self.network.dve_dvelist) > 0:
            if self.radioDHCP_a.get_active():
                self.network.r_button_dhcp = True
            else:
                try:
                    network.sanityCheckIPString(self.ipv4_a.get_text())
                except network.IPMissing, msg:
                    self.handleMissingOptionalIP("Bridge IP")
                    raise gui.StayOnScreen
                except network.IPError, msg:
                    self.handleIPError('Bridge IP', msg)
                    raise gui.StayOnScreen


                val = self.subnet_a.get_text()
                if val.find('.') == -1:
		    #import pdb
		    #pdb.set_trace()
                # user provided a CIDR prefix
                    try:
                        if int(val) > 32 or int(val) < 0:
                            self.intf.messageWindow(_("Invalid Prefix"),
                                                    _("Bridge Mask"
                                                      "must be between "
                                                      "0 and 32."))
                            raise gui.StayOnScreen
                    except:
                        # self.handleIPMissing('Bridge Mask')
                        raise gui.StayOnScreen
		    #import pdb
		    #pdb.set_trace()
		    br0_pr=isys.prefix2netmask(int(val))
                else:
                # user provided a dotted-quad netmask
                    try:
                        network.sanityCheckIPString(self.subnet_a.get_text())
                    except network.IPMissing, msg:
                        self.handleIPMissing('Bridge Mask')
                        raise gui.StayOnScreen
                    except network.IPError, msg:
                        self.handleIPError('Bridge Mask', msg)
                        raise gui.StayOnScreen
        self.network.br0_ip = br0_ip
        self.network.br0_pr = br0_pr"""
        #self.network.dve_dvelist = dve_dvelist

	#if self.getNumberActiveDevices() == 0:
	    #pass
	    #rc = self.handleNoActiveDevices()
	    #if not rc:
	    #	raise gui.StayOnScreen

	override = 0
	if self.hostnameManual.get_active():
            #global_dhcp=False 
            self.network.hostname_dhcp=False
	    hname = string.strip(self.hostnameEntry.get_text())
	    neterrors =  network.sanityCheckHostname(hname)
	    if neterrors is not None:
		self.handleBadHostname(hname, neterrors) 
		raise gui.StayOnScreen
            #if hname.find('.')!=-1:
                #self.hostnameEntry.set_text(u"主机名不能包含“.”!")
                #raise gui.StayOnScreen
            elif len(hname) == 0:
                hname = "localhost" # ...better than empty
		#if ((self.getNumberActiveDevices() > 0) and
		if ((len(self.network.dve_dvelist)>0) and 
                    self.handleMissingHostname()):
		    raise gui.StayOnScreen

	    newHostname = hname
            override = 1
	else:
            self.network.hostname_dhcp=True
	    newHostname = "localhost"
	    override = 0

	# If we're not using DHCP, skip setting up the network config
	# boxes.  Otherwise, don't clear the values out if we are doing
	# kickstart since we could be in interactive mode.  Don't want to
	# write out a broken resolv.conf later on, after all.
	#if not network.anyUsingDHCP(self.devices, self.anaconda):
	if not False:
	    tmpvals = {}
	    for t in range(len(global_options)):
		try:
                    network.sanityCheckIPString(self.globals[global_options[t]].get_text())
		    tmpvals[t] = self.globals[global_options[t]].get_text()
		except network.IPMissing, msg:
                    #if t < 2 and self.getNumberActiveDevices() > 0:
		    if t<2 and (len(self.network.dve_dvelist)>0):
			if self.handleMissingOptionalIP(global_options[t]):
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

        """iter = self.ethdevices.store.get_iter_first()
	while iter:
	    model = self.ethdevices.store
	    dev = model.get_value(iter, 1)
	    bootproto = model.get_value(iter, 2)
	    onboot = model.get_value(iter, 0)

	    if onboot:
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
            iter = self.ethdevices.store.iter_next(iter)"""

	self.network.hostname = newHostname
	self.network.overrideDHCPhostname = override
         
	
        """if self.dhcp_a_yes==False:
                try:
                    network.sanityCheckIPString(self.ipv4_a.get_text())
                except network.IPMissing, msg:
                    #self.netwin.handleIPMissing('IPv4 address')
                    #self.valid_input = 1
                    return
                except network.IPError, msg:
                    #self.netwin.handleIPError('IPv4 address', msg)
                    #self.valid_input = 1
                    return

                val = self.subnet_a.get_text()
                if val.find('.') == -1:
                    # user provided a CIDR prefix
                    try:
                        if int(val) > 32 or int(val) < 0:
                            self.netwin.intf.messageWindow(_("Invalid Prefix"),
                                                           _("IPv4 prefix "
                                                             "must be between "
                                                             "0 and 32."))
                            self.valid_input = 1
                            return
                        else:
                            self.subnet_a.set_text(isys.prefix2netmask(int(val)))
                    except:
                        self.netwin.handleIPMissing('IPv4 network mask')
                        self.valid_input = 1
                        return
                else:
                    # user provided a dotted-quad netmask
                    try:
                        network.sanityCheckIPString(self.subnet_a.get_text())
                    except network.IPMissing, msg:
                        #self.netwin.handleIPMissing('IPv4 network mask')
                        #self.valid_input = 1
                        return
                    except network.IPError, msg:
                        #self.netwin.handleIPError('IPv4 network mask', msg)
                        #self.valid_input = 1
                        return"""
        return None

    def setHostOptionsSensitivity(self):
        # figure out if they have overridden using dhcp for hostname
	if network.anyUsingDHCP(self.devices, self.anaconda):
	    self.hostnameUseDHCP.set_sensitive(1)

	    if self.hostname != "localhost" and self.network.overrideDHCPhostname:
		self.hostnameManual.set_active(1)
		self.hostnameManual.set_sensitive(1)
	    else:
		self.hostnameUseDHCP.set_active(1)
	else:
	    self.hostnameManual.set_active(1)
	    #self.hostnameUseDHCP.set_sensitive(0)
	    self.hostnameUseDHCP.set_sensitive(1)

    def setIPTableSensitivity(self):
	numactive = self.getNumberActiveDevices()
	#if numactive == 0:
	#    state = False
	#else:
	#state = not network.anyUsingDHCP(self.devices, self.anaconda)
        state=True
	self.ipTable.set_sensitive(state)

    def handleMissingHostname(self):
	return not self.intf.messageWindow(_("Error With Data"),
				_(u"您还没有设置主机名，这在某些网络环境下可能会引起错误。"), type="custom", custom_buttons=["gtk-cancel", _("C_ontinue")])

    def handleMissingOptionalIP(self, field):
	return not self.intf.messageWindow(_("Error With Data"),
				_(u"您还没有设置\"%s\"选项，这在某些网络环境下可能会引起错误。") % (field,), type="custom", custom_buttons=["gtk-cancel", _("C_ontinue")])

    def handleBadHostname(self, hostname, error):
	self.intf.messageWindow(_("Error With Data"),
				#_("The hostname \"%s\" is not valid for the following reason:\n\n%s") % (hostname, error))
                                _(u"无效的主机名\"%s\" : \n\n%s")%(hostname,error))

    def handleIPMissing(self, field):
	self.intf.messageWindow(_("Error With Data"),
	    _("A value is required for the field %s.") % (field,))

    def handleIPError(self, field, msg):
	self.intf.messageWindow(_("Error With %s Data") % (field,),
				_("Input error") )
	                       # _("%s") % msg.__str__())

    def handleBroadCastError(self):
	self.intf.messageWindow(_("Error With Data"),
				#_("The IPv4 information you have entered is "
				  #"invalid."))
                                _(u"输入的IPv4信息无效。"))
    def handleNoActiveDevices(self):
	return self.intf.messageWindow(_("Error With Data"), _("You have no active network devices.  Your system will not be able to communicate over a network by default without at least one device active."), type="custom", custom_buttons=["gtk-cancel", _("C_ontinue")])
    
    def editDevice(self, data):
	#global dve_dvelist
        selection = self.ethdevices.get_selection()
        (model, iter) = selection.get_selected()
        if not iter:
            return None
        dev = model.get_value(iter, 1)
        bootproto = model.get_value(iter, 2)
        onboot = model.get_value(iter, 0)

        # create dialog box for editing this interface
        editwin = NetworkDeviceEditWindow(self)
        editwin.setTitle(dev)
        editwin.setDescription(self.devices[dev].get('desc'))
        editwin.setHardwareAddress(self.devices[dev].get('hwaddr'))

        ipaddr = self.devices[dev].get('ipaddr')
        netmask = self.devices[dev].get('netmask')
        editwin.setIPv4Manual(ipaddr, netmask)

        #ipv6_autoconf = self.devices[dev].get('ipv6_autoconf')
        #ipv6addr = self.devices[dev].get('ipv6addr')
        #ipv6prefix = self.devices[dev].get('ipv6prefix')
        #brk = ipv6addr.find('/')
        #if brk != -1:
        #    ipv6addr = ipv6addr[0:brk]
        #    brk += 1
        #    ipv6prefix = ipv6addr[brk:]
        #editwin.setIPv6Manual(ipv6addr, ipv6prefix)

        if isys.isWireless(dev):
            editwin.showWirelessTable()
            editwin.setESSID(self.devices[dev].get('essid'))
            editwin.setEncKey(self.devices[dev].get('key'))
        else:
            editwin.hideWirelessTable()

        if network.isPtpDev(dev):
            editwin.showPtPTable()
            editwin.setPtP(self.devices[dev].get('remip'))
        else:
            editwin.hidePtPTable()

        editwin.setEnableIPv4(self.devices[dev].get('useIPv4'))
        editwin.selectIPv4Method(ipaddr)

        #editwin.setEnableIPv6(self.devices[dev].get('useIPv6'))
        #editwin.selectIPv6Method(ipv6_autoconf, ipv6addr)

        rc = 1
        while rc == 1:
            editwin.run()
            rc = editwin.getInputValidationResults()
            if rc == 3:
                return

        # collect results
        useipv4 = editwin.isIPv4Enabled()
        #useipv6 = editwin.isIPv6Enabled()

        self.devices[dev].set(('useIPv4', useipv4))
        #self.devices[dev].set(('useIPv6', useipv6))

        if useipv4:
            bootproto = editwin.getIPv4Method()
            if bootproto == 'dhcp' or bootproto == 'ibft':
                self.devices[dev].set(('ipaddr', bootproto))
                self.devices[dev].set(('network', ''), ('broadcast', ''))
            elif bootproto == 'static':
                try:
                    (net, bc) = isys.inet_calcNetBroad(editwin.getIPv4Address(),
                                                       editwin.getIPv4Prefix())
                    self.devices[dev].set(('network', net), ('broadcast', bc))
                except Exception, e:
                    self.handleBroadCastError()
                    return

                self.devices[dev].set(('ipaddr', editwin.getIPv4Address()))
                self.devices[dev].set(('netmask', editwin.getIPv4Prefix()))

        #if useipv6:
        #    method = editwin.getIPv6Method()

        #    if method == 'auto':
        #        self.devices[dev].set(('ipv6_autoconf', 'yes'))
        #        self.devices[dev].set(('ipv6addr', ''))
        #        self.devices[dev].set(('ipv6prefix', ''))
        #    elif method == 'dhcp':
        #        self.devices[dev].set(('ipv6_autoconf', 'no'))
        #        self.devices[dev].set(('ipv6addr', 'dhcp'))
        #        self.devices[dev].set(('ipv6prefix', ''))
        #    elif method == 'static':
        #        self.devices[dev].set(('ipv6_autoconf', 'no'))
        #        self.devices[dev].set(('ipv6addr', editwin.getIPv6Address()))
        #        self.devices[dev].set(('ipv6prefix', editwin.getIPv6Prefix()))

        if editwin.isWirelessEnabled():
            self.devices[dev].set(('essid', editwin.getESSID()))
            self.devices[dev].set(('key', editwin.getEncKey()))

        if editwin.isPtPEnabled():
            self.devices[dev].set(('remip', editwin.getPtP()))

        self.devices[dev].set(('bootproto', bootproto))

        if onboot:
            self.devices[dev].set(('onboot', 'yes'))
        else:
            self.devices[dev].set(('onboot', 'no'))
        """if 1:
            onboot = False
            self.devices[dev].set(('onboot', 'no'))
            if dev in dve_dvelist:
                dve_dvelist.remove(dev)
            if len(dve_dvelist) == 0:
                self.hostbox1.set_sensitive(False)
                self.hostbox1_flag = 1
        print dve_dvelist"""

        model.set_value(iter, 0, onboot)
        model.set_value(iter, 2, self.createIPV4Repr(self.devices[dev]))
        #model.set_value(iter, 3, self.createIPV6Repr(self.devices[dev]))

        editwin.close()

        #self.setIPTableSensitivity()
        #self.setHostOptionsSensitivity()
        #state=not network.anyUsingDHCP(self.devices, self.anaconda)
	#state=not (not network.anyUsingDHCP(self.devices, self.anaconda))  #3
	#self.edit1.set_sensitive(state)
        return

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

    #def createIPV6Repr(self, device):
    #    if device.get('useIPv6') is False:
    #	    return _("Disabled")

    #    auto = device.get('ipv6_autoconf').lower()
    #    addr = device.get('ipv6addr').lower()
    #    pfx = device.get('ipv6prefix').lower()

    #    if auto == 'yes' or addr == '':
    #        ip = 'Auto'
    #    elif addr == 'dhcp':
    #	    ip = 'DHCPv6'
    #	else:
    #	    ip = "%s/%s" % (addr, pfx,)

    #	return ip

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
        """a = 0
        b = 0
        for device in self.devices.keys():
            bootproto = self.devices[device].get("bootproto")

            if bootproto and bootproto.lower() == 'static':
#                if not self.r_button1.get_active():
                a = 1
#                if self.hostbox1_flag == 0:
#                    if self.r_button1.get_active():
#                        a = 0
#                return 0

            if bootproto and bootproto.lower() == 'dhcp':
                onboot = self.devices[device].get("ONBOOT")
                if onboot == "no":
                    b = 1
#               return 1
        if b == 1:
            return 1

        if a == 1:
            if self.hostbox1_flag == 0:
                if self.r_button1.get_active():
                    return 1
                else:
                    return 0
            else:
                return 0
        if a == 0:
            if self.r_button1.get_active():
                return 1
            else:
                return 0"""
    def on_cursor_changed_a(self,widget):
        global dve_dvelist
        iter=widget.get_selection().get_selected()[1]
	model = self.ethdevices.get_model()
	val=model.get_value(iter,0)
	if val:
            self.edit1.set_sensitive(False)
	else:
	    self.edit1.set_sensitive(True)
        return False
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
	    
            model.set_value(iter, 0, onboot)
            model.set_value(iter, 2, self.createIPV4Repr(self.devices[dev])
)
            self.edit1.set_sensitive(False)
            if dev in dve_dvelist:
                pass
            else:
                dve_dvelist.append(dev)
            if len(dve_dvelist) > 0:
		self.globals[_("Gateway")].set_sensitive(True)
		self.globals[_("Primary DNS")].set_sensitive(True)
		self.globals[_("Secondary DNS")].set_sensitive(True)    
            #    self.hostbox1.set_sensitive(True)
            #    self.hostbox1_flag = 0	    
	else:
	    onboot = "no"
            self.edit1.set_sensitive(True)
            if dev in dve_dvelist:
                dve_dvelist.remove(dev)
            if len(dve_dvelist) == 0:
		self.globals[_("Gateway")].set_text("")
		self.globals[_("Primary DNS")].set_text("")
	 	self.globals[_("Secondary DNS")].set_text("")
                self.globals[_("Gateway")].set_sensitive(False)
		self.globals[_("Primary DNS")].set_sensitive(False)
		self.globals[_("Secondary DNS")].set_sensitive(False)
                """self.hostbox1.set_sensitive(False)
                self.hostbox1_flag = 1
        print dve_dvelist"""	    
	self.devices[dev].set(("ONBOOT", onboot))
	
	#state=not (not network.anyUsingDHCP(self.devices, self.anaconda)) #1
	#self.edit1.set_sensitive(state)
	#self.setIPTableSensitivity
	#self.setHostOptionsSensitivity
	
	return
    
	
    def setupDevices(self):
	global dve_dvelist
	devnames = self.devices.keys()
	devnames.sort()

	store = gtk.TreeStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING,
	                      gobject.TYPE_STRING, gobject.TYPE_STRING)
	
	self.ethdevices = NetworkDeviceCheckList(2, store, clickCB=self.onbootToggleCB)
	self.ethdevices.connect("cursor-changed",self.on_cursor_changed_a)
        num = 0
        for device in devnames:
            if device not in dve_dvelist:
                dve_dvelist.append(device)
#            onboot = self.devices[device].get("ONBOOT")
#            if not onboot:
            onboot = "yes"
            self.devices[device].set(("ONBOOT", onboot))

	    onboot = self.devices[device].get("ONBOOT")
	    if ((num == 0 and not onboot) or onboot == "yes"):
		active = True
	    else:
		active = False

	    #bootproto = self.devices[device].get("bootproto")
            #if not bootproto:
	    bootproto = 'dhcp'
	    self.devices[device].set(("bootproto", bootproto))
		
	    ipv4 = self.createIPV4Repr(self.devices[device])
	    #ipv6 = self.createIPV6Repr(self.devices[device])
            self.ethdevices.append_row((device, ipv4), active)

            num += 1

	self.ethdevices.set_column_title(0, (_(u"是否加入交换机")))
        self.ethdevices.set_column_sizing (0, gtk.TREE_VIEW_COLUMN_GROW_ONLY)
	self.ethdevices.set_column_title(1, (_("Device")))
        self.ethdevices.set_column_sizing (1, gtk.TREE_VIEW_COLUMN_GROW_ONLY)
	self.ethdevices.set_column_title(2, (_("IPv4/Netmask")))
        self.ethdevices.set_column_sizing (2, gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        #self.ethdevices.set_column_title (3, (_("IPv6/Prefix")))
        #self.ethdevices.set_column_sizing (3, gtk.TREE_VIEW_COLUMN_GROW_ONLY)
        self.ethdevices.set_headers_visible(True)

	self.ignoreEvents = 1
	iter = self.ethdevices.store.get_iter_first()
	selection = self.ethdevices.get_selection()
	selection.set_mode(gtk.SELECTION_BROWSE)
	selection.select_iter(iter)
	self.ignoreEvents = 0

	return self.ethdevices

    def hostnameUseDHCPCB(self, widget, data):
	self.network.overrideDHCPhostname = 0
        self.hostnameEntry.set_text("localhost")
	self.hostnameEntry.set_sensitive(not widget.get_active())
    def hostnameManualCB(self, widget, data):
	self.network.overrideDHCPhostname = 1
	if widget.get_active():
	    self.hostnameEntry.grab_focus()

    """def r_button_def(self, widget, data):
        if self.r_button1.get_active():
            self.r_box.set_sensitive(False)
            self.ipTable.set_sensitive(False)
        else:
            self.setIPTableSensitivity()
            self.r_box.set_sensitive(True)
        self.setHostOptionsSensitivity()"""

    # NetworkWindow tag="netconf"
    
    def manual_a(self,widget,data=None):
        if(widget.get_active()):
            self.ipv4_a.set_sensitive(True)
            self.subnet_a.set_sensitive(True)
            #self.dhcp_a_yes=False
            
    def dhcp_a(self,widget,data=None):
        if(widget.get_active()):
            self.ipv4_a.set_sensitive(False)
            self.subnet_a.set_sensitive(False)
	    self.ipv4_a.set_text("")
	    self.subnet_a.set_text("")
	    #self.dhcp_a_yes=True    
    def add_a(self,boxradio_a):
        #self.window=gtk.Window(gtk.WINDOW_TOPLEVEL)
        
        label_a=gtk.Label(u"交换机设置")
        label_a.set_alignment(0.0,0.0)
        boxradio_a.pack_start(label_a,False,False,0)
        
        #self.radioManual_a=gtk.RadioButton(None,u"手动设置")
        #self.radioManual_a.connect("toggled",self.manual_a,"radioManual_a")
        #boxradio_a.pack_start(self.radioManual_a,True,True,0)
        
        self.radioDHCP_a=gtk.RadioButton(None,u"自动设置")
        self.radioDHCP_a.connect("toggled",self.dhcp_a,"radioDHCP_a")
        boxradio_a.pack_start(self.radioDHCP_a,True,True,0)
        
	self.radioManual_a=gtk.RadioButton(self.radioDHCP_a,u"手动设置")
	self.radioManual_a.connect("toggled",self.manual_a,"radioManual_a")
        boxradio_a.pack_start(self.radioManual_a,True,True,0)
        
        tmphbox_a=gtk.HBox(False,0)
        labelIp_a=gtk.Label(u"IPv4地址")
        labelIp_a.set_width_chars(8)
        tmphbox_a.pack_start(labelIp_a,False,False,0)
        self.ipv4_a=gtk.Entry()
        self.ipv4_a.set_width_chars(20)
        tmphbox_a.pack_start(self.ipv4_a,True,True,0)
        boxradio_a.pack_start(tmphbox_a,True,True,0)
        
        tmphbox_a=gtk.HBox(False,0)
        labelsubnet_a=gtk.Label(u"子网掩码")
        labelsubnet_a.set_width_chars(8)
        tmphbox_a.pack_start(labelsubnet_a,False,False,0)
        self.subnet_a=gtk.Entry()
        self.subnet_a.set_width_chars(20)
        tmphbox_a.pack_start(self.subnet_a,True,True,0)
        boxradio_a.pack_start(tmphbox_a,True,True,0)
        
        self.ipv4_a.set_sensitive(False)
        self.subnet_a.set_sensitive(False)
	self.radioDHCP_a.set_active(True)
	self.dhcp_a_yes=True
	
    def getScreen(self, anaconda):
	self.intf = anaconda.intf
	self.id = anaconda.id
        self.anaconda = anaconda
        box = gtk.VBox(False)
        box.set_spacing(6)
	box1 = gtk.HBox(False)
	self.network = anaconda.id.network
        #import pdb
	#pdb.set_trace()        
        self.devices = self.network.available()
	
        if not self.devices:
	    return None

	self.numdevices = len(self.devices.keys())

	self.hostname = self.network.hostname

	"""devhbox = gtk.HBox(False)
	devhbox.set_spacing(12)"""

	
	"""self.boxradio_a=gtk.VBox(False,0)
	self.add_a(self.boxradio_a)

        if len(self.network.dve_dvelist)==0:
            pass
        else:
            devhbox.pack_start(self.boxradio_a,False)"""
        """devhbox.set_border_width(6)"""

        """l = gtk.Label()
        l.set_markup("<b>%s</b>" %(_("Network Devices"),))
	frame=gtk.Frame()
        if len(self.network.dve_dvelist)==0:
            pass
        else:
            frame.set_label_widget(l)
	frame.add(devhbox)
        frame.set_shadow_type(gtk.SHADOW_NONE)
	box1.pack_start(frame, False)"""

        """box.pack_start(box1, False)"""

	# show hostname and dns/misc network info and offer chance to modify
	hostbox=gtk.VBox()
	hostbox.set_spacing(6)

	"""label=gtk.Label(_("Set the hostname:"))
	label.set_alignment(0.0, 0.0)
	hostbox.pack_start(label, False, False)"""

	tmphbox=gtk.HBox()
        self.hostnameUseDHCP = gtk.RadioButton(label=_("_automatically via DHCP"))
	self.hostnameUseDHCP.connect("toggled", self.hostnameUseDHCPCB, None)
	tmphbox.pack_start (self.hostnameUseDHCP, False, False)
	hostbox.pack_start(tmphbox, False, False)

	tmphbox=gtk.HBox()
	tmphbox.set_spacing(6)
	self.hostnameManual = gtk.RadioButton(group=self.hostnameUseDHCP, label=_("_manually"))
	tmphbox.pack_start(self.hostnameManual, False, False)
	self.hostnameEntry = gtk.Entry()
	self.hostnameEntry.set_width_chars(32)
	tmphbox.pack_start(self.hostnameEntry, False, False)
	tmphbox.pack_start(gtk.Label(_(u'(例如：localhost)')), False, False)
	self.hostnameManual.connect("toggled", self.hostnameManualCB, None)
	hostbox.pack_start(tmphbox, False, False)

	hostbox.set_border_width(6)
        l = gtk.Label()
        l.set_markup("<b>%s</b>" %(_(u"主机名设置：\n"),))
	frame=gtk.Frame()
        frame.set_label_widget(l)
	frame.add(hostbox)
        frame.set_shadow_type(gtk.SHADOW_NONE)
	box.pack_start(frame, False, False)


        #self.setHostOptionsSensitivity()
        
	self.ipTable = gtk.Table(len(global_options), 2)
	options = {}
	for i in range(len(global_options)):
	    label = gtk.Label("%s:" %(global_option_labels[i],))
	    #label.set_property("use-underline", True)
	    label.set_alignment(0.0, 0.0)
	    self.ipTable.attach(label, 0, 1, i, i+1, gtk.FILL, 0)
	    align = gtk.Alignment(0, 0.5)
	    options[i] = gtk.Entry()
	    options[i].set_width_chars(32)
	    align.add(options[i])
	    label.set_mnemonic_widget(options[i])

	    self.ipTable.attach(align, 1, 2, i, i+1, gtk.FILL, 0)
       
        #self.add_iptable()
	self.globals = {}
	for t in range(len(global_options)):
	    self.globals[global_options[t]] = options[t]
        #import pdb
        #pdb.set_trace()
	# bring over the value from the loader
        if self.network.hostname_dhcp==True:
            self.hostnameUseDHCP.set_active(True)
        else:
            self.hostnameManual.set_active(True)
	self.hostnameEntry.set_text(self.network.hostname)
	#import pdb
	#pdb.set_trace()
        if len(self.network.dve_dvelist)==0:
	    self.globals[_("Gateway")].set_text("")
	    self.globals[_("Primary DNS")].set_text("")
	    self.globals[_("Secondary DNS")].set_text("")
	    self.globals[_("Gateway")].set_sensitive(False)
            self.globals[_("Primary DNS")].set_sensitive(False)
	    self.globals[_("Secondary DNS")].set_sensitive(False)
	    #self.set_visible_false()
        else:
	    #self.set_visible_true()
	    self.globals[_("Gateway")].set_sensitive(True)
	    self.globals[_("Primary DNS")].set_sensitive(True)
	    self.globals[_("Secondary DNS")].set_sensitive(True)	    
            
            """if not network.anyUsingDHCP(self.devices, anaconda):"""
            if self.network.gateway:
                self.globals[_("Gateway")].set_text(self.network.gateway)
	    if self.network.primaryNS:
                self.globals[_("Primary DNS")].set_text(self.network.primaryNS)
	    if self.network.secondaryNS:
                self.globals[_("Secondary DNS")].set_text(self.network.secondaryNS)

	self.ipTable.set_border_width(6)

        l = gtk.Label()
        l.set_markup("<b>%s</b>" %(_("其他设置：\n"),))
	frame=gtk.Frame()
        
        if len(self.network.dve_dvelist)==0:
            pass
        else:
            frame.set_label_widget(l)

        if len(self.network.dve_dvelist)==0:
            pass
        else:
	    frame.add(self.ipTable)

        frame.set_shadow_type(gtk.SHADOW_NONE)
	box.pack_start(frame, False, False)
	box.set_border_width(6)

	self.hostnameEntry.set_sensitive(not self.hostnameUseDHCP.get_active())
	
	#state=not (not network.anyUsingDHCP(self.devices, self.anaconda)) #2
	#self.edit1.set_sensitive(False)
	#self.setIPTableSensitivity()
        #self.hostnameUseDHCP.set_sensitive(network.anyUsingDHCP(self.devices, anaconda))

	return box
    """def add_iptable(self):
        self.label_gate = gtk.Label("%s:" %(global_option_labels[0],))
        self.label_gate.set_property("use-underline", True)
        self.label_gate.set_alignment(0.0, 0.0)
        self.ipTable.attach(self.label_gate, 0, 1, 0,1, gtk.FILL, 0)
        align = gtk.Alignment(0, 0.5)
	options[0] = gtk.Entry()
	options[0].set_width_chars(41)
	align.add(options[0])
	self.label_gate.set_mnemonic_widget(options[0])
        self.ipTable.attach(align, 1, 2, 0, 1, gtk.FILL, 0）

        self.label_pri = gtk.Label("%s:" %(global_option_labels[1],))
        self.label_pri.set_property("use-underline", True)
        self.label_pri.set_alignment(0.0, 0.0)
        self.ipTable.attach(self.label_pri, 0, 1, 1, 2, gtk.FILL, 0)
        align = gtk.Alignment(0, 0.5)
        options[1] = gtk.Entry()
        options[1].set_width_chars(41)
        align.add(options[1])
        self.label_pri.set_mnemonic_widget(options[1])
        self.ipTable.attach(align, 1, 2, 1, 2, gtk.FILL, 0）

        self.label_sec = gtk.Label("%s:" %(global_option_labels[2],))
        self.label_sec.set_property("use-underline", True)
        self.label_sec.set_alignment(0.0, 0.0)
        self.ipTable.attach(self.label_sec, 0, 1, 2, 3, gtk.FILL, 0)
        align = gtk.Alignment(0, 0.5)
        options[2] = gtk.Entry()
        options[2].set_width_chars(41)
        align.add(options[i])
        self.label_sec.set_mnemonic_widget(options[2])
        self.ipTable.attach(align, 1, 2, 2, 3, gtk.FILL, 0）

        return False
    def set_visible_false(self):
        self.label_gate.set_visible(False)
        self.label_pri.set_visible(False)
        self.label_sec.set_visible(False)
        for t in range(len(global_options)):
            self.globals[global_options[t]].set_visible(False)
        
    def set_visible_true(self):
        self.label_gate.set_visible(True)
        self.label_pri.set_visible(True)
        self.label_sec.set_visible(True)
        for t in range(len(global_options)):
            self.globals[global_options[t]].set_visible(True)"""
        
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

        #self.enable_ipv6 = self.xml.get_widget("enable_ipv6")
        #self.auto_ipv6 = self.xml.get_widget("auto_ipv6")
        #self.dhcp_ipv6 = self.xml.get_widget("dhcp_ipv6")
        #self.manual_ipv6 = self.xml.get_widget("manual_ipv6")
        #self.ipv6_address_label = self.xml.get_widget("ipv6_address_label")
        #self.ipv6_prefix_label = self.xml.get_widget("ipv6_prefix_label")
        #self.ipv6_address = self.xml.get_widget("ipv6_address")
        #self.ipv6_slash = self.xml.get_widget("ipv6_slash_label")
        #self.ipv6_prefix = self.xml.get_widget("ipv6_prefix")

        self.toplevel.connect("destroy", self.destroy)
        self.button_ok.connect("clicked", self.okClicked)
        self.button_cancel.connect("clicked", self.cancelClicked)

        self.enable_ipv4.connect("toggled", self.ipv4_toggled)
        self.dhcp_ipv4.connect("toggled", self.ipv4_changed)
        self.manual_ipv4.connect("toggled", self.ipv4_changed)
        #self.enable_ipv6.connect("toggled", self.ipv6_toggled)
        #self.auto_ipv6.connect("toggled", self.ipv6_changed)
        #self.dhcp_ipv6.connect("toggled", self.ipv6_changed)
        #self.manual_ipv6.connect("toggled", self.ipv6_changed)

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

        self.hardware_address.set_markup("<b>" + _("Hardware address: ") + mac + "</b>")

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

    #def setIPv6Manual(self, ipv6addr, ipv6prefix):
    #    if ipv6addr.lower() == 'dhcp':
    #        return

    #    if ipv6addr is not None:
    #        self.ipv6_address.set_text(ipv6addr)

    #    if ipv6prefix is not None:
    #        self.ipv6_prefix.set_text(ipv6prefix)

    #def getIPv6Address(self):
    #    return self.ipv6_address.get_text()

    #def getIPv6Prefix(self):
    #    return self.ipv6_prefix.get_text()

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

    def okClicked(self, args):
        # input validation
        if not self.isIPv4Enabled() and not self.isIPv6Enabled():
            self.netwin.intf.messageWindow(_("Missing Protocol"),
                                           _("You must select at least IPv4 "
                                             "or IPv6 support."))
            self.valid_input = 1
            return

        if self.isIPv4Enabled():
            if self.manual_ipv4.get_active():
                try:
                    network.sanityCheckIPString(self.ipv4_address.get_text())
                except network.IPMissing, msg:
                    self.netwin.handleIPMissing('IPv4 address')
                    self.valid_input = 1
                    return
                except network.IPError, msg:
                    self.netwin.handleIPError('IPv4 address', msg)
                    self.valid_input = 1
                    return

                val = self.ipv4_prefix.get_text()
                if val.find('.') == -1:
                    # user provided a CIDR prefix
                    try:
                        if int(val) > 32 or int(val) < 0:
                            self.netwin.intf.messageWindow(_("Invalid Prefix"),
                                                           _("IPv4 prefix "
                                                             "must be between "
                                                             "0 and 32."))
                            self.valid_input = 1
                            return
                        else:
                            self.ipv4_prefix.set_text(isys.prefix2netmask(int(val)))
                    except:
                        self.netwin.handleIPMissing('IPv4 network mask')
                        self.valid_input = 1
                        return
                else:
                    # user provided a dotted-quad netmask
                    try:
                        network.sanityCheckIPString(self.ipv4_prefix.get_text())
                    except network.IPMissing, msg:
                        self.netwin.handleIPMissing('IPv4 network mask')
                        self.valid_input = 1
                        return
                    except network.IPError, msg:
                        self.netwin.handleIPError('IPv4 network mask', msg)
                        self.valid_input = 1
                        return

        #if self.isIPv6Enabled():
        #    if self.manual_ipv6.get_active():
        #        try:
        #            network.sanityCheckIPString(self.ipv6_address.get_text())
        #        except network.IPMissing, msg:
        #            self.netwin.handleIPMissing('IPv6 address')
        #            self.valid_input = 1mkisofs -o /mnt/hgfs/iso/RHEL5U3.iso -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -R -J -v -T /ltos/
        #            return
        #        except network.IPError, msg:
        #            self.netwin.handleIPError('IPv6 address', msg)
        #            self.valid_input = 1
        #            return

        #        val = self.ipv6_prefix.get_text()
        #        try:
        #            if int(val) > 128 or int(val) < 0:
        #                self.netwin.intf.messageWindow(_("Invalid Prefix"),
        #                                               _("IPv6 prefix must be "
        #                                                 "between 0 and 128."))
        #                self.valid_input = 1
        #                return
        #        except:
        #            self.netwin.intf.messageWindow(_("Invalid Prefix"),
        #                                           _("IPv6 prefix must be "
        #                                             "between 0 and 128."))
        #            self.valid_input = 1
        #            return

        if self.isPtPEnabled():
            try:
                network.sanityCheckIPString(self.ptp_address.get_text())
            except network.IPMissing, msg:
                self.netwin.handleIPMissing('point-to-point IP address')
                self.valid_input = 1
                return
            except network.IPError, msg:
                self.netwin.handleIPError('point-to-point IP address', msg)
                self.valid_input = 1
                return

        # if we made it this far, all input is good
        self.valid_input = 2

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
