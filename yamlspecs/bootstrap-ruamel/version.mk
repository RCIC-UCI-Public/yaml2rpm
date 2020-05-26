NAME 		= python-ruamel-yaml
ARCHIVENAME 	= ruamel.yaml
VERSION 	= 0.16.5
RELEASE 	= 1
TARBALL_POSTFIX	= tar.xz
DISTRO          = $(ARCHIVENAME)-$(VERSION).$(TARBALL_POSTFIX)
RPM.EXTRAS      = "AutoReq: no"
RPM.FILES       = /usr/lib/python2.7/site-packages/*
