# Copyright (c) 2000 - 2020 The Regents of the University of California.
# All rights reserved.	
# This includes the Generic toplevel Makefile - most admixes should
# be able to use this.

SHELL = /bin/bash
CWD := $(shell pwd)
default: 
	module avail
	YAML2RPM_INC=$(CWD)/yamlspecs/include YAML2RPM_HOME=$(CWD) TEMPLATEDIR=$(CWD) make --environment-overrides buildall
install:
	YAML2RPM_INC=$(CWD)/yamlspecs/include YAML2RPM_HOME=$(CWD) TEMPLATEDIR=$(CWD) make --environment-overrides install-admix 
	
include yamlspecs/Makefile.toplevel
buildall:
	$(SUDO) yum -y install redhat-lsb-core
	make setuptools-install
	make future-install
	make ruamel-install
	make ruamel-clib-install
	make -e download
	make -e -C yamlspecs buildall

setuptools future ruamel ruamel-clib:
	make -C yamlspecs/bootstrap-$@

ruamel-install: ruamel
	make createlocalrepo
	$(SUDO) yum -y -c yum.conf install python-ruamel-yaml 

ruamel-clib-install: ruamel-clib
	make createlocalrepo
	$(SUDO) yum -y -c yum.conf install python-ruamel-yaml-clib

setuptools-install: setuptools
	make createlocalrepo
	$(SUDO) yum -y -c yum.conf install python-setuptools

future-install: future
	make createlocalrepo
	$(SUDO) yum -y -c yum.conf install python-future
