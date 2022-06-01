# Copyright (c) 2000 - 2020 The Regents of the University of California.
# All rights reserved.	
# This includes the Generic toplevel Makefile - most admixes should
# be able to use this.

SHELL = /bin/bash
CWD := $(shell pwd)
OS.MAJOR = $(shell lsb_release -rs | cut -d . -f 1)


## Packages that need to be built prior to yamlrpm 
BOOTSTRAP_PKGS = bin-python future setuptools ruamel-yaml ruamel-yaml-clib
TMP0_BOOTSTRAP_PKGS = $(BOOTSTRAP_PKGS:%=python-%) 
TMP1_BOOTSTRAP_PKGS = $(TMP0_BOOTSTRAP_PKGS:python-bin-python=bin-python)
ifeq ($(OS.MAJOR),8)
BOOTSTRAP_PKGS_INST = $(TMP1_BOOTSTRAP_PKGS:python-setuptools=platform-python-setuptools)
else
BOOTSTRAP_PKGS_INST = $(TMP1_BOOTSRAP_PKGS)
endif

default: 
	module avail
	YAML2RPM_INC=$(CWD)/yamlspecs/include YAML2RPM_HOME=$(CWD)/yamlspecs TEMPLATEDIR=$(CWD)/yamlspecs make --environment-overrides buildthis
install:
	YAML2RPM_INC=$(CWD)/yamlspecs/include YAML2RPM_HOME=$(CWD)/yamlspecs TEMPLATEDIR=$(CWD)/yamlspecs make --environment-overrides install-admix 
	
include yamlspecs/Makefile.toplevel
buildthis:
	$(SUDO) yum -y install redhat-lsb-core
	make bin-python-install
	make setuptools-install
	make future-install
	make ruamel-yaml-install
	make ruamel-yaml-clib-install
	make -e download
	make -e -C yamlspecs buildall

$(BOOTSTRAP_PKGS):
	make -C yamlspecs/bootstrap-$@

bootstrap_build: $(BOOTSTRAP_PKGS)
bootstrap_install_nobuild:
	make createlocalrepo
	$(SUDO) yum -y -c yum.conf install $(BOOTSTRAP_PKGS_INST) 
bootstrap_install: $(BOOTSTRAP_PKGS) bootstrap_install_nobuild 
