# These are Derived Makefile definitions based on Rules.mk Defaults.mk Definitions.mk
ifndef SRC_TARBALL
SRC_TARBALL =  $(TARNAME)-$(VERSION).$(TARBALL-EXTENSION)
endif
ifndef SRC_DIR
SRC_DIR	= $(TARNAME)-$(VERSION)
endif

## Files for Package
CONFIG.DESCRIPTION = $(CONFIGURE) $(CONFIGURE_ARGS)
RPM.DESCRIPTION = $(DESCRIPTION). Configured with $(CONFIG.DESCRIPTION).
RPM.DESCRIPTION += Modules loaded for compilation: $(MODULES)

#COMPRESSED CAT
ifneq (,$(findstring bz2, $(TARBALL-EXTENSION)))
CAT-COMPRESS = bzcat
else ifneq (,$(findstring xz, $(TARBALL-EXTENSION)))
CAT-COMPRESS = xzcat
else ifneq (,$(findstring zip, $(TARBALL-EXTENSION)))
CAT-COMPRESS = unzip 
else
CAT-COMPRESS = zcat
endif

#UNTAR
ifneq (,$(findstring zip, $(TARBALL-EXTENSION)))
UNTAR = /bin/wc 
else
UNTAR = $(TAR) -xf - 
endif
