# Copyright (c) 2000 - 2020 The Regents of the University of California.
# All rights reserved.	
# This includes the Generic toplevel Makefile - most admixes should
# be able to use this.

SHELL = /bin/bash
CWD := $(shell pwd)
default: 
	module avail
	YAML2RPM_INC=$(CWD)/yamlspecs/include YAML2RPM_HOME=$(CWD)/yamlspecs TEMPLATEDIR=$(CWD)/yamlspecs make --environment-overrides buildthis
install:
	YAML2RPM_INC=$(CWD)/yamlspecs/include YAML2RPM_HOME=$(CWD)/yamlspecs TEMPLATEDIR=$(CWD)/yamlspecs make --environment-overrides install-admix 
	
include yamlspecs/Makefile.toplevel
buildthis:
	$(SUDO) yum -y install redhat-lsb-core
	#make setuptools-install
	#make future-install
	#make ruamel-yaml-install
	#make ruamel-yaml-clib-install
	#make -e download
	make -e -C yamlspecs buildall

setuptools future ruamel-yaml ruamel-yaml-clib:
	make -C yamlspecs/bootstrap-$@

%-install: %
	make createlocalrepo
	$(SUDO) yum -y -c yum.conf install python-$?
