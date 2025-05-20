## This a Makefile to drive the bootstrapping/building of RPMS
# Uncomment this line if using the yaml2rpm files
SHELL=/bin/bash
TEMPLATEDIR=$(YAML2RPM_HOME)
MAKEPARALLEL=$(YAML2RPM_HOME)/bin/runparallel

SILENT := $(findstring s,$(filter-out -%,$(MAKEFLAGS)))
ifndef USEHOME
HOME = $(shell pwd)
else
HOME = $(USEHOME)
endif

SUDO = sudo
AllRepoLockfile = /var/lock/yaml2rpm.lock
YUM = $(SUDO) /usr/bin/yum
#  YUM should always be flocked
#  When installing a bootstrapped package, need to lock both the repo creation and YUM as one 
YUMEXCLUSIVE = flock $(AllRepoLockfile) $(YUM)

## We want the name of the enclosing Makefile since
# this particular Makefile is usually included
THISMAKE := $(firstword $(MAKEFILE_LIST))
THISDIR := $(shell pwd)

ifndef ADMIX
ADMIX = $(shell basename $$(realpath ..))
endif

## Two marker files to determine if this Makefile is being called directly from
## an already-staged directory or from the admix's base yamlspecs directory

ADMIXROOT = $(shell if [ -f .admix.root ]; then cat .admix.root; else realpath ..; fi)
ADMIXYAMLS = $(shell if [ -f .admix.yamls ]; then cat .admix.yamls; else pwd; fi)

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
LOCALREPODIR = $(ADMIXROOT)
SOURCES = $(ADMIXROOT)/sources

## To support parallel SET BUILDS we need to define a subdirectory
## That
##   0. (Optionally) copies all files from set-specific yaml directory
##   1. Mirrors everything else (except .pkg) in the yamlspecs directory (via softlinks)
##   2. Defines that tmpbuild relative to this staging directory in that 
##
STAGEPREFIX = 00STAGE
STAGEBASE = $(STAGEPREFIX)$(SET)

## Determine if above the stagedir or in the stagedir
ifeq ($(THISDIR),$(ADMIXYAMLS))
STAGEDIR = $(THISDIR)/$(STAGEBASE)
else
STAGEDIR = $(THISDIR)
endif

##  
## Name of local directory for build. Cleared for each package built
## so it only supports one build a time
TMPBUILD = $(STAGEDIR)/tmpbuild
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

## How many SETS to build in parallel
PARALLEL = $(shell $(BASEGENERATE) -Q --query=parallel $(PACKAGES_FILE))
ifeq ($(PARALLEL),)
PARALLEL = 2
endif 

## Handling a version set. 
## A set file MUST have an entry 
## versions: <name of versions file>
## The set file set-$(SET).yaml is then used as the packages.yaml file.
## if SET is not empty, then we want to look in the 
## set file for versions: tag and use that file for versions going forward
## PACKAGES_FILE is then the set-$(SET) file
## There are three types of sets:
##   1. UNNAMED Set:  This is the "set" that corresponds to versions.yaml
##   2. ALLSETS: All Sets 
##   3. SERIAL_SETS: SETS Groups That must be built serially
VMAP = 
ifneq ($(PACKAGES_FILE),)
ALLSETS := $(shell $(BASEGENERATE) -Q --query=sets $(PACKAGES_FILE))
SERIAL_SETS := $(shell $(BASEGENERATE) -Q --query=serialsets --values $(PACKAGES_FILE))
SERIAL_SETS_PY := $(shell $(BASEGENERATE) -Q --raw --query=serialsets $(PACKAGES_FILE))
PARALLEL_SETS := $(filter-out $(SERIAL_SETS),$(ALLSETS))
else
SERIAL_SETS = 
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
BOOTSTRAP_ADDREPO = $(strip $(shell  $(GENERATE) --query=enablerepo  $(PACKAGES_FILE)))
MODULES_QUERY = $(shell  $(GENERATE) --no-defaults --quiet --query=build  $(PACKAGES_FILE) |  sed -e 's/ /.yaml /g' -e 's/$$/.yaml/') 
MODULES = $(MODULES_QUERY:None.yaml=)
MANIFEST = $(shell $(GENERATE) --no-defaults --quiet --query=manifest  $(PACKAGES_FILE) | sed -e 's/None//') 
else
BOOTSTRAP_MODULES = $(shell grep -s -v '\#' $(BOOTSTRAP_MODULES_FILE)) 
BOOTSTRAP_SYSTEM  = $(shell grep -s -v '\#' $(BOOTSTRAP_SYSTEM_FILE)) 
MODULES           = $(shell grep -s -v '\#' $(BUILD_MODULES_FILE) | sed 's/$$/.yaml/') 
MANIFEST          = $(shell grep -s -v '\#' $(MANIFEST_FILE)) 
endif

