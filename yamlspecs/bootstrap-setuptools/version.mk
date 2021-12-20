ifeq ($(VERSION.MAJOR),8)
PYPKG = platform-python
PYSETUP = python3-setuptools
RPM.OBSOLETES = platform-python-setuptools
ADDPROVIDES = platform-python-setuptools
else
PYPKG = python
PYSETUP = python2-setuptools
ADDPROVIDES =  "python-setuptools-devel = $(VERSION)-$(RELEASE)"
endif

NAME 		= $(PYPKG)-setuptools
ARCHIVENAME 	= setuptools
VERSION 	= 41.0.0
RELEASE 	= 1
TARBALL_POSTFIX        = tar.gz
DISTRO          = $(ARCHIVENAME)-$(VERSION).$(TARBALL_POSTFIX)
RPM.EXTRAS      = "AutoReq: no\n%define __brp_mangle_shebangs /bin/echo turn of shebang mangling"
RPM.FILES       = /usr/lib/python$(PY.VERSION)/site-packages/*\n/usr/bin/*
RPM.ARCH	= noarch
RPM.PROVIDES	= python-distribute = $(VERSION)-$(RELEASE) $(ADDPROVIDES) $(PYSETUP) = $(VERSION)-$(RELEASE) 

