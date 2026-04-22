NAME 		= python-future
ifeq ($(strip $(VERSION.MAJOR)), 10)
ARCHIVENAME 	= python-future
VERSION 	= 1.0.0
else
ARCHIVENAME 	= future
VERSION 	= 0.18.2
endif
RELEASE 	= 1
TARBALL_POSTFIX	= tar.gz
DISTRO          = $(ARCHIVENAME)-$(VERSION).$(TARBALL_POSTFIX)
RPM.ARCH        = noarch
RPM.FILES       = /usr/lib/python$(PY.VERSION)/site-packages/*\n/usr/bin/*
RPM.EXTRAS      = "AutoReq: no\\n%define __brp_mangle_shebangs /bin/echo"
