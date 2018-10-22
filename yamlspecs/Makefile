## This a Makefile to drive the bootstrapping/building of RPMS

## System template dir should be /opt/rocks/yaml2rpm
## if not defined, expect local copy (e.g. as in master Git repo)
ifndef TEMPLATEDIR
TEMPLATEDIR = ..
endif

BUILDTEMPLATE = builder
TEMPLATE_FILES = $(wildcard $(TEMPLATEDIR)/$(BUILDTEMPLATE)/*)
LOCALREPODIR = $(TEMPLATEDIR)
GENERATE = $(TEMPLATEDIR)/gen-definitions.py
DEFINITIONS = Definitions.mk

## Local sources of tarballs
SOURCES = ../sources
## Name of local directory for build. Cleared for each package built, so 
## only supports one at a time
TMPBUILD = tmpbuild

## These define the modules for bootstrap. 
# BOOTSTRAP_SYSTEM - modules part of the OS/other repo that need to be installed for building
# BOOTSTRAP_MODULES - pkgs that need to be built and installed locally before anything else can be 
#                     be built
# MODULES - the packages to be built

BOOTSTRAP_MODULES = $(shell  grep -v '\#' modules.bootstrap) 
BOOTSTRAP_SYSTEM = $(shell  grep -v '\#' modules.system) 
MODULES = $(shell  grep -v '\#' modules.build | sed 's/$$/.yaml/') 

PKGS = $(MODULES:.yaml=.pkg)


default: $(PKGS)

## This section takes the yaml file and does various interpretations to create files
## 1. Create temp working directory $(TMPBUILD) - install template files from $(TEMPLATEDIR)/builder
## 2. Generate the Defintions.mk file compatible with the builder/Makefile builder/*mk definitions
##    located in $(TEMPLATEDIR) 
## 3. Execute instructions from the pretar definition (if any)
## 4. Execute patch from the patch definition (if any)
## 5. Copy the tarball from the $(SOURCES) directory
## 6. Execute "make pkg" in the $(TMPBUILD) directory 
## 7. Touch pkg file to indicate the build was completed.

%.pkg : %.yaml
	make cleantmp $(TMPBUILD)
	$(GENERATE) $< > $(TMPBUILD)/$(DEFINITIONS)
	- $(GENERATE) -m $< > $(TMPBUILD)/modulefile
	- $(GENERATE) --query=pretar $< | /bin/sh
	- install $$($(GENERATE) --query=patch $<) $(TMPBUILD)
	- install  $(SOURCES)/$$($(GENERATE) --query=tarball $<) $(TMPBUILD)
	make -C $(TMPBUILD) pkg
	touch $@

bootstrap: 
	yum -y install $(BOOTSTRAP_SYSTEM) 
	( for mod in $(BOOTSTRAP_MODULES); do					\
		make $$mod.pkg;							\
		make -C $(LOCALREPODIR) createlocalrepo; 			\
		rpmname=$$($(GENERATE) --query=pkgname $$mod.yaml);		\
		yum -y -c $(LOCALREPODIR)/yum.conf install $$rpmname;		\
	  done									\
	)
	
$(TMPBUILD):
	mkdir $(TMPBUILD)
	install $(TEMPLATE_FILES) $(TMPBUILD)

cleantmp: 
	- /bin/rm -rf $(TMPBUILD)

cleanpkg:
	- /bin/rm *pkg

cleanyaml:
	( for mod in $(MODULES); do					\
		cleandir=$$($(GENERATE) --query=clean $$mod);		\
		if [ $$? == 0 ]; then /bin/rm -r $$cleandir; fi;		\
	  done									\
	)
	
clean: cleanpkg cleantmp cleanyaml

veryclean: clean
