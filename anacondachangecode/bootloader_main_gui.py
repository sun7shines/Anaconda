# -*- coding:utf8 -*-
# bootloader_main_gui.py: gui bootloader configuration dialog
#
# Copyright (C) 2001, 2002  Red Hat, Inc.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author(s): Jeremy Katz <katzj@redhat.com>
#

import gtk
import gobject
import gui
import iutil
from iw_gui import *
from constants import *

import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)

from osbootwidget import OSBootWidget
from blpasswidget import BootloaderPasswordWidget


class MainBootloaderWindow(InstallWindow):
    windowTitle = N_("Boot Loader Configuration")

    def __init__(self, ics):
        InstallWindow.__init__(self, ics)
        self.parent = ics.getICW().window


    def getPrev(self):
        pass


    def getNext(self):
        # go ahead and set the device even if we already knew it
        # since that won't change anything
        self.bl.setDevice(self.bldev)

        self.bl.drivelist = self.driveorder

        if not self.grubCB.get_active():
            # if we're not installing a boot loader, don't show the second
            # screen and don't worry about other options
            self.dispatch.skipStep("instbootloader", skip = 1)

            # kind of a hack...
            self.bl.defaultDevice = None
            return
        else:
            self.dispatch.skipStep("instbootloader", skip = 0)
            self.bl.setUseGrub(1)

        # set the password
        self.bl.setPassword(self.blpass.getPassword(), isCrypted = 0)

        # set the bootloader images based on what's in our list
        self.oslist.setBootloaderImages()

    def bootloaderChanged(self, *args):
        active = self.grubCB.get_active()

        for widget in [ self.oslist.getWidget(), self.blpass.getWidget(), self.deviceButton ]:
            if widget:
                widget.set_sensitive(active)


    def _deviceChange(self, b, anaconda, *args):
        def __driveChange(combo, dxml, choices):
            if not choices.has_key("mbr"):
                return

            iter = combo.get_active_iter()
            if not iter:
                return

            first = combo.get_model()[iter][1]
            desc = choices["mbr"][1]
            dxml.get_widget("mbrRadio").set_label("%s - /dev/%s" %(_(desc), first))
            dxml.get_widget("mbrRadio").set_data("bootDevice", first)

        def __genStore(combo, disks, active):
            model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
            combo.set_model(model)
            cell = gtk.CellRendererText()
            combo.pack_start(cell, True)
            combo.set_attributes(cell, text = 0)

            for disk in disks:
                i = model.append(None)
                model[i] = ("%s %8.0f MB %s" %(disk.name, disk.size,
                                               disk.description),
                            "%s" %(disk.name,))
                if disk.name == active:
                    combo.set_active_iter(i)

            return model

        (dxml, dialog) = gui.getGladeWidget("blwhere.glade",
                                            "blwhereDialog")
        gui.addFrame(dialog)
        dialog.set_transient_for(self.parent)
        dialog.show()

        choices = anaconda.platform.bootloaderChoices(self.bl)
        for t in ("mbr", "boot"):
            if not choices.has_key(t):
                continue
            (device, desc) = choices[t]
            w = dxml.get_widget("%sRadio" %(t,))
            w.set_label("%s - /dev/%s" %(_(desc), device))
            w.show()
            if self.bldev == device:
                w.set_active(True)
            else:
                w.set_active(False)
            w.set_data("bootDevice", device)

        for i in range(1, 5):
            if len(self.driveorder) < i:
                break
            combo = dxml.get_widget("bd%dCombo" %(i,))
            lbl = dxml.get_widget("bd%dLabel" %(i,))
            combo.show()
            lbl.show()
            partitioned = anaconda.id.storage.partitioned
            disks = anaconda.id.storage.disks
            bl_disks = [d for d in disks if d in partitioned]
            m = __genStore(combo, bl_disks, self.driveorder[i - 1])

        dxml.get_widget("bd1Combo").connect("changed", __driveChange, dxml, choices)
        __driveChange(dxml.get_widget("bd1Combo"), dxml, choices)

        while 1:
            rc = dialog.run()
            if rc in [gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT]:
                break

            # set the boot device based on what they chose
            if dxml.get_widget("bootRadio").get_active():
                self.bldev = dxml.get_widget("bootRadio").get_data("bootDevice")
            elif dxml.get_widget("mbrRadio").get_active():
                self.bldev = dxml.get_widget("mbrRadio").get_data("bootDevice")
            else:
                raise RuntimeError, "No radio button selected!"

            # and adjust the boot order
            neworder = []
            for i in range(1, 5):
                if len(self.driveorder) < i:
                    break

                combo = dxml.get_widget("bd%dCombo" %(i,))
                iter = combo.get_active_iter()
                if not iter:
                    continue

                act = combo.get_model()[iter][1]
                if act not in neworder:
                    neworder.append(act)
            for d in self.driveorder:
                if d not in neworder:
                    neworder.append(d)
            self.driveorder = neworder

            break

        dialog.destroy()
        self.grubCB.set_label(_("_Install boot loader on /dev/%s.") %
                              (self.bldev,))
        return rc

    def _setBLCBText(self):
        self.grubCB.set_label(_("_Install boot loader on /dev/%s.") %
                              (self.bldev,))


    def getScreen(self, anaconda):
        self.dispatch = anaconda.dispatch
        self.bl = anaconda.id.bootloader
        self.intf = anaconda.intf

        self.driveorder = self.bl.drivelist
        if len(self.driveorder) == 0:
            partitioned = anaconda.id.storage.partitioned
            disks = anaconda.id.storage.disks
            self.driveorder = [d.name for d in disks if d in partitioned]

        if self.bl.getPassword():
            self.usePass = 1
            self.password = self.bl.getPassword()
        else:
            self.usePass = 0
            self.password = None

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
        path = "/usr/share/anaconda/pixmaps/icon11_boot.png"
        i.set_from_file(path)
        i.show()
        fixed.put(i,45,15)
        label1 = gtk.Label()
        lstr = "<span font_desc=' 16' weight='bold' foreground='"+fontcolor+"'><b>引导程序:</b></span>"
        label1.set_markup(lstr)
        fixed.put(label1,160,23)
        label2 = gtk.Label()
        label2.set_markup("<span font_desc=' 11.5' weight='bold' foreground='"+fontcolor+"'><b>选择引导程序安装位置</b></span>")
        fixed.put(label2,160,58)
        eboximage.add(fixed) 
        eboximage.show_all()

        thebox = gtk.VBox(False,0)
        thebox.pack_start(eboximage,False,False,0)
        
        ###########################################################
        
        # make sure we get a valid device to say we're installing to
        if self.bl.getDevice() is not None:
            self.bldev = self.bl.getDevice()
        else:
            # we don't know what it is yet... if mbr is possible, we want
            # it, else we want the boot dev
            choices = anaconda.platform.bootloaderChoices(self.bl)
            if choices.has_key('mbr'):
                self.bldev = choices['mbr'][0]
            else:
                self.bldev = choices['boot'][0]
        ###########################################################
        boxall = gtk.VBox(False,0)
        
        hb = gtk.HBox(False, 12)
        """self.grubCB = gtk.CheckButton(_("_Install boot loader on /dev/%s.") %
                                      (self.bldev,))"""
        self.grubCB = gtk.CheckButton((u"在/dev/%s 中安装引导装载程序") %
                                      (self.bldev,))
        l = self.grubCB.get_children()[0]
        lstr = "<span  foreground='#333333'><b>"+l.get_text()+"</b></span>"
        l.set_markup(lstr)
            
        self.grubCB.set_active(not self.dispatch.stepInSkipList("instbootloader"))
        self.grubCB.connect("toggled", self.bootloaderChanged)
        hb.pack_start(self.grubCB, False)

        # no "Change device" button on EFI systems, since there should only
        # be one EFI System Partition available/usable
        self.deviceButton = None
        if not iutil.isEfi():
            self.deviceButton = gtk.Button(_(u"更换设备"))
            
            l = self.deviceButton.get_children()[0]
            lstr = "<span  foreground='#333333'><b>"+l.get_text()+"</b></span>"
            l.set_markup(lstr)
            
            self.deviceButton.connect("clicked", self._deviceChange, anaconda)
            hb.pack_start(self.deviceButton, False,False,32)

        boxall.pack_start(hb,False,False,0)
        #################################################################
        
        # control whether or not there's a boot loader password and what it is
        self.blpass = BootloaderPasswordWidget(anaconda, self.parent)
        boxall.pack_start(self.blpass.getWidget(),False,False,5)
        
        ###################################################################
        # configure the systems available to boot from the boot loader
        self.oslist = OSBootWidget(anaconda, self.parent)
        boxall.pack_start(self.oslist.getWidget(),True,True,10)
        
        fix = gtk.Fixed()
        fix.put(boxall,35,35)
        thebox.pack_start(fix,True,True,20)
        ######################################################################
        
        self.bootloaderChanged()
        """return thebox"""
        ####################################################################
        ebox = gtk.EventBox()
        ebox.add(thebox)
        ebox.set_app_paintable(True)
        ebox.set_border_width(0)
        ebox.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#e6e6e6"))
        return ebox
