TMPBUILD = tmpbuild
BUILDTEMPLATE = builder
TEMPLATEDIR = ..
TEMPLATE_FILES = $(wildcard $(TEMPLATEDIR)/$(BUILDTEMPLATE)/*)
GENERATE = ../gen-definitions.py
DEFINITIONS = Definitions.mk
SOURCES = ../sources

YAMLFILES = fcgi.yaml ior.yaml pigz.yaml
PKGS = $(YAMLFILES:.yaml=.pkg)

default: $(PKGS)

%.pkg : %.yaml
	make cleantmp $(TMPBUILD)
	$(GENERATE) $< > $(TMPBUILD)/$(DEFINITIONS)
	- install $*.patch $(TMPBUILD)
	- install  $(SOURCES)/$***gz $(TMPBUILD)
	make -C $(TMPBUILD) pkg
	touch $@

$(TMPBUILD):
	mkdir $(TMPBUILD)
	install $(TEMPLATE_FILES) $(TMPBUILD)

cleantmp: 
	- /bin/rm -rf $(TMPBUILD)

cleanpkg:
	- /bin/rm *pkg

clean: cleanpkg cleantmp

veryclean: clean
