## This a Makefile to drive the bootstrapping/building of RPMS
# Uncomment this line if using the yaml2rpm files
TEMPLATEDIR=/opt/rocks/yaml2rpm

## Name of this Makefile
THISMAKE := $(lastword $(MAKEFILE_LIST))

## System template dir should be /opt/rocks/yaml2rpm
## if not defined, expect local copy (e.g. as in master Git repo)
ifndef TEMPLATEDIR
TEMPLATEDIR = ..
endif

BUILDTEMPLATE = builder
TEMPLATE_FILES = $(wildcard $(TEMPLATEDIR)/$(BUILDTEMPLATE)/*)
DEFINITIONS = Definitions.mk
DEFAULTS = pkg-defaults.yaml
GENERATE = $(TEMPLATEDIR)/gen-definitions.py -d $(DEFAULTS)

## Local sources of tarballs
LOCALREPODIR = ..
SOURCES = ../sources
## Name of local directory for build. Cleared for each package built, so 
## only supports one at a time
TMPBUILD = tmpbuild

## These define the modules for bootstrap. 
# BOOTSTRAP_SYSTEM - modules part of the OS/other repo that need to be installed for building
# BOOTSTRAP_MODULES - pkgs that need to be built and installed locally before anything else can be 
#                     be built
# MODULES - the packages to be built

BOOTSTRAP_MODULES_FILE = modules.bootstrap 
BOOTSTRAP_SYSTEM_FILE = modules.system 
BUILD_MODULES_FILE =  modules.build
BOOTSTRAP_MODULES = $(shell  grep -v '\#' $(BOOTSTRAP_MODULES_FILE)) 
BOOTSTRAP_SYSTEM = $(shell  grep -v '\#' $(BOOTSTRAP_SYSTEM_FILE)) 
MODULES = $(shell  grep -v '\#' $(BUILD_MODULES_FILE) | sed 's/$$/.yaml/') 

PKGS = $(MODULES:.yaml=.pkg)


default: $(PKGS)

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

%.pkg : %.yaml
	make -e -f $(THISMAKE) cleantmp $(TMPBUILD)
	$(GENERATE) $< > $(TMPBUILD)/$(DEFINITIONS)
	- $(GENERATE) -m $< > $(TMPBUILD)/modulefile
	- $(GENERATE) --query=pretar $< | /bin/sh
	- install $$($(GENERATE) --query=patch $<) $(TMPBUILD)
	- install  $(SOURCES)/$$($(GENERATE) --query=tarball $<) $(TMPBUILD)
	- (for src in $$($(GENERATE) --listsep=" " --query=addsource --quiet $<); do  \
		install $(SOURCES)/$$src $(TMPBUILD); done)
	make -e -C $(TMPBUILD) pkg 
	touch $@

bootstrap: 
	- yum -y install $(BOOTSTRAP_SYSTEM) 
	echo $(BOOTSTRAP_MODULES)
	( for mod in $(BOOTSTRAP_MODULES); do					\
		make -e -f $(THISMAKE) $$mod.pkg;							\
		make -e -C $(LOCALREPODIR) createlocalrepo; 			\
		rpmname=$$($(GENERATE) --query=pkgname $$mod.yaml);		\
		yum -y -c $(LOCALREPODIR)/yum.conf install $$rpmname;		\
	  done									\
	)

unbootstrap:
	( ALLRPMS='';								\
	  for mod in $(BOOTSTRAP_MODULES); do					\
		rpmname=$$($(GENERATE) --query=pkgname $$mod.yaml);		\
                ALLRPMS="$$ALLRPMS $$rpmname";					\
	  done;									\
          yum -y erase $$ALLRPMS 						\
	)
unbootstrap-sys:
	yum -y erase $(BOOTSTRAP_SYSTEM);					\

$(TMPBUILD):
	mkdir $(TMPBUILD)
	install $(TEMPLATE_FILES) $(TMPBUILD)

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
	echo $(BOOTSTRAP_MODULES)
