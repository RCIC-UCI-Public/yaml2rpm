## This a Makefile to drive the bootstrapping/building of RPMS
# Uncomment this line if using the yaml2rpm files
SHELL=/bin/bash
TEMPLATEDIR=/opt/rocks/yaml2rpm
HOME=$(shell pwd)

SUDO = sudo
YUM = $(SUDO) /usr/bin/yum

## We want the name of the enclosing Makefile since
# this particular Makefile is usually included
THISMAKE := $(firstword $(MAKEFILE_LIST))

## System template dir should be /opt/rocks/yaml2rpm
## if not defined, expect local copy (e.g. as in master Git repo)
ifndef TEMPLATEDIR
TEMPLATEDIR = ..
endif

BUILDTEMPLATE = builder
TEMPLATE_FILES = $(wildcard $(TEMPLATEDIR)/$(BUILDTEMPLATE)/*)
DEFINITIONS = Definitions.mk

GENERATE = $(TEMPLATEDIR)/gen-definitions.py $(GENEXTRAS)

## Local sources of tarballs
LOCALREPODIR = ..
SOURCES = ../sources
## Name of local directory for build. Cleared for each package built
## so it only supports one build a time
TMPBUILD = tmpbuild
ADDFILTERS = addfilters

## These define the modules.
# BOOTSTRAP_SYSTEM - modules part of the OS/other repo that need to be installed for building
# BOOTSTRAP_MODULES - pkgs that need to be built and installed locally before anything else can be 
#                     be built
# MODULES - the packages to be built
#
# These can be specified in packages.yaml file with components as lists of modules, eg:
#
# bootstrap:
#    - packagename
#    - packagename2
# system:
#    - rpm name
#    - rpm name2
# build:
#    - packagename1
#    - packagename2
# manifest:
#    - packagename
#    - rpm name 
# 
# Alternatively, in place of packages.yaml file the same entries can be listed in separate files
# with the following file naming convention:
#            modules.bootstrap, modules.system, modules.build, modules.manifest
 
# These are default settings. Can be overwritten in respective yamlspecs/Makefile
# if placed AFTER the line that includes this default Makefile
BOOTSTRAP_MODULES_FILE = modules.bootstrap 
BOOTSTRAP_SYSTEM_FILE = modules.system
BUILD_MODULES_FILE =  modules.build
MANIFEST_FILE =  $(wildcard modules.manifest)
ifeq ($(MANIFEST_FILE),)
MANIFEST_FILE = $(BUILD_MODULES_FILE)
endif
PACKAGES_FILE = $(wildcard packages.yaml)

# Values are taken from packages.yaml file or from modules.* files
ifneq ($(PACKAGES_FILE),)
BOOTSTRAP_QUERY = $(shell  $(GENERATE) --no-defaults --quiet --listsep=' ' --query=bootstrap  $(PACKAGES_FILE)) 
BOOTSTRAP_MODULES = $(subst, None, ,$(BOOTSTRAP_QUERY))
BOOTSTRAP_SYSTEM = $(shell  $(GENERATE) --no-defaults --quiet  --listsep=' ' --query=system  $(PACKAGES_FILE)) 
MODULES = $(shell  $(GENERATE) --no-defaults --quiet --listsep=' ' --query=build  $(PACKAGES_FILE) |  sed -e 's/ /.yaml /g' -e 's/$$/.yaml/') 
MANIFEST = $(shell  $(GENERATE) --no-defaults --quiet  --listsep=' ' --query=manifest  $(PACKAGES_FILE)) 
else
BOOTSTRAP_MODULES = $(shell grep -s -v '\#' $(BOOTSTRAP_MODULES_FILE)) 
BOOTSTRAP_SYSTEM  = $(shell grep -s -v '\#' $(BOOTSTRAP_SYSTEM_FILE)) 
MODULES           = $(shell grep -s -v '\#' $(BUILD_MODULES_FILE) | sed 's/$$/.yaml/') 
MANIFEST          = $(shell grep -s -v '\#' $(MANIFEST_FILE)) 
endif

PKGS = $(MODULES:.yaml=.pkg)
BOOTSTRAP_YAMLS = $(addsuffix .yaml, $(BOOTSTRAP_MODULES))

####  TARGETS ####

default: $(SOURCES) $(PKGS)

## This Target Bootstraps and builds packages.
## Non-conformant admixes should include this makefile and then
## define ALL_TARGETS 

.PHONY:  buildall buildstart
ifndef ALL_TARGETS
ALL_TARGETS = bootstrap $(SOURCES) $(PKGS)
endif

buildall: buildstart $(ALL_TARGETS)
	echo "== Built ALL Targets: $^ =="
	echo "== Built ALL $(shell date) =="
buildstart:
	echo "== BUILDING ALL $(shell date) =="

## This section takes the yaml file and does various interpretations to create files
## 1. Create temp working directory $(TMPBUILD) - install template files from $(TEMPLATEDIR)/builder
## 2. Generate the Defintions.mk file compatible with the builder/Makefile builder/*mk definitions
##    located in $(TEMPLATEDIR) 
## 3. Execute instructions from the pretar definition (if any)
## 4. Execute patch from the patch definition (if any)
## 5. Copy the tarball from the $(SOURCES) directory
## 6. Copy any additional tarballs from $(SOURCES) directory (if any)
## 7. Execute "make pkg" in the $(TMPBUILD) directory 
## 8. Touch pkg file to indicate the build was completed.

%.pkg : $(SOURCES)

%.pkg : %.yaml
	echo "===== Building $@ ( $$(date) )========" 
	make -e -f $(THISMAKE) cleantmp $(TMPBUILD)
	make -e -f $(THISMAKE) $(ADDFILTERS) thismod=$<
	$(GENERATE) $< > $(TMPBUILD)/$(DEFINITIONS)
	- $(GENERATE) -m $< > $(TMPBUILD)/modulefile
	- $(GENERATE) --query=pretar $< | /bin/sh
	- install $$($(GENERATE) --query=patch $<) $(TMPBUILD)
	- install  $(SOURCES)/$$($(GENERATE) --query=tarball $<) $(TMPBUILD)
	- install $$($(GENERATE) --listsep=" " --query=addfile $<) $(TMPBUILD)
	- (for src in $$($(GENERATE) --listsep=" " --query=addsource $<); do  \
		install $(SOURCES)/$$src $(TMPBUILD); done)
	make -e -C $(TMPBUILD) pkg 
	touch $@
	echo "===== Completed $@ ( $$(date) )========" 

manifest:
	( for pkg in $(MANIFEST); do					\
		if [ -f $$pkg.yaml ]; then				\
		     $(GENERATE) --query=pkgname $$pkg.yaml;		\
		else							\
			echo $$pkg;					\
		fi;							\
	  done								\
	)


module-provides:
	( for pkg in $(MANIFEST); do					\
		if [ -f $$pkg.yaml ]; then				\
		     isModule=`$(GENERATE) --query=envmodule $$pkg.yaml`;	\
		     if [ "$$isModule" == "True" ]; then                \
		        $(GENERATE) --query=module.loadname $$pkg.yaml;	        \
		     fi;					\
		fi;							\
	  done								\
	)
module-requires:
	( for pkg in $(MODULES) $(BOOTSTRAP_YAMLS); do					\
		if [ -f $$pkg ]; then				\
		     needModule=`$(GENERATE) --query=build.modules --listsep="\\n" $$pkg`;	\
		     if [ "$$needModule" != "False" ]; then                \
		        [ "$$needModule" != "None" ] && echo -e $$needModule;	        \
		     fi;					\
		fi;							\
	  done								\
	)
	
bootstrap: 
	- $(YUM) -y install $(BOOTSTRAP_SYSTEM) 
	echo $(BOOTSTRAP_MODULES)
	( for mod in $(BOOTSTRAP_MODULES); do					\
		make -e -f $(THISMAKE) $$mod.pkg;							\
		make -e -C $(LOCALREPODIR) createlocalrepo; 			\
		rpmname=$$($(GENERATE) --query=pkgname $$mod.yaml);		\
		$(YUM) -y -c $(LOCALREPODIR)/yum.conf install $$rpmname;		\
	  done									\
	)

unbootstrap:
	( ALLRPMS='';								\
	  for mod in $(BOOTSTRAP_MODULES); do					\
		rpmname=$$($(GENERATE) --query=pkgname $$mod.yaml);		\
                ALLRPMS="$$ALLRPMS $$rpmname";					\
	  done;									\
          $(YUM) -y erase $$ALLRPMS 						\
	)

unbootstrap-sys:
	$(YUM) -y erase $(BOOTSTRAP_SYSTEM);					\

$(TMPBUILD):
	mkdir $(TMPBUILD)
	install $(TEMPLATE_FILES) $(TMPBUILD)

$(ADDFILTERS)::
	echo

download: $(SOURCES)
	if [ "$$PKG" == "" ]; then \
	   echo "please call as make download PKG='<name of pkg>'"; \
	else \
 	   url=$$($(GENERATE) --query=vendor_source $$PKG.yaml); \
 	   tarball=$$($(GENERATE) --query=tarball $$PKG.yaml); \
	   wget -O $(SOURCES)/$$tarball $$url; \
	fi

$(SOURCES):
	/bin/mkdir -p $@

cleantmp: 
	- /bin/rm -rf $(TMPBUILD)

cleanpkg:
	- /bin/rm *pkg

cleanyaml:
	echo $(MODULES)
	( for mod in $(MODULES); do					\
		cleandir=$$($(GENERATE) --query=clean $$mod);		\
		if [ $$? == 0 ]; then /bin/rm -r $$cleandir; fi;		\
	  done									\
	)
	
clean: cleanpkg cleantmp cleanyaml

veryclean: clean

FORCE:

diag:
	echo "HOME:  $(HOME)"
	echo "BOOTSTRAP_MODULES: $(BOOTSTRAP_MODULES)"
	echo "BOOTSTRAP_YAMLS: $(BOOTSTRAP_YAMLS)"
	echo "MANIFEST: $(MANIFEST)"
	echo "THISMAKE: $(THISMAKE)"
	echo "MAKEFILE_LIST: $(MAKEFILE_LIST)"
	echo "ALL_TARGETS: $(ALL_TARGETS)"
