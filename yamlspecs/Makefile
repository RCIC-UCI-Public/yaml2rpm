## This a Makefile to drive the bootstrapping/building of RPMS
# Uncomment this line if using the yaml2rpm files
SHELL=/bin/bash
TEMPLATEDIR=$(YAML2RPM_HOME)
HOME=$(shell pwd)

SUDO = sudo
YUM = $(SUDO) /usr/bin/yum

## We want the name of the enclosing Makefile since
# this particular Makefile is usually included
THISMAKE := $(firstword $(MAKEFILE_LIST))

ifndef ADMIX
ADMIX = $(shell basename $$(realpath ..))
endif

## System template dir should be $YAML2RPM_HOME
## if not defined, expect local copy (e.g. as in master Git repo)
ifndef TEMPLATEDIR
TEMPLATEDIR = .
endif

BUILDTEMPLATE = builder
TEMPLATE_FILES = $(wildcard $(TEMPLATEDIR)/$(BUILDTEMPLATE)/*)
DEFINITIONS = Definitions.mk

BASEGENERATE = $(TEMPLATEDIR)/bin/gen-definitions.py $(GENEXTRAS)
MANIFEST2ANSIBLE = $(TEMPLATEDIR)/bin/manifest2ansible.py 

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

## Handling a version set. 
## A set file MUST have an entry 
## versions: <name of versions file>
## The set file set-$(SET).yaml is then used as the packages.yaml file.
## if SET is not empty, then we want to look in the 
## set file for versions: tag and use that file for versions going forward
## PACKAGES_FILE is then the set-$(SET) file
VMAP = 
ifneq ($(PACKAGES_FILE),)
ALLSETS := $(shell $(BASEGENERATE) -Q --query=sets $(PACKAGES_FILE))
else
ALLSETS = 
endif

ifdef SET 
PACKAGES_FILE = set-$(SET).yaml
VERSIONSFILE = $(shell $(BASEGENERATE) --query=versions $(PACKAGES_FILE))
VMAP = --versions=$(VERSIONSFILE)

ifeq ("$(VERSIONSFILE)","")
$(error set file $(PACKAGES_FILE) has no versions: tag)
endif

endif

GENERATE=$(BASEGENERATE) $(VMAP)


# Values are taken from packages.yaml file or from modules.* files
ifneq ($(PACKAGES_FILE),)
BOOTSTRAP_QUERY = $(shell  $(GENERATE)  --no-defaults --quiet --query=bootstrap  $(PACKAGES_FILE)) 
BOOTSTRAP_MODULES = $(BOOTSTRAP_QUERY:None=)
BOOTSTRAP_SYSTEM = $(shell  $(GENERATE) --no-defaults --quiet  --query=system  $(PACKAGES_FILE)) 
MODULES = $(shell  $(GENERATE) --no-defaults --quiet --query=build  $(PACKAGES_FILE) |  sed -e 's/ /.yaml /g' -e 's/$$/.yaml/') 
MANIFEST = $(shell  $(GENERATE) --no-defaults --quiet --query=manifest  $(PACKAGES_FILE)) 
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

buildall:: buildstart $(ALL_TARGETS)
	echo "== Built ALL Targets ($(SET)): $^ =="
	echo "== Built ALL ($(SET)) $(shell date) =="

buildstart:
	echo "== BUILDING ALL ($(SET)) $(shell date) =="

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
	- install $$($(GENERATE) --query=addfile $<) $(TMPBUILD)
	- (for src in $$($(GENERATE) --query=addsource $<); do  \
		install $(SOURCES)/$$src $(TMPBUILD); done)
	make -e -C $(TMPBUILD) pkg 
	touch $@
	echo "===== Completed $@ ( $$(date) )========" 

## Target copyset must be empty in this makefile
## When need to overwrite do in respective admix/yamlspecs/Makefile
## only needed for compelx admixes where there are multiple sets of yamls
## saved in subdirectories.
copyset:

manifest:: copyset
	( MANIFEST_YAML=();                                             \
	  for pkg in $(MANIFEST); do					\
		if [ -f $$pkg.yaml ]; then				\
		     MANIFEST_YAML+=("$$pkg.yaml");                     \
		else							\
			echo $$pkg;					\
		fi;							\
	  done;								\
	  [ $${#MANIFEST_YAML[@]} -gt 0 ] &&                            \
		$(GENERATE) --query=pkgname $${MANIFEST_YAML[@]};	\
	)
	
ansible:
	make -f $(THISMAKE) -s manifest | xargs $(MANIFEST2ANSIBLE) --name $(ADMIX) 


module-provides:: copyset
	( MANIFEST_YAML=();                                                 \
	  for pkg in $(MANIFEST); do			                    \
		if [ -f $$pkg.yaml ]; then MANIFEST_YAML+=("$$pkg.yaml");fi;\
	  done;								    \
	  [ $${#MANIFEST_YAML[@]} -gt 0 ] &&                             \
	    modNames=`$(GENERATE) --query=module.logname $${MANIFEST_YAML[@]}`;    \
          for mod in $$modNames; do                                         \
	     if [ "$$mod" != "False" ]; then echo $$mod; fi;                \
	  done							            \
	)
module-requires:: copyset
	( ALLMODS=();                                                       \
	  for pkg in $(MODULES) $(BOOTSTRAP_YAMLS); do	                    \
		if [ -f $$pkg ]; then ALLMODS+=($$pkg); fi;                 \
	  done;                                                             \
	  [ $${#ALLMODS[@]} -gt 0 ] &&                                       \
	     needModule=`$(GENERATE) --query=build.modules $${ALLMODS[@]}`;   \
          for x in $$needModule; do                                         \
		if [ "$$x" != "False" ] && [ "$$x" != "True" ]              \
		&& [ "$$x" != "None" ]; then                                \
			echo -e $$x| tr ' ' '\n';                           \
		fi; 	                                                    \
	  done                                                              \
	)
	

module-info:: copyset
	( MODYAMLS=();                                                  \
          for ypkg in $(MODULES) $(BOOTSTRAP_YAMLS); do                 \
		if [ -f $$ypkg ]; then MODYAMLS+=("$$ypkg");fi;         \
	  done;                                                         \
          if [ $${#MODYAMLS[@]} -gt 0 ]; then                       \
	  $(GENERATE) -c $${MODYAMLS[@]}; fi                            \
	)

admix-bootstrap-yaml:
	( NEEDS=$$(make -f $(THISMAKE) -s module-requires | sort | uniq); \
	PROVIDES=$$(make -f $(THISMAKE) -s module-provides | sort | uniq);\
	echo "!include rcic-admix-requires.yaml" > $(ADMIX)-bootstrap.yaml;\
        echo "---" >> $(ADMIX)-bootstrap.yaml; \
        echo "- package: $(ADMIX)-bootstrap" >> $(ADMIX)-bootstrap.yaml; \
        echo "  name: $(ADMIX)-bootstrap" >> $(ADMIX)-bootstrap.yaml; \
        echo "  requires: " >> $(ADMIX)-bootstrap.yaml; \
 	for x in $$NEEDS; do echo $$PROVIDES | grep -q $$x; \
	  if [ $$? != 0 ]; then echo "    - $$x" >> \
		$(ADMIX)-bootstrap.yaml; \
	  fi;\
	done )

bootstrap:: 
	- $(YUM) -y install $(BOOTSTRAP_SYSTEM) 
	echo $(BOOTSTRAP_MODULES)
	( for mod in $(BOOTSTRAP_MODULES); do					\
		make -e -f $(THISMAKE) $$mod.pkg;							\
		make -e -C $(LOCALREPODIR) createlocalrepo; 			\
		rpmname=$$($(GENERATE) --query=pkgname $$mod.yaml);		\
		$(YUM) -y -c $(LOCALREPODIR)/yum.conf install $$rpmname;		\
	  done									\
	)

unbootstrap::
	( BOOTSTRAP_YAMLS=();                                             \ 
	  for mod in $(BOOTSTRAP_MODULES); do				  \
		BOOTSTRAP_YAMLS+=("$$mod.yaml");                          \
	  done;                                                           \
	  ALLRRPMS=$$($(GENERATE) --query=pkgname $${BOOTSTRAP_YAMLS[@]); \
          $(YUM) -y erase $$ALLRPMS                                       \
	)

unbootstrap-sys:
	$(YUM) -y erase $(BOOTSTRAP_SYSTEM);				\

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

veryclean:: clean

FORCE:


## Targets that should iterate through sets after the BASE set 
## action is completed
##  --> IF BASEONLY is defined, then ALLSETS is not iterated
##  --> IF SET=<string>  is defined, then ALLSETS is not iterated
manifest module-requires module-provides module-info veryclean unbootstrap ::
ifndef BASEONLY
	if [ "$(SET)" == "" ] && [ "$(ALLSETS)" != "" ]; then \
	    for set in $(ALLSETS); do \
		make -s -e -f $(THISMAKE) SET=$$set $@; \
	    done; \
	fi 
endif 

## Same as above, except make clean between each stage. 
buildall ::
ifndef BASEONLY
	if [ "$(SET)" == "" ] && [ "$(ALLSETS)" != "" ]; then \
	    for set in $(ALLSETS); do \
		make -e SET=$$set -f $(THISMAKE) clean; \
		make -e -f $(THISMAKE) SET=$$set $@; \
	    done; \
	fi 
endif 

diag:
	echo "HOME:  $(HOME)"
	echo "BOOTSTRAP_MODULES: $(BOOTSTRAP_MODULES)"
	echo "BOOTSTRAP_YAMLS: $(BOOTSTRAP_YAMLS)"
	echo "MANIFEST: $(MANIFEST)"
	echo "THISMAKE: $(THISMAKE)"
	echo "MAKEFILE_LIST: $(MAKEFILE_LIST)"
	echo "ALL_TARGETS: $(ALL_TARGETS)"
	echo "ALLSETS: $(ALLSETS)"
	echo "SET: $(SET)"
