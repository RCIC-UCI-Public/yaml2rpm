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
	echo "Targets for building/installing on Pristine environment"
	echo "      bootstrap - build/install RPMS needed before building yaml2rpm"
	echo "      download  - download TARBALLS from vault" 
	echo "      build     - build yaml2rpm RPMS" 
	echo "      install   - install yaml2rpm RPMS" 

bootstrap download build: 
	module avail
	YAML2RPM_INC=$(CWD)/yamlspecs/include YAML2RPM_HOME=$(CWD)/yamlspecs TEMPLATEDIR=$(CWD)/yamlspecs make --environment-overrides $@_pristine 

install:
	YAML2RPM_INC=$(CWD)/yamlspecs/include YAML2RPM_HOME=$(CWD)/yamlspecs TEMPLATEDIR=$(CWD)/yamlspecs make --environment-overrides YES=-y install-admix 
	
include yamlspecs/Makefile.toplevel

bootstrap_pristine:
	$(SUDO) yum -y install redhat-lsb-core
	make bootstrap_install  

download_pristine:
	make -e download

build_pristine:
	make --environment-overrides TEMPLATE_DIR=$(CWD)/yamlspecs -C yamlspecs -f Makefile.site 
	make --environment-overrides TEMPLATE_DIR=$(CWD)/yamlspecs -C yamlspecs buildall

$(BOOTSTRAP_PKGS):
	make -C yamlspecs/bootstrap-$@
	make -C yamlspecs/bootstrap-$@ pkginstall

bootstrap_build: $(BOOTSTRAP_PKGS)
bootstrap_install_nobuild:
	make createlocalrepo
	$(SUDO) yum -y -c yum.conf install $(BOOTSTRAP_PKGS_INST) 
bootstrap_install: $(BOOTSTRAP_PKGS) bootstrap_install_nobuild 
