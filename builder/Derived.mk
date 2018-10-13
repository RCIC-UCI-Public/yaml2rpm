# These are Derived Makefile definitions based on Rules.mk Defaults.mk Definitions.mk
SRC_TARBALL =  $(TARNAME)-$(VERSION).$(TARBALL-EXTENSION)
ifndef SRC_DIR
SRC_DIR	= $(TARNAME)-$(VERSION)
endif

## Files for Package
CONFIG.DESCRIPTION = $(CONFIGURE) $(CONFIGURE_ARGS)
RPM.DESCRIPTION = $(DESCRIPTION). Configured with $(CONFIG.DESCRIPTION).
RPM.DESCRIPTION += Modules loaded for compilation: $(MODULES).
RPM.PROVIDES	= $(TARNAME),$(VERSION)

#COMPRESSED CAT
ifneq (,$(findstring bz2, $(TARBALL-EXTENSION)))
CAT-COMPRESS = bzcat
else
CAT-COMPRESS = zcat
endif
