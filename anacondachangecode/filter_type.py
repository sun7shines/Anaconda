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

from constants import *
import gui
from partition_ui_helpers_gui import *
from pixmapRadioButtonGroup_gui import pixmapRadioButtonGroup

from iw_gui import *
from flags import flags
from storage.deviceaction import *

import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)

class FilterTypeWindow(InstallWindow):
    def __init__(self, ics):
        InstallWindow.__init__(self, ics)
        ics.setTitle("Filter Type")
        ics.setNextEnabled(True)

    def getNext(self):
        #if self.buttonGroup.getCurrent() == "simple":
        # 每次进入本界面都默认选中基本存储设备，不管是不是第一此进入本届面 7-1-2013 修改
#        if self.buttonGroup_setCurrent == "simple":
#            self.anaconda.id.simpleFilter = True
#        else:
#            self.anaconda.id.simpleFilter = False
        
        if self.radio.get_active():
            self.anaconda.id.simpleFilter = True
        else:
            self.anaconda.id.simpleFilter = False
        
        return None
    
    def radiocallback(self,widget,data=None):
        self.buttonGroup_setCurrent = data
            
    def getScreen(self, anaconda):
        self.anaconda = anaconda
        self.intf = anaconda.intf
        
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
        lstr = "<span font_desc=' 11.5' weight='bold' foreground='"+fontcolor+"'><b>选择一种存储设备</b></span>"
        label2.set_markup(lstr)
        fixed.put(label2,160,58)
        eboximage.add(fixed) 
        eboximage.show_all()

        vbox = gtk.VBox(False,0) 
        vbox.pack_start(eboximage,expand=False,fill=False)
        
        fix = gtk.Fixed()
        label = gtk.Label()
        label.set_markup("<span font=' 10.5' foreground='#333333' size='large'><b>您的安装将使用哪种设备？</b></span>\
        ")
        fix.put(label,70,55)
    
        rvbox = gtk.VBox()
        rvbox.show()
        fix.put(rvbox,70,100)
        self.radio = gtk.RadioButton(None)
        self.radio.connect("toggled",self.radiocallback,"simple")
        rlabel1 = gtk.Label()
        rlabel1.set_markup("<span font=' 10.5' foreground='#333333' size='large'><b>基本存储设备</b></span>")
        lstr = "<span font=' 8.5' foreground='#525252' size='large'><b>    安装或者升级到存储设备的典型类型。如果您不确定哪个选项适合您，您可能应该选择这个\
选项。</b></span>"
        self.radio.add(rlabel1)
        
        rvbox.pack_start(self.radio, False,False,0)
        l = gtk.Label()
        l.set_markup(lstr)
        l.set_alignment(0.0, 0.5)
        rvbox.pack_start(l,False,False,5)
        
        self.radio.set_active(True)
        self.radio.show()
    
        self.radiof = gtk.RadioButton(self.radio)
        self.radiof.connect("toggled",self.radiocallback,"complex")
        rlabel2 = gtk.Label()
        rlabel2.set_markup("<span font=' 10.5' foreground='#333333' size='large'><b>指定存储设备</b></span>")
        lstr = "<span font=' 8.5' foreground='#525252' size='large'><b>    安装或者升级到企业级设备，比如存储局域网（SAN）。这个选项可让您添加FCoE/iSCSI/zFCP磁盘并过滤\
\n    掉安装程序应该忽略的设备。</b></span>"
        self.radiof.add(rlabel2)
    
        rvbox.pack_start(self.radiof, False, False,5)
        l = gtk.Label()
        l.set_markup(lstr)
        l.set_alignment(0.0, 0.5)
        rvbox.pack_start(l,False,False,0)
        
        self.radiof.show()
        vbox.pack_start(fix,True,True)

        
        if self.anaconda.id.simpleFilter == True:
            #self.buttonGroup.setCurrent("simple")
            self.buttonGroup_setCurrent = "simple"
#            radiof.set_active(False)
#            radio.set_active(True)
        else:
            #self.buttonGroup.setCurrent("complex")
            self.buttonGroup_setCurrent = "complex"
#            radiof.set_active(True)
#            radio.set_active(False)
        
        # 默认选中基本存储设备
        self.radiof.set_active(False)
        self.radio.set_active(True)
        return vbox
