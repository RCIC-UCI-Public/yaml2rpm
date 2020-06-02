NAME 		= python-setuptools
ARCHIVENAME 	= setuptools
VERSION 	= 41.0.0
RELEASE 	= 1
TARBALL_POSTFIX	= tar.gz
DISTRO          = $(ARCHIVENAME)-$(VERSION).$(TARBALL_POSTFIX)
RPM.EXTRAS      = "AutoReq: no"
RPM.FILES       = /usr/lib/python2.7/site-packages/*\n/usr/bin/*
