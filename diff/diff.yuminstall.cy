Index: yuminstall.py.cy
===================================================================
--- yuminstall.py.cy	(版本 13803)
+++ yuminstall.py.cy	(工作副本)
@@ -327,6 +327,7 @@
         # Only needed for media installs.
         self.currentMedia = None
         self.mediagrabber = None
+        self._loopdev_used = None
 
         # Where is the source media mounted?  This is the directory
         # where Packages/ is located.
@@ -433,7 +434,7 @@
                         _("Unable to access the disc."))
 
     def _switchImage(self, discnum):
-        umountImage(self.tree, self.currentMedia)
+        umountImage(self.tree, self.currentMedia, self._loopdev_used)
         self.currentMedia = None
 
         # mountDirectory checks before doing anything, so it's safe to
@@ -441,9 +442,11 @@
         mountDirectory(self.anaconda.methodstr,
                        self.anaconda.intf.messageWindow)
 
-        self._discImages = mountImage(self.isodir, self.tree, discnum,
-                                      self.anaconda.intf.messageWindow,
-                                      discImages=self._discImages)
+        (self._loopdev_used, self._discImages) = mountImage(self.isodir, self.tree, discnum,
+                                                            self.anaconda.intf.messageWindow,
+                                                            discImages=self._discImages)
+
+
         self.currentMedia = discnum
 
     def configBaseURL(self):
@@ -462,9 +465,21 @@
             if m.startswith("hd:"):
                 if m.count(":") == 2:
                     (device, path) = m[3:].split(":")
+                    fstype = "auto"
                 else:
                     (device, fstype, path) = m[3:].split(":")
 
+                # First check for an installable tree
+                isys.mount(device, self.tree, fstype=fstype)
+                #if os.path.exists("%s/%s/repodata/repomd.xml" % (self.tree, path)):
+                if os.path.exists("%s/%s/Packages" % (self.tree, path)):
+                    self._baseRepoURL = "file://%s/%s" % (self.tree, path)
+                    return
+                isys.umount(self.tree, removeDir=False)
+
+                # Look for .iso images
+
+
                 self.isodir = "/mnt/isodir/%s" % path
 
                 # This takes care of mounting /mnt/isodir first.
@@ -1583,9 +1598,12 @@
             selectKernel("kernel")
 
     def selectFSPackages(self, storage):
+        fspkgs = set()
         for device in storage.fsset.devices:
             # this takes care of device and filesystem packages
-            map(self.selectPackage, device.packages)
+            for pkg in device.packages:
+                fspkgs.add(pkg)
+        map(self.selectPackage, fspkgs)
 
     # anaconda requires several programs on the installed system to complete
     # installation, but we have no guarantees that some of these will be
