# This is a specific  Makefile that is called to build python-ruamel-yaml RPM
# needed by gen-definitions.py for processing of other yaml files 
# Prerequisite: rocks-devel RPM.

REDHAT.ROOT = $(CURDIR)/../../
-include $(ROCKSROOT)/etc/Rules.mk
include Rules.mk

-include ../bootstrap.inc
ROCKSSHARE=/opt/rocks/share/devel
DOWNLOADER=$(ROCKSSHARE)/bin/get_sources.sh

ifeq ($(strip $(ROCKS.OS.VERSION.MAJOR)), 7)
PYTHON_DEV_RPM = python-devel 
else
PYTHON_DEV_RPM = platform-python-devel 
endif

default: prereqs download rpm

prereqs:
	- yum -y install $(PYTHON_DEV_RPM)
	
download: sources
	SURL=$(SURL) $(DOWNLOADER)
sources:
	mkdir sources

build: sources
	#xzcat sources/$(DISTRO) | tar -xf -
	tar xzf sources/$(DISTRO) 
	(cd $(ARCHIVENAME)-$(VERSION); python ./setup.py build;)

install::
	(cd $(ARCHIVENAME)-$(VERSION); python ./setup.py $@ --root=$(ROOT)/; )

clean::
	rm -rf $(ARCHIVENAME)-$(VERSION) 