ifneq ("$(BOOTSTRAP_ADDREPO)","False")
ENABLEREPO = --enablerepo=$(BOOTSTRAP_ADDREPO)
endif 

PKGS = $(MODULES:.yaml=.pkg)
BOOTSTRAP_YAMLS = $(addsuffix .yaml, $(BOOTSTRAP_MODULES))

####  TARGETS ####

default: $(STAGEDIR) $(SOURCES) $(PKGS)

## This Target Bootstraps and builds packages.
## Non-conformant admixes should include this makefile and then
## define ALL_TARGETS 

.PHONY:  buildall buildall-parallel buildstart stageset stagedir thawyamls thawsources
ifndef ALL_TARGETS
ALL_TARGETS = bootstrap $(SOURCES) $(PKGS)
endif

buildall buildall-parallel:: buildstart stagedir thawsources $(ALL_TARGETS)
	echo "== Built ALL Targets ($(SET)): $^ =="
	echo "== Built ALL ($(SET)) $(shell date) =="

buildstart:
	echo "== BUILDING ALL ($(SET)) $(shell date) =="

## This section takes the yaml file and does various interpretations to create files
## 0. If required, create and populate the STAGEDIR
## 1. Create temp working directory $(TMPBUILD) - install template files from $(TEMPLATEDIR)/builder
## 2. Generate the Defintions.mk file compatible with the builder/Makefile builder/*mk definitions
##    located in $(TEMPLATEDIR) 
## 3. Execute instructions from the pretar definition (if any)
## 4. Execute patch from the patch definition (if any)
## 5. Copy the tarball from the $(SOURCES) directory
## 6. Copy any additional tarballs from $(SOURCES) directory (if any)
## 7. Execute "make pkg" in the $(TMPBUILD) directory 
## 8. Touch pkg file to indicate the build was completed.

%.pkg : $(SOURCES) stagedir

%.pkg : %.yaml
	echo "===== Building $@ ( $$(date) )========" 
	make -e -f $(THISMAKE) $(STAGEDIR)
	make -e -f $(THISMAKE) cleantmp $(TMPBUILD)
	(cd $(STAGEDIR); make -e -f $(THISMAKE) $(ADDFILTERS) thismod=$<)
	(cd $(STAGEDIR); $(GENERATE) $< > $(TMPBUILD)/$(DEFINITIONS))
	(cd $(STAGEDIR); echo "ADMIXROOT = $(ADMIXROOT)"  >> $(TMPBUILD)/$(DEFINITIONS))
	- ( cd $(STAGEDIR); $(GENERATE) -m $< > $(TMPBUILD)/modulefile )
	- ( cd $(STAGEDIR); $(GENERATE) --query=pretar $< | ADMIXROOT=$(ADMIXROOT) /bin/sh )
	- ( cd $(STAGEDIR); install $$($(GENERATE) --query=patch $<) $(TMPBUILD))
	- ( cd $(STAGEDIR); install  $(SOURCES)/$$($(GENERATE) --query=tarball $<) $(TMPBUILD))
	- ( cd $(STAGEDIR); install $$($(GENERATE) --query=addfile $<) $(TMPBUILD))
	- (cd $(STAGEDIR); for src in $$($(GENERATE) --query=addsource $<); do  \
		install $(SOURCES)/$$src $(TMPBUILD); done)
	make -e -C $(TMPBUILD) USEHOME=$(HOME) ADMIXROOT=$(ADMIXROOT) pkg 
	touch $(STAGEDIR)/$@
	echo "===== Completed $@ ( $$(date) )========" 

## Target copyset, thaw must be empty in this makefile
## When need to overwrite do in respective admix/yamlspecs/Makefile
## only needed for compelx admixes where there are multiple sets of yamls
## saved in subdirectories.
copyset:
thaw:
thawyamls:
thawsources:

stagedir: $(STAGEDIR)

