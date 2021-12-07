NAME 		= python-ruamel-yaml-clib
ARCHIVENAME 	= ruamel.yaml.clib
VERSION 	= 0.2.2
RELEASE 	= 1
TARBALL_POSTFIX	= tar.gz
DISTRO          = $(ARCHIVENAME)-$(VERSION).$(TARBALL_POSTFIX)
RPM.EXTRAS      = "AutoReq: no"
RPM.FILES       = /usr/lib64/python$(PY.VERSION)/site-packages
