# This is a specifc  Makefile that is called to build python-ruamel-yaml RPM
# needed by gen-definitions.py for processing of other yaml files 
# Prerequisite: rocks-devel RPM.

REDHAT.ROOT = $(CURDIR)/../../
-include $(ROCKSROOT)/etc/Rules.mk
include Rules.mk

SURL=https://googledrive.com/host/1L-VOgFEvE3OVVQYT3Okfu7Fy9MLUcr8W
ROCKSSHARE=/opt/rocks/share/devel
DOWNLOADER=$(ROCKSSHARE)/bin/get_sources.sh

default: download rpm

download: sources
	SURL=$(SURL) $(DOWNLOADER)
sources:
	mkdir sources

build: sources
	tar xzf sources/$(DISTRO) 
	(cd $(ARCHIVENAME)-$(VERSION); python ./setup.py build;)

install::
	(cd $(ARCHIVENAME)-$(VERSION); python ./setup.py $@ --root=$(ROOT)/; )

clean::
	rm -rf $(ARCHIVENAME)-$(VERSION) 

diag:
	echo $(VERSION.MAJOR) "'$(PY.VERSION)'"
