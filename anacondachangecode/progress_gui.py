# -*- coding:utf8 -*-
# progress_gui.py: install/upgrade progress window setup.
#
# Copyright (C) 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007  Red Hat, Inc.
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

import os
import glob

import gtk
import pango

import gui
from flags import flags
from iw_gui import *
from constants import *
import language

import logging
log = logging.getLogger("anaconda")

class InstallProgressWindow (InstallWindow):
    windowTitle = N_("Installing Packages")

    def __init__ (self, ics):
        InstallWindow.__init__ (self, ics)
        ics.setPrevEnabled (False)
        ics.setNextEnabled (False)
        ics.cw.mainxml.get_widget("nextButton").hide()
        ics.cw.mainxml.get_widget("backButton").hide()
        self._updateChange = 0.01
        self._showPercentage = False

    def processEvents(self):
        gui.processEvents()

    def get_fraction(self):
        return self.progress.get_fraction()
    def set_fraction(self, pct):
        cur = self.get_fraction()
        if pct - cur > self._updateChange:
            self.progress.set_fraction(pct)
            if self._showPercentage:
                self.progress.set_text("%d %%" %(pct * 100,))
            self.processEvents()

    def set_label(self, txt):
        # handle txt strings that contain '&' and '&amp;'
        # we convert everything to '&' first, then take them all to '&amp;'
        # so we avoid things like &amp;&amp;
        # we have to use '&amp;' for the set_markup() method
        txt = txt.replace('&amp;', '&')
        txt = txt.replace('&', '&amp;')
        self.infolabel.set_markup(txt)
        self.infolabel.set_ellipsize(pango.ELLIPSIZE_END)
        self.processEvents()

    def set_text(self, txt):
        if self._showPercentage:
            log.debug("Setting progress text with showPercentage set")
            return
        self.progress.set_text(txt)
        self.processEvents()

    def renderCallback(self):
        self.intf.icw.nextClicked()

    def setShowPercentage(self, val):
        if val not in (True, False):
            raise ValueError, "Invalid value passed to setShowPercentage"
        self._showPercentage = val

    def _getRnotes(self):
        langs = []
        pixmaps = []
        if (os.environ.has_key('LANG')):
            langs = language.expandLangs(os.environ['LANG'])
        langs.append('')

        pixmaps = []
        paths = ("/tmp/product/pixmaps/rnotes/%s/*.png",
                 "/usr/share/anaconda/pixmaps/rnotes/%s/*.png")
        for p in paths:
            for lang in langs:
                path = p % lang
                pixmaps = glob.glob(path)
                if len(pixmaps) > 0:
                    break

        if len(pixmaps) > 0:
            files = pixmaps
        else:
            files = ["progress_first.png"]

        return files
        

    def getScreen (self, anaconda):
        self.intf = anaconda.intf
        if anaconda.dir == DISPATCH_BACK:
            self.intf.icw.prevClicked()
            return

        self.pixmaps = self._getRnotes()

        # Create vbox to contain components of UI
        vbox = gtk.VBox (False, 12)

        # Create rnote area

        #######################################
        
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
        path = "/usr/share/anaconda/pixmaps/icon12_vserver_installation.png"
        i.set_from_file(path)
        i.show()
        fixed.put(i,45,15)
        label1 = gtk.Label()
        label1.set_markup("<span font_desc=' 16' weight='bold' foreground='"+fontcolor+"'><b>安装软件：</b></span>")
        fixed.put(label1,160,23)
        label2 = gtk.Label()
        label2.set_markup("<span font_desc=' 11.5' weight='bold' foreground='"+fontcolor+"'><b>正在安装软件包，请稍等...</b></span>")
        fixed.put(label2,160,58)
        eboximage.add(fixed) 
        eboximage.show_all()

        vbox = gtk.VBox(False,0) 
        vbox.pack_start(eboximage,expand=False,fill=False)
        #####################################################
        fix = gtk.Fixed()
        self.progress = gtk.ProgressBar()
        
        eboxpro = gtk.EventBox()
        eboxpro.add(self.progress)
        
        eboxpro.set_size_request(800,25)
        fix.put(eboxpro,120,240)
        
        self.intf.setPackageProgressWindow(self)
        anaconda.id.setInstallProgressClass(self)

        vbox.pack_start(fix,True,True)
        return vbox
