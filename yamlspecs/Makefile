TMPBUILD = tmpbuild
BUILDTEMPLATE = builder
TEMPLATEDIR = ..
TEMPLATE_FILES = $(wildcard $(TEMPLATEDIR)/$(BUILDTEMPLATE)/*)
LOCALREPODIR = $(TEMPLATEDIR)
GENERATE = ../gen-definitions.py
DEFINITIONS = Definitions.mk
SOURCES = ../sources

MODULES = $(shell  grep -v '\#' modules.build | sed 's/$$/.yaml/') 
BOOTSTRAP_MODULES = $(shell  grep -v '\#' modules.bootstrap) 

PKGS = $(MODULES:.yaml=.pkg)


foo:
	echo $(MODULES)
	echo $(BOOTSTRAP_MODULES)
default: $(PKGS)

%.pkg : %.yaml
	make cleantmp $(TMPBUILD)
	$(GENERATE) $< > $(TMPBUILD)/$(DEFINITIONS)
	- install $$($(GENERATE) --query=patch $<) $(TMPBUILD)
	- install  $(SOURCES)/$$($(GENERATE) --query=tarball $<) $(TMPBUILD)
	make -C $(TMPBUILD) pkg
	touch $@

bootstrap: 
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

clean: cleanpkg cleantmp

veryclean: clean
