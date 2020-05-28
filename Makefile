# Copyright (c) 2000 - 2020 The Regents of the University of California.
# All rights reserved.	
# This includes the Generic toplevel Makefile - most admixes should
# be able to use this.

CWD := $(shell pwd)
default: 
	YAML2RPM_INC=$(CWD)/yamlspecs/include YAML2RPM_HOME=$(CWD) TEMPLATEDIR=$(CWD) make --environment-overrides buildall
install:
	YAML2RPM_INC=$(CWD)/yamlspecs/include YAML2RPM_HOME=$(CWD) TEMPLATEDIR=$(CWD) make --environment-overrides install-admix 
	
include yamlspecs/Makefile.toplevel
buildall:
	make ruamel ruamel-install
	make -e download
	make -e -C yamlspecs buildall

ruamel:
	make -C yamlspecs/bootstrap-ruamel

ruamel-install:
	make createlocalrepo
	$(SUDO) yum -y -c yum.conf install python-ruamel-yaml 

