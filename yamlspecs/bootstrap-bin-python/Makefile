# This is a specifc  Makefile that creates the bin-python RPM
# It declare that it provides /usr/bin/python
# In it's postinstall scriptlet it uses alternative 
# Prerequisite: rocks-devel RPM.

REDHAT.ROOT = $(CURDIR)/../../
-include $(ROCKSROOT)/etc/Rules.mk
include Rules.mk
ROCKSSHARE=/opt/rocks/share/devel

default: rpm

build: 
	echo "no build"

install::
	mkdir -p $(ROOT)/$(RPM.ROOT)
	echo "RPM uses /usr/sbin/alternatives Link to /usr/bin/python from /usr/bin/python3"	 > $(ROOT)/$(RPM.ROOT)/README
	echo "It will NOT change an existing link"	 >> $(ROOT)/$(RPM.ROOT)/README


