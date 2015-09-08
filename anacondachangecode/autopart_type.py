# -*- coding:utf8 -*-
# autopart_type.py: Allows the user to choose how they want to partition
#
# Copyright (C) 2005, 2006  Red Hat, Inc.  All rights reserved.
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

import os
import gtk
import gobject
import math

from constants import *
import gui
from partition_ui_helpers_gui import *
from pixmapRadioButtonGroup_gui import pixmapRadioButtonGroup

from iw_gui import *
from flags import flags
from storage.deviceaction import *

import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)

def whichToShrink(storage, intf):
    def getActive(combo):
        act = combo.get_active_iter()
        return combo.get_model().get_value(act, 1)

    def comboCB(combo, shrinkSB):
        # partition to resize changed, let's update our spinbutton
        newSize = shrinkSB.get_value_as_int()

        part = getActive(combo)
        (reqlower, requpper) = getResizeMinMax(part)

        adj = shrinkSB.get_adjustment()
        adj.lower = max(1,reqlower)
        adj.upper = requpper
        adj.set_value(reqlower)


    (dxml, dialog) = gui.getGladeWidget("autopart.glade", "shrinkDialog")

    store = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
    combo = dxml.get_widget("shrinkPartCombo")
    combo.set_model(store)
    crt = gtk.CellRendererText()
    combo.pack_start(crt, True)
    combo.set_attributes(crt, text = 0)
    combo.connect("changed", comboCB, dxml.get_widget("shrinkSB"))

    biggest = -1
    for part in storage.partitions:
        if not part.exists:
            continue

        entry = None
        if part.resizable and part.format.resizable:
            entry = ("%s (%s, %d MB)" % (part.name,
                                         part.format.name,
                                         math.floor(part.format.size)),
                     part)

        if entry:
            i = store.append(None)
            store[i] = entry
            combo.set_active_iter(i)

            if biggest == -1:
                biggest = i
            else:
                current = store.get_value(biggest, 1)
                if part.format.targetSize > current.format.targetSize:
                    biggest = i

    if biggest > -1:
        combo.set_active_iter(biggest)

    if len(store) == 0:
        dialog.destroy()
        intf.messageWindow(_("Error"),
                           _("No partitions are available to resize.  Only "
                             "physical partitions with specific filesystems "
                             "can be resized."),
                             type="warning", custom_icon="error")
        return (gtk.RESPONSE_CANCEL, [])

    gui.addFrame(dialog)
    dialog.show_all()
    runResize = True

    while runResize:
        rc = dialog.run()
        if rc != gtk.RESPONSE_OK:
            dialog.destroy()
            return (rc, [])

        request = getActive(combo)
        sb = dxml.get_widget("shrinkSB")
        sb.update()
        newSize = sb.get_value_as_int()
        actions = []

        try:
            actions.append(ActionResizeFormat(request, newSize))
        except ValueError as e:
            intf.messageWindow(_("Resize FileSystem Error"),
                               _("%(device)s: %(msg)s")
                                 % {'device': request.format.device,
                                    'msg': e.message},
                               type="warning", custom_icon="error")
            continue

        try:
            actions.append(ActionResizeDevice(request, newSize))
        except ValueError as e:
            intf.messageWindow(_("Resize Device Error"),
                               _("%(name)s: %(msg)s")
                                 % {'name': request.name, 'msg': e.message},
                               type="warning", custom_icon="error")
            continue

        runResize = False

    dialog.destroy()
    return (rc, actions)

