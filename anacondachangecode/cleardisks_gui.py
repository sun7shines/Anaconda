# -*- coding:utf8 -*-
# Select which disks to clear and which ones to just mount.
#
# Copyright (C) 2009  Red Hat, Inc.
# All rights reserved.
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

import gtk, gobject
import gui
from DeviceSelector import *
from constants import *
import isys
from iw_gui import *
from storage.devices import deviceNameToDiskByPath
from storage.udev import *

import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)

class ClearDisksWindow (InstallWindow):
    windowTitle = N_("Clear Disks Selector")

    def getNext (self):
        # All the rows that are visible in the right hand side should be cleared.
        cleardisks = []
        destroydisks = []
        for row in self.store:
            if row[self.rightVisible]:
                cleardisks.append(row[OBJECT_COL].name)
            if row[self.delete_col]:
                destroydisks.append(row[OBJECT_COL].name)

        if len(cleardisks) == 0:
            self.anaconda.intf.messageWindow(_("Error"),
                                             _("You must select at least one "
                                               "drive to be used for installation."),
                                             custom_icon="error")
            raise gui.StayOnScreen

        if len(cleardisks) != 1:
            self.anaconda.intf.messageWindow(_("Error"),
                                             _(u"您只能选择一个目标安装设备."),
                                             custom_icon="error")
            raise gui.StayOnScreen
        
        # The selected row is the disk to boot from.
        selected = self.rightDS.getSelected()

        if len(selected) == 0:
            self.anaconda.intf.messageWindow(_("Error"),
                                             _("You must select one drive to "
                                               "boot from."),
                                             custom_icon="error")
            raise gui.StayOnScreen

        bootDisk = selected[0][OBJECT_COL].name

        cleardisks.sort(self.anaconda.id.storage.compareDisks)

        if bootDisk in destroydisks:
            destroydisks.remove(bootDisk) 

        self.anaconda.id.storage.clearPartDisks = cleardisks
        self.anaconda.id.storage.destroyDisks = destroydisks
        self.anaconda.id.bootloader.updateDriveList([bootDisk])

    def getScreen (self, anaconda):
        # We can't just use exclusiveDisks here because of kickstart.  First,
        # the kickstart file could have used ignoredisk --drives= in which case
        # exclusiveDisks would be empty.  Second, ignoredisk is entirely
        # optional in which case neither list would be populated.  Luckily,
        # storage.disks takes isIgnored into account and that handles both these
        # issues.
        disks = filter(lambda d: not d.format.hidden, anaconda.id.storage.disks)

        # Skip this screen as well if there's only one disk to use.
        if len(disks) == 1:
            anaconda.id.storage.clearPartDisks = [disks[0].name]
            anaconda.id.bootloader.drivelist = [disks[0].name]
            return None

        (xml, self.vbox) = gui.getGladeWidget("cleardisks.glade", "vbox")
        self.leftScroll = xml.get_widget("leftScroll")
        self.rightScroll = xml.get_widget("rightScroll")
        ############################
        
        self.leftScroll.set_size_request(500,300)
        self.rightScroll.set_size_request(300,300)
        ###########################
        self.addButton = xml.get_widget("addButton")
        self.removeButton = xml.get_widget("removeButton")
        self.installTargetImage = xml.get_widget("installTargetImage")
        self.installTargetTip = xml.get_widget("installTargetTip")

        self.anaconda = anaconda

        self.leftVisible = 1
        self.leftActive = 2
        self.rightVisible = 4
        self.rightActive = 5
        self.delete_col = 6
        
        # One store for both views.  First the obejct, then a visible/active for
        # the left hand side, then a visible/active for the right hand side, then
        # all the other stuff.
        #
        # NOTE: the third boolean is a placeholder.  DeviceSelector uses the third
        # slot in the store to determine whether the row is immutable or not.  We
        # just need to put False in there for everything.
        self.store = gtk.TreeStore(gobject.TYPE_PYOBJECT,
                                   gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN,
                                   gobject.TYPE_BOOLEAN,
                                   gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN,
                                   gobject.TYPE_BOOLEAN,
                                   gobject.TYPE_STRING, gobject.TYPE_STRING,
                                   gobject.TYPE_STRING, gobject.TYPE_STRING,
                                   gobject.TYPE_STRING)
        self.store.set_sort_column_id(7, gtk.SORT_ASCENDING)

        # The left view shows all the drives that will just be mounted, but
        # can still be moved to the right hand side.
        self.leftFilteredModel = self.store.filter_new()
        self.leftSortedModel = gtk.TreeModelSort(self.leftFilteredModel)
        self.leftTreeView = gtk.TreeView(self.leftSortedModel)

        self.leftFilteredModel.set_visible_func(lambda model, iter, view: model.get_value(iter, self.leftVisible), self.leftTreeView)

        self.leftScroll.add(self.leftTreeView)

        self.leftDS = DeviceSelector(self.store, self.leftSortedModel,
                                     self.leftTreeView, visible=self.leftVisible,
                                     active=self.leftActive,delete_col=self.delete_col)
        self.leftDS.createSelectionCol_2(title=_("格式化"), radioButton=True)
        self.leftDS.createMenu()
        xxx = 7
        self.leftDS.addColumn(_("Model"), xxx)
        self.leftDS.addColumn(_("Capacity"), xxx+1)
        self.leftDS.addColumn(_("Vendor"), xxx+2)
        self.leftDS.addColumn(_("Identifier"), xxx+3)
        self.leftDS.addColumn(_("Interconnect"), xxx+4, displayed=False)

        # The right view show all the drives that will be wiped during install.
        self.rightFilteredModel = self.store.filter_new()
        self.rightSortedModel = gtk.TreeModelSort(self.rightFilteredModel)
        self.rightTreeView = gtk.TreeView(self.rightSortedModel)

        self.rightFilteredModel.set_visible_func(lambda model, iter, view: model.get_value(iter, self.rightVisible), self.rightTreeView)

        self.rightScroll.add(self.rightTreeView)

        self.rightDS = DeviceSelector(self.store, self.rightSortedModel,
                                      self.rightTreeView, visible=self.rightVisible,
                                      active=self.rightActive)
        self.rightDS.createSelectionCol(title=_("Boot\nLoader"), radioButton=True)
        self.rightDS.createMenu()
        yyy = 7
        self.rightDS.addColumn(_("Model"), yyy)
        self.rightDS.addColumn(_("Capacity"), yyy+1)
        self.rightDS.addColumn(_("Identifier"), yyy+3)

        # Store the first disk (according to our detected BIOS order) for
        # auto boot device selection
        names = map(lambda d: d.name, disks)
        self.bootDisk = sorted(names, self.anaconda.id.storage.compareDisks)[0]

        # The device filtering UI set up exclusiveDisks as a list of the names
        # of all the disks we should use later on.  Now we need to go get those,
        # look up some more information in the devicetree, and set up the
        # selector.
        for d in disks:
            rightVisible = d.name in self.anaconda.id.storage.clearPartDisks
            rightActive = rightVisible and \
                          d.name in self.anaconda.id.bootloader.drivelist[:1]
            leftVisible = not rightVisible
            
            deletexxx = d.name in self.anaconda.id.storage.destroyDisks
            
            if hasattr(d, "wwid"):
                ident = d.wwid
            else:
                try:
                    ident = deviceNameToDiskByPath(d.name)
                    if ident.startswith("/dev/disk/by-path/"):
                        ident = ident.replace("/dev/disk/by-path/", "")
                except DeviceNotFoundError:
                    ident = d.name

            self.store.append(None, (d,
                                     leftVisible, True, False,
                                     rightVisible, rightActive,
                                     deletexxx,
                                     d.model,
                                     str(int(d.size)) + " MB",
                                     d.vendor, ident, d.bus))

        self.addButton.connect("clicked", self._add_clicked)
        self.removeButton.connect("clicked", self._remove_clicked)

        # Also allow moving devices back and forth with double click, enter, etc.
        self.leftTreeView.connect("row-activated", self._add_clicked)
        self.rightTreeView.connect("row-activated", self._remove_clicked)

        # And let the user select multiple devices at a time.
        self.leftTreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.rightTreeView.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

        if self.anaconda.id.storage.clearPartType == CLEARPART_TYPE_LINUX:
            self.installTargetTip.set_markup(_("<b>Tip:</b> All Linux filesystems on install target devices will be reformatted and wiped of any data.  Make sure you have backups."))
        elif self.anaconda.id.storage.clearPartType == CLEARPART_TYPE_ALL:
            self.installTargetTip.set_markup(_("<b>Tip:</b> Install target devices will be reformatted and wiped of any data.  Make sure you have backups."))
        else:
            self.installTargetTip.set_markup(_("<b>Tip:</b> Your filesystems on install target devices will not be wiped unless you choose to do so during customization."))

        """return self.vbox"""
        #####################################################
        
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
        path = "/usr/share/anaconda/pixmaps/icon4_storage_select.png"
        i.set_from_file(path)
        i.show()
        fixed.put(i,45,15)
        label1 = gtk.Label()
        lstr = "<span font_desc=' 16' weight='bold' foreground='"+fontcolor+"'><b>存储设备：</b></span>"
        label1.set_markup(lstr)
        fixed.put(label1,160,23)
        label2 = gtk.Label()
        lstr = "<span font_desc=' 11.5' weight='bold' foreground='"+fontcolor+"'><b>选择操作系统安装位置</b></span>"
        label2.set_markup(lstr)
        fixed.put(label2,160,58)
        eboximage.add(fixed) 
        eboximage.show_all()
        
        vbox = gtk.VBox(False,0)
        vbox.pack_start(eboximage,False,False,0)
        #####################################################
        
        tmphbox = gtk.HBox(False,0)
        tmphbox.pack_start(self.vbox,True,True,0)
        
        fix = gtk.Fixed()
        fix.put(tmphbox,35,35)
        #fix.set_size_request(900,400)
        vbox.pack_start(fix,True,True,0)
        
        l = xml.get_widget("label1")
        text = "下面是您选择用于这个安装的存储设备。请使用下面的箭头指定您要用做数据驱动器的设备（这些设备不会被格式化，只被挂载）以及用做系统驱动器的设备（这些设备将被格式化）。还请指定在哪个系统驱动器中安装引导装载程序。"
        lstr = "<span foreground='#333333'><b>"+text+"</b></span>"
        l.set_markup(lstr)
        l = xml.get_widget("label4")
        lstr = "<span foreground='#333333'><b>"+l.get_text()+"</b></span>"
        l.set_markup(lstr)
        l = xml.get_widget("label5")
        lstr = "<span foreground='#333333'><b>"+l.get_text()+"</b></span>"
        l.set_markup(lstr)
        
        return vbox
    

    def _autoSelectBootDisk(self):
        if self.rightDS.getSelected():
            return

        for row in self.store:
            if row[OBJECT_COL].name == self.bootDisk and row[self.rightVisible]:
                row[self.rightActive] = True

    def _add_clicked(self, widget, *args, **kwargs):
        (sortedModel, pathlist) = self.leftTreeView.get_selection().get_selected_rows()

        if not pathlist:
            return

        for path in reversed(pathlist):
            sortedIter = sortedModel.get_iter(path)
            if not sortedIter:
                continue

            filteredIter = self.leftSortedModel.convert_iter_to_child_iter(None, sortedIter)
            iter = self.leftFilteredModel.convert_iter_to_child_iter(filteredIter)

            self.store.set_value(iter, self.leftVisible, False)
            self.store.set_value(iter, self.rightVisible, True)
            self.store.set_value(iter, self.rightActive, False)

        self._autoSelectBootDisk()
        self.leftFilteredModel.refilter()
        self.rightFilteredModel.refilter()

    def _remove_clicked(self, widget, *args, **kwargs):
        (sortedModel, pathlist) = self.rightTreeView.get_selection().get_selected_rows()

        if not pathlist:
            return

        for path in reversed(pathlist):
            sortedIter = sortedModel.get_iter(path)
            if not sortedIter:
                continue

            filteredIter = self.rightSortedModel.convert_iter_to_child_iter(None, sortedIter)
            iter = self.rightFilteredModel.convert_iter_to_child_iter(filteredIter)

            self.store.set_value(iter, self.leftVisible, True)
            self.store.set_value(iter, self.rightVisible, False)
            self.store.set_value(iter, self.rightActive, False)

        self._autoSelectBootDisk()
        self.leftFilteredModel.refilter()
        self.rightFilteredModel.refilter()
