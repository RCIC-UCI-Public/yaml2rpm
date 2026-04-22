NAME 		= python-ruamel-yaml-clib
ARCHIVENAME 	= ruamel.yaml.clib
ifeq ($(filter 8 9,$(VERSION.MAJOR)),)
    VERSION = 0.2.15
else
    VERSION = 0.2.2
endif
RELEASE 	= 1
TARBALL_POSTFIX	= tar.gz
DISTRO          = $(ARCHIVENAME)-$(VERSION).$(TARBALL_POSTFIX)
RPM.EXTRAS      = "AutoReq: no\\n%global source_date_epoch_from_changelog 0"
RPM.FILES       = /usr/lib64/python$(PY.VERSION)/site-packages