## This creates the stage directory
#  1. fill .admix.root and .admix.yamls so that in the STAGEDIR, it can find home 
#  2. thaw -- used only the R4-admix
#  3. softlink all remaining files in the ADMIXYAMLS dir to the STAGEDIR
#
# 
$(STAGEDIR): 
	- mkdir $(STAGEDIR)
	- echo $(ADMIXROOT) > $(STAGEDIR)/.admix.root
	- echo $(ADMIXYAMLS) > $(STAGEDIR)/.admix.yamls
	- make -f $(THISMAKE) thawyamls
	(for fname in $$(find $(ADMIXYAMLS) -maxdepth 1 -printf '%P\n' | grep -v $(STAGEPREFIX)); do       \
		if [ ! -f $(STAGEDIR)/$$fname ]; then         \
		    [ "x$(SILENT)" != "x" ] || echo "softlinking $$fname";               \
		    ln -s $(ADMIXYAMLS)/$$fname $(STAGEDIR)/$$fname;        \
		fi;                                           \
	 done)	

cleanstage:
	if [ "x$(STAGEDIR)" != "x" ]  && [ $$(expr length $(STAGEDIR)) -ge 10 ]; then \
	       rm -rf $(STAGEDIR); \
	fi
	
manifest:: stagedir
	( cd $(STAGEDIR); MANIFEST_YAML=();                             \
	  for pkg in $(MANIFEST); do					\
		if [ -f $$pkg.yaml ]; then				\
		     MANIFEST_YAML+=("$$pkg.yaml");                     \
		else							\
			echo $$pkg;					\
		fi;							\
	  done;								\
	  if [ $${#MANIFEST_YAML[@]} -gt 0 ] ; then                        \
		$(GENERATE) --query=pkgname $${MANIFEST_YAML[@]}; fi	\
	)
	
ansible:
	make -f $(THISMAKE) -s manifest | xargs $(MANIFEST2ANSIBLE) --name $(ADMIX) 


module-provides:: stagedir
	( cd $(STAGEDIR); MANIFEST_YAML=();                                 \
	  for pkg in $(MANIFEST); do			                    \
		if [ -f $$pkg.yaml ]; then MANIFEST_YAML+=("$$pkg.yaml");fi;\
	  done;								    \
	  [ $${#MANIFEST_YAML[@]} -gt 0 ] &&                             \
	    modNames=`$(GENERATE) --query=module.logname $${MANIFEST_YAML[@]}`;    \
          for mod in $$modNames; do                                         \
	     if [ "$$mod" != "False" ]; then echo $$mod; fi;                \
	  done							            \
	)
module-requires:: stagedir
	( cd $(STAGEDIR); ALLMODS=();                                                       \
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
	

module-info:: stagedir
	( cd $(STAGEDIR); MODYAMLS=();                                  \
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
	- $(YUMEXCLUSIVE) $(ENABLEREPO) -y install $(BOOTSTRAP_SYSTEM) 
	echo $(BOOTSTRAP_MODULES)
	( cd $(STAGEDIR); for mod in $(BOOTSTRAP_MODULES); do					\
		make -e -f $(THISMAKE) $$mod.pkg;				\
		rpmname=$$($(GENERATE) --query=pkgname $$mod.yaml);		\
		flock $(AllRepoLockfile) make -e -f $(THISMAKE) ins-bootstrap PACKAGE=$$rpmname;	\
	  done									\
	)
ins-bootstrap:
	make -e -C $(LOCALREPODIR) createBootstrapRepo PACKAGE=$(PACKAGE);	\
	$(YUM) -y -c $(LOCALREPODIR)/yum.conf install $(PACKAGE)

unbootstrap::
	( cd $(STAGEDIR); BOOTSTRAP_YAMLS=();                             \ 
	  for mod in $(BOOTSTRAP_MODULES); do				  \
		BOOTSTRAP_YAMLS+=("$$mod.yaml");                          \
	  done;                                                           \
	  ALLRRPMS=$$($(GENERATE) --query=pkgname $${BOOTSTRAP_YAMLS[@]); \
          $(YUMEXCLUSIVE) -y erase $$ALLRPMS                                       \
	)

unbootstrap-sys:
	$(YUMEXCLUSIVE) -y erase $(BOOTSTRAP_SYSTEM);				\

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
	- /bin/rm -f $(STAGEDIR)/*pkg

cleanyaml:
	echo $(MODULES)
	( for mod in $(MODULES); do					\
		cleandir=$$($(GENERATE) --query=clean $$mod);		\
		if [ $$? == 0 ]; then /bin/rm -rf $$cleandir; fi;		\
	  done									\
	)
	
clean: cleanpkg cleantmp cleanyaml

veryclean:: clean cleanstage

FORCE:


## Targets that should iterate through sets after the BASE set 
## action is completed
##  --> IF BASEONLY is defined, then ALLSETS is not iterated
##  --> IF SET=<string>  is defined, then ALLSETS is not iterated
## This only make sense when called from the main yamlspecs directory
manifest module-requires module-provides module-info unbootstrap ::
ifndef BASEONLY
	if [ "$(SET)" == "" ] && [ "$(ALLSETS)" != "" ]; then \
	    for set in $(ALLSETS); do \
		make -s -e -f $(THISMAKE) SET=$$set stagedir; \
		make -C $(THISDIR)/$(STAGEBASE)$${set} -s -e -f $(THISMAKE) SET=$$set $@; \
	    done; \
	fi 
endif 

## Similar to above, but don't make the stagedir, it needs to be removed
veryclean ::
ifndef BASEONLY
	if [ "$(SET)" == "" ] && [ "$(ALLSETS)" != "" ]; then \
	    for set in $(ALLSETS); do \
		make -s -e -f $(THISMAKE) SET=$$set $@; \
	    done; \
	fi 
endif 

## Same as above, except make clean each stage. 
buildall ::
ifndef BASEONLY
	if [ "$(SET)" == "" ] &&  [ "$(ALLSETS)" != "" ] ; then \
	    for set in $(ALLSETS); do \
	        make -e SET=$$set -f $(THISMAKE) stagedir; \
		make -C $(THISDIR)/$(STAGEBASE)$${set} -e SET=$$set -f $(THISMAKE) clean; \
		make -C $(THISDIR)/$(STAGEBASE)$${set} -e -f $(THISMAKE) SET=$$set $@; \
	    done; \
	fi 
endif 

## As above, but builds each set in parallel. 
## Very similar to above except instead of making buildall in each set serially it:
##   1. it builds \n separated string of the above "make -e -f $(THISMAKE) SET=$$set $@;"
##   2. Creates stdout and stderr prefixes for each set
##   3. Uses the helper runparallel script to run upto $(PARALLEL) makes concurrently
##         -- builds the SERIAL_SETS (if any) in parallel
##         -- builds the PARALLEL_SETS (if any) in parallel
buildall-parallel ::
ifndef BASEONLY
	if [ "$(SET)" == "" ] && [ "$(ALLSETS)" != "" ] ; then \
		make -e PBUILD_SETS="$(SERIAL_SETS)" PBUILD_SETS_PY="$(SERIAL_SETS_PY)" -f $(THISMAKE) parallelBuild; \
		make -e PBUILD_SETS="$(PARALLEL_SETS)" PBUILD_SETS_PY="$(PARALLEL_SETS)" -f $(THISMAKE) parallelBuild; \
	fi
endif 

# This is passed a variable PBUILD_SETS from the buildall-parallel target
# These are either SERIAL_SETS or  ALLSETS
# Currently, only the perl-admix defines serialsets: in its packages.yaml file 
parallelBuild:
	## First setup each stage
	for set in $(PBUILD_SETS); do \
	   make -e SET=$$set -f $(THISMAKE) stagedir; \
	   make -C $(THISDIR)/$(STAGEBASE)$${set} -e SET=$$set -f $(THISMAKE) clean; \
	done; \
        TEMPLATE="make -C $(THISDIR)/$(STAGEBASE)%SET% -e -f $(THISMAKE) SET=%SET% buildall-parallel" ; \
	PATTERN="%SET%" ; \
	$(MAKEPARALLEL) -p $(PARALLEL) --autoprefix --template="$$TEMPLATE" --pattern="$$PATTERN" --variables="$(PBUILD_SETS_PY)" run

diag:
	echo "HOME:  $(HOME)"
	echo "BOOTSTRAP_MODULES: $(BOOTSTRAP_MODULES)"
	echo "BOOTSTRAP_YAMLS: $(BOOTSTRAP_YAMLS)"
	echo "MANIFEST: $(MANIFEST)"
	echo "THISMAKE: $(THISMAKE)"
	echo "MAKEFILE_LIST: $(MAKEFILE_LIST)"
	echo "ALL_TARGETS: $(ALL_TARGETS)"
	echo "ALLSETS: $(ALLSETS)"
	echo "PARALLEL_SETS: $(PARALLEL_SETS)"
	echo "SERIAL_SETS: $(SERIAL_SETS)"
	echo "SERIAL_SETS_PY: $(SERIAL_SETS_PY)"
	echo "SET: $(SET)"
	echo "ADMIX:  $(ADMIX)"
	echo "ADMIXROOT  $(ADMIXROOT)"
	echo "ADMIXYAMLS  $(ADMIXYAMLS)"
	echo "STAGEDIR  $(STAGEDIR)"
	echo "BOOTSTRAP_ADDREPO :$(BOOTSTRAP_ADDREPO):"
	echo "SILENT: $(SILENT)"
