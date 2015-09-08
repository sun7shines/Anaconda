# -*- coding:utf8 -*-
# congrats_gui.py: install/upgrade complete screen.
#
# Copyright (C) 2000, 2001, 2002, 2003, 2004, 2005, 2006  Red Hat, Inc.
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

import gtk
import gui
from iw_gui import *
from constants import *
import os
import platform
import iutil
import gettext
_ = lambda x: gettext.ldgettext("anaconda", x)
import congrats_next
class CongratulationWindow (InstallWindow):		

    windowTitle = N_("Congratulations")

    def __init__ (self, ics):
        InstallWindow.__init__(self, ics)

        ics.setPrevEnabled(False)

        # force buttonbar on in case release notes viewer is running
        ics.cw.mainxml.get_widget("buttonBar").set_sensitive(True)

        self.rebootButton = ics.cw.mainxml.get_widget("rebootButton")

        # this mucks around a bit, but it's the weird case and it's
        # better than adding a lot of complication to the normal
        ics.cw.mainxml.get_widget("nextButton").hide()
        
        if os.path.exists(os.environ.get("LIVE_BLOCK", "/dev/mapper/live-osimg-min")):
            ics.cw.mainxml.get_widget("closeButton").show()
            ics.cw.mainxml.get_widget("closeButton").grab_focus()
        else:
            self.rebootButton.show()
            self.rebootButton.grab_focus()
            ics.cw.mainxml.get_widget("rebootButton").show()
            ics.cw.mainxml.get_widget("rebootButton").grab_focus()
            
        window = ics.cw.mainxml.get_widget("mainWindow")
        window.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("white"))
        window.set_size_request(1024,768)
    
        mainbox = ics.cw.mainxml.get_widget("mainBox")
        
        window.remove(mainbox)
        hbox = gtk.HBox()
        i = gtk.Image()
        #path = "/home/she/glade/screen13_end.png"
        path = "/usr/share/anaconda/pixmaps/screen13_end.png"
        i.set_from_file(path)
        i.show()
        hbox.pack_start(i,False,False,0)
        button =  ics.cw.mainxml.get_widget("rebootButton")
        hbuttonbox2 = ics.cw.mainxml.get_widget("hbuttonbox2")
        hbuttonbox2.remove(button)
        button.set_size_request(110,32)
        #########################################################
        
        label = gtk.Label()
        label.set_markup("<span font=' 11' foreground='#333333' size='large'><b>\
恭喜您,您的系统安装已经完成。\n\n请重启以便使用安装的系统。请注意：可使用更新以确定\n\
您的系统正常工作，且建议在重启后安装这些更新。</b></span>")
    
        vbox = gtk.VBox()
        hbox0 = gtk.HBox()
        hbox1 = gtk.HBox()
    
        hbox0.pack_end(label,True,True,100)
        hbox1.pack_end(button,False,False,100)
        vbox.pack_start(hbox0,False,False,200)
        vbox.pack_end(hbox1,False,False,30)
        hbox.pack_end(vbox,False,False,0)
        window.add(hbox)
        label.show()
        hbox0.show()
        hbox1.show()
        vbox.show()
        hbox.show()
        window.show()


    def getNext(self):
        # XXX - copy any screenshots over
        gui.copyScreenshots()

    # CongratulationWindow tag=NA
    def getScreen (self, anaconda):
        hbox = gtk.HBox (False, 5)
        
        #pix = gui.readImageFromFile ("done.png")
        #if pix:
        #    a = gtk.Alignment ()
        #    a.add (pix)
        #    a.set (0.5, 0.5, 1.0, 1.0)
        #    a.set_size_request(200, -1)
        #    hbox.pack_start (a, False, False, 36)

        congrats_next.func(anaconda)

        gtk.gdk.beep()
        return hbox