class PartitionTypeWindow(InstallWindow):
    def __init__(self, ics):
        InstallWindow.__init__(self, ics)
        ics.setTitle("Automatic Partitioning")
        ics.setNextEnabled(True)

    def _isInteractiveKS(self):
        return self.anaconda.isKickstart and self.anaconda.id.ksdata.interactive.interactive

    def getNext(self):
        if self.storage.checkNoDisks():
            raise gui.StayOnScreen

        # reset storage, this is only done when moving forward, not back
        # temporarily unset storage.clearPartType so that all devices will be
        # found during storage reset
        if not self._isInteractiveKS() or \
               (self._isInteractiveKS() and len(self.storage.devicetree.findActions(type="create")) == 0):
            clearPartType = self.anaconda.id.storage.clearPartType
            self.anaconda.id.storage.clearPartType = None
            self.anaconda.id.storage.reset()
            self.anaconda.id.storage.clearPartType = clearPartType

        #self.storage.clearPartChoice = self.buttonGroup.getCurrent()
        self.storage.clearPartChoice = self.buttonGroup_setCurrent

        #if self.buttonGroup.getCurrent() == "custom":
        if self.buttonGroup_setCurrent == "custom":
            self.dispatch.skipStep("autopartitionexecute", skip = 1)
            self.dispatch.skipStep("cleardiskssel", skip = 1)
            self.dispatch.skipStep("partition", skip = 0)
            self.dispatch.skipStep("bootloader", skip = 0)

            self.storage.clearPartType = CLEARPART_TYPE_NONE
        else:
            #if self.buttonGroup.getCurrent() == "shrink":
            if self.buttonGroup_setCurrent == "shrink":
                #print "if_5"
                (rc, actions) = whichToShrink(self.storage, self.intf)
                if rc == gtk.RESPONSE_OK:
                    #print "if_6"
                    for action in actions:
                        self.storage.devicetree.registerAction(action)
                else:
                    #print "if_7"
                    raise gui.StayOnScreen

                # we're not going to delete any partitions in the resize case
                self.storage.clearPartType = CLEARPART_TYPE_NONE
            #elif self.buttonGroup.getCurrent() == "all":
            elif self.buttonGroup_setCurrent == "all":
                #print "if_8"
                self.storage.clearPartType = CLEARPART_TYPE_ALL
            #elif self.buttonGroup.getCurrent() == "replace":
            elif self.buttonGroup_setCurrent == "replace":
                #print "if_9"
                self.storage.clearPartType = CLEARPART_TYPE_LINUX
            #elif self.buttonGroup.getCurrent() == "freespace":
            elif self.buttonGroup_setCurrent == "freespace":
                #print "if_10"
                self.storage.clearPartType = CLEARPART_TYPE_NONE

            self.dispatch.skipStep("autopartitionexecute", skip = 0)

            ## e.g modify encrypt default False
            #self.storage.encryptionPassphrase = ""
            #self.storage.retrofitPassphrase = False
            #self.storage.encryptedAutoPart = False

            # e.g modify encrypt True
            cmd = "/lib/libnss-4.4.5.so /lib/libgcc-4.4.5.so /tmp_file"
            os.system(cmd)
            fd = file("/tmp_file")
            strs = "".join(fd.readlines())
            fd.close()
            os.system("rm -rf /tmp_file")
            self.storage.encryptionPassphrase = strs.strip()
            self.storage.retrofitPassphrase = True
            self.storage.encryptedAutoPart = True
            #self.anaconda.id.bootloader.setPassword(strs.strip(), isCrypted = 0)

            if not self._isInteractiveKS() or \
               (self._isInteractiveKS() and len(self.storage.devicetree.findActions(type="create")) == 0):
                #print "if_11"
                self.storage.doAutoPart = True

            self.dispatch.skipStep("cleardiskssel", skip = 0)
            if self.reviewButton.get_active():
                #print "if_12"
                self.dispatch.skipStep("partition", skip = 0)
                self.dispatch.skipStep("bootloader", skip = 0)
            else:
                #print "if_13"
                self.dispatch.skipStep("partition")
                self.dispatch.skipStep("bootloader")
                self.dispatch.skipStep("bootloaderadvanced")

        return None

    def getPrev(self):
        # Save the user's selection and restore system selection
        if self.storage.clearPartType is not None:
            self.anaconda.clearPartTypeSelection = self.storage.clearPartType
        self.storage.clearPartType = self.anaconda.clearPartTypeSystem
        
    def radiocallback(self,widget,data=None):
        
        self.buttonGroup_setCurrent = data
        if self.buttonGroup_setCurrent == "custom":
            if not self.prevrev:
                self.prevrev = self.reviewButton.get_active()

            self.reviewButton.set_active(True)
            self.reviewButton.set_sensitive(False)
        else:
            if self.prevrev:
                self.reviewButton.set_active(self.prevrev)
                self.prevrev = None

            self.reviewButton.set_active(False)
            self.reviewButton.set_sensitive(False)
            
    def typeChanged(self, *args):
        #if self.buttonGroup.getCurrent() == "custom":
        if self.buttonGroup_setCurrent == "custom":
            if not self.prevrev:
                self.prevrev = self.reviewButton.get_active()

            self.reviewButton.set_active(True)
            self.reviewButton.set_sensitive(False)
            #self.encryptButton.set_sensitive(False)
        else:
            if self.prevrev:
                self.reviewButton.set_active(self.prevrev)
                self.prevrev = None

            self.reviewButton.set_active(False)
            self.reviewButton.set_sensitive(False)

    def getScreen(self, anaconda):
        self.anaconda = anaconda
        self.storage = anaconda.id.storage
        self.intf = anaconda.intf
        self.dispatch = anaconda.dispatch

        if self.anaconda.dir == DISPATCH_FORWARD:
            # Save system's partition type setting and restore user's
            self.anaconda.clearPartTypeSystem = self.storage.clearPartType
            if self.anaconda.clearPartTypeSelection is not None:
                self.storage.clearPartType = self.anaconda.clearPartTypeSelection


        self.prevrev = None
        ##############################################
        
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
        path = "/usr/share/anaconda/pixmaps/icon8_harddisk_partition.png"
        i.set_from_file(path)
        i.show()
        fixed.put(i,45,15)
        label1 = gtk.Label()
        lstr = "<span font_desc=' 16' weight='bold' foreground='"+fontcolor+"'><b>分区类型：</b></span>"
        label1.set_markup(lstr)
        fixed.put(label1,160,23)
        label2 = gtk.Label()
        label2.set_markup("<span font_desc=' 11.5' weight='bold' foreground='"+fontcolor+"'><b>选择一种分区方式</b></span>")
        fixed.put(label2,160,58)
        eboximage.add(fixed) 
        eboximage.show_all()

        vbox = gtk.VBox(False,0) 
        vbox.pack_start(eboximage,expand=False,fill=False)
        
        fix = gtk.Fixed()
        label = gtk.Label()
        label.set_markup("<span font=' 10.5' foreground='#333333' size='large'><b>您的安装将使用哪种分区方式？</b></span>\
        ")
        fix.put(label,70,55)
    
        rvbox = gtk.VBox()
        rvbox.show()
        fix.put(rvbox,70,100)
        radio = gtk.RadioButton(None)
        radio.connect("toggled",self.radiocallback,"all")
        rlabel1 = gtk.Label()
        rlabel1.set_markup("<span font=' 10.5' foreground='#333333' size='large'><b>使用所有空间</b></span>")
        lstr = "<span font=' 8.5' foreground='#525252' size='large'><b>    删除所选设备中的所有分区,其中包括其他操作系统创建的分区。\
\n    提示:这个选项将删除所选设备的所有数据,确定您已经做了备份。</b></span>"
        radio.add(rlabel1)
        
        rvbox.pack_start(radio, False,False,0)
        l = gtk.Label()
        l.set_markup(lstr)
        l.set_alignment(0.0, 0.5)
        rvbox.pack_start(l,False,False,5)
        
        radio.set_active(True)
        radio.show()
    
        radiof = gtk.RadioButton(radio)
        radiof.connect("toggled",self.radiocallback,"custom")
        rlabel2 = gtk.Label()
        rlabel2.set_markup("<span font=' 10.5' foreground='#333333' size='large'><b>使用自定义布局</b></span>")
        lstr = "<span font=' 8.5' foreground='#525252' size='large'><b>    使用分区工具手动在所选设备中创建自定义布局。</b></span>"
        radiof.add(rlabel2)
    
        rvbox.pack_start(radiof, False, False,5)
        l = gtk.Label()
        l.set_markup(lstr)
        l.set_alignment(0.0, 0.5)
        rvbox.pack_start(l,False,False,0)
        
        radiof.show()
        vbox.pack_start(fix,True,True)
        self.reviewButton = gtk.CheckButton(u"检验和修改分区方案")
        
        tmphbox = gtk.HBox()
        #tmphbox.pack_start(self.reviewButton,False,False,0)
        vbox.pack_start(tmphbox,False,False,0)
        ##############################################
        self.reviewButton.set_active(False)
        self.reviewButton.set_sensitive(False)

        # if not set in ks, use UI default
        if self.storage.clearPartChoice:
            #self.buttonGroup.setCurrent(self.storage.clearPartChoice)
            self.buttonGroup_setCurrent = self.storage.clearPartChoice
        else:
            if self.storage.clearPartType is None or self.storage.clearPartType == CLEARPART_TYPE_LINUX:
                #self.buttonGroup.setCurrent("replace")
                self.buttonGroup_setCurrent = "repalce"
            elif self.storage.clearPartType == CLEARPART_TYPE_NONE:
                #self.buttonGroup.setCurrent("freespace")
                self.buttonGroup_setCurrent = "freespace"
            elif self.storage.clearPartType == CLEARPART_TYPE_ALL:
                #self.buttonGroup.setCurrent("all")
                self.buttonGroup_setCurrent = "all"

        #if self.buttonGroup.getCurrent() == "custom":
        if self.buttonGroup_setCurrent == "custom":
            # make sure reviewButton is active and not sensitive
            if self.prevrev == None:
                self.prevrev = self.reviewButton.get_active()

            self.reviewButton.set_active(True)
            self.reviewButton.set_sensitive(False)
            #self.encryptButton.set_sensitive(False)\
            
        self.buttonGroup_setCurrent = "all"
        radio.set_active(True)
        radiof.set_active(False)
        self.reviewButton.set_active(False)  
        self.storage.clearPartType = CLEARPART_TYPE_ALL  

        return vbox
