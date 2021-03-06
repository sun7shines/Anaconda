# -*- coding:utf8 -*-
# Copyright (C) 2009  Red Hat, Inc.  All rights reserved.
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
# Author(s): Chris Lumens <clumens@redhat.com>
#

import gtk
import gobject
import math
import string

from constants import *
import gui
from partition_ui_helpers_gui import *
from pixmapRadioButtonGroup_gui import pixmapRadioButtonGroup

from iw_gui import *
from flags import flags
from storage.deviceaction import *

import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)


class InstallationTypeWindow(InstallWindow):
    def __init__(self, ics):
        InstallWindow.__init__(self, ics)
        ics.setTitle("Installation Type")
        ics.setNextEnabled(True)

    def hinsert_text(self,entry,new_text, new_text_length, position):
        if len(entry.get_text())+len(new_text)>64:
            entry.stop_emission('insert-text')
        str = string.ascii_letters+string.digits+"-"
        for c in new_text:
            if c not in str:
                entry.stop_emission('insert-text')
    
    def getNext(self):
        
        self.anaconda.sn = self.sn_entry.get_text()
        if len(self.anaconda.sn)==0:
            self.intf.messageWindow(_("Error With Data"),
                                _(u"必须输入出厂编号才能进行下一步操作！"))
            raise gui.StayOnScreen
        '''
        f = open("/root/isotype")
        lines = f.readlines()
        f.close()
        for line in lines:
            isotype = string.strip(line)
            break
        '''
        import fvi
        isotype = fvi.get_iso_type()
                
        self.anaconda.isotype = isotype.split('.')[0]
        if self.buttonGroup_setCurrent == "fast":
            self.anaconda.id.installationtype = True
            self.anaconda.dispatch.skipStep("filtertype",skip=1)
            self.anaconda.dispatch.skipStep("u_filtertype",skip=0)

            self.anaconda.dispatch.skipStep("network",skip=1)
            self.anaconda.dispatch.skipStep("u_network",skip=0)
 
            self.anaconda.dispatch.skipStep("parttype",skip=1)
            self.anaconda.dispatch.skipStep("u_parttype",skip=0)

            self.anaconda.dispatch.skipStep("tasksel",skip=1)
            self.anaconda.dispatch.skipStep("u_tasksel",skip=0)

            self.anaconda.dispatch.skipStep("complete",skip=1)
            self.anaconda.dispatch.skipStep("u_complete",skip=0)
        else:
            self.anaconda.id.installationtype = False
            self.anaconda.dispatch.skipStep("u_filtertype",skip=1)
            self.anaconda.dispatch.skipStep("filtertype",skip=0)

            self.anaconda.dispatch.skipStep("network",skip=0)
            self.anaconda.dispatch.skipStep("u_network",skip=1)

            self.anaconda.dispatch.skipStep("parttype",skip=0)
            self.anaconda.dispatch.skipStep("u_parttype",skip=1)

            self.anaconda.dispatch.skipStep("tasksel",skip=0)
            self.anaconda.dispatch.skipStep("u_tasksel",skip=1)

            self.anaconda.dispatch.skipStep("complete",skip=0)
            self.anaconda.dispatch.skipStep("u_complete",skip=1)
        #import pdb
        #pdb.set_trace()
        return None
    
    def radiocallback(self,widget,data=None):
        self.buttonGroup_setCurrent = data
        
    def getScreen(self, anaconda):
        self.anaconda = anaconda
        self.intf = anaconda.intf

        isBlack = False
        import fvi
        x = fvi.get_iso_type()
        '''
        f = open("/root/isotype")
        lines = f.readlines()
        f.close()
    
        for x in lines:
            if x.find("vServer") != -1 or x.find("vCenter") != -1:
                isBlack = True
                break
        '''
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
        path = "/usr/share/anaconda/pixmaps/icon2_install_selection.png"
        i.set_from_file(path)
        i.show()
        fixed.put(i,45,15)
        label1 = gtk.Label()
        lstr = "<span font_desc='16' weight='bold' foreground='"+fontcolor+"'><b>安装方式:</b></span>"
        label1.set_markup(lstr)
        fixed.put(label1,160,23)
        label2 = gtk.Label()
        lstr = "<span font_desc='11.5' weight='bold' foreground='"+fontcolor+"'><b>选择一种安装方式</b></span>"
        label2.set_markup(lstr)
        fixed.put(label2,160,58)
        eboximage.add(fixed) 
        eboximage.show_all()
        
        vbox = gtk.VBox(False,0) 
        vbox.pack_start(eboximage,expand=False,fill=False)

        #######################################################
        fix = gtk.Fixed()
        label = gtk.Label()
        label.set_markup("<span font='10.5' foreground='#333333' size='large'><b>您想要选择哪种系统安装方式？</b></span>\
        ")
        fix.put(label,70,55)
    
        rvbox = gtk.VBox()
        rvbox.show()
        fix.put(rvbox,70,100)
        radio = gtk.RadioButton(None)
        radio.connect("toggled",self.radiocallback,"ordinary")
        rlabel1 = gtk.Label()
        rlabel1.set_markup("<span font='10.5' foreground='#333333' size='large'><b>普通安装</b></span>")
        lstr = "<span font='8.5' weight='50' foreground='#333333' size='large'><b>    建议选择此方式安装，可对网络，硬盘等信息进行配置。</b></span>"
        radio.add(rlabel1)
        rvbox.pack_start(radio, False,False,0)
        
        l = gtk.Label()
        l.set_markup(lstr)
        l.set_alignment(0.0, 0.5)
        rvbox.pack_start(l,False,False,5)

        radio.set_active(True)
        radio.show()
    
        radiof = gtk.RadioButton(radio)
        radiof.connect("toggled",self.radiocallback,"fast")
        rlabel2 = gtk.Label()
        rlabel2.set_markup("<span font='10.5' foreground='#333333' size='large'><b>一键安装</b></span>")
        lstr = "<span font='8.5' weight='50' foreground='#333333' size='large'><b>    安装介质将选择第一顺位物理硬盘（并清空该硬盘所有数据），安装网络为dhcp方式。若\
需要使用固定网络,请于安装后\n    的第一时间在本地界面进行网络配置修改。需要与其他主机通信时请不要使用此方式安装，避免dhcp网络的不稳定带来的\n    主机间通讯异常。</b></span>"
        radiof.add(rlabel2)
        rvbox.pack_start(radiof, False, False,5)
        
        
        
        l = gtk.Label()
        l.set_markup(lstr)
        l.set_alignment(0.0, 0.5)
        rvbox.pack_start(l,False,False,0)
        
        self.sn_entry = gtk.Entry()
        self.sn_entry.connect('insert-text',self.hinsert_text)
        try:
            self.sn_entry.set_text(self.anaconda.sn)
        except:
            pass
        sn_label = gtk.Label()
        sn_label.set_markup("<span font='10' foreground='#333333' size='large'><b>请输入出厂编号:</b></span>")
        sn_hbox = gtk.HBox()
        sn_hbox.pack_start(sn_label, False, False,5)
        sn_hbox.pack_start(self.sn_entry, False, False,5)
        rvbox.pack_start(sn_hbox, False, False,20)
        
        radiof.show()
        vbox.pack_start(fix,True,True)
        
        """f = gtk.FontSelection()
        vbox.pack_start(f,False,False,0)"""


        if self.anaconda.id.installationtype == True:
            self.buttonGroup_setCurrent = "fast"
            radiof.set_active(True)
            radio.set_active(False)
        else:
            self.buttonGroup_setCurrent = "ordinary"
            radiof.set_active(False)
            radio.set_active(True)
            
        sn_vbox = gtk.VBox(False,0)
        sn_vbox.show()
        
        ebox = gtk.EventBox()
        ebox.add(vbox)
        ebox.set_app_paintable(True)
        ebox.set_border_width(0)
        ebox.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#e6e6e6"))
        
        return ebox
