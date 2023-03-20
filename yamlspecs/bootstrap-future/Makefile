# This is a specifc  Makefile that is called to build python-ruamel-yaml RPM
# needed by gen-definitions.py for processing of other yaml files 
# Prerequisite: rocks-devel RPM.

REDHAT.ROOT = $(CURDIR)/../../
-include $(ROCKSROOT)/etc/Rules.mk
include Rules.mk

-include ../bootstrap.inc 
ROCKSSHARE=/opt/rocks/share/devel
DOWNLOADER=$(ROCKSSHARE)/bin/get_sources.sh

default: download rpm

download: sources
	SURL=$(SURL) $(DOWNLOADER)
sources:
	mkdir sources

build: sources
	zcat sources/$(DISTRO) | tar -xf -
	(cd $(ARCHIVENAME)-$(VERSION); python ./setup.py build;)

install::
	(cd $(ARCHIVENAME)-$(VERSION); python ./setup.py $@ --root=$(ROOT)/; )

clean::
	rm -rf $(ARCHIVENAME)-$(VERSION) 
