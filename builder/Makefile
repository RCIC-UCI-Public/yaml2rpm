-include $(ROCKSROOT)/etc/Rules.mk
include Rules.mk
include Override.mk

ifndef  PKGMAKE
PKGMAKE = $(MAKE) 
endif

## These exist so that CUSTOM_* can be used in shell scripts without
## create syntax errors

ifndef  MAKEINSTALL
CUSTOM_MAKEINSTALL =  echo
else
CUSTOM_MAKEINSTALL = $(MAKEINSTALL)
endif 

ifndef INSTALLEXTRA
CUSTOM_INSTALLEXTRA =  echo
else
CUSTOM_INSTALLEXTRA = $(INSTALLEXTRA)
endif 
#################################################################

%: %.in
	$(SED) $(SEDSCRIPT) $^ > $@

build:
	$(CAT-COMPRESS) $(SRC_TARBALL) |  $(TAR) -xf -
	(							\
		module purge; 					\
		if [ "$(MODULES)" !=  "" ]; then module load $(MODULES); fi; 			\
		cd $(SRC_DIR);					\
		$(PATCH_METHOD) $(PATCH_ARGS) < ../$(PATCH_FILE);  		\
		$(PRECONFIGURE);				\
		$(CONFIGURE) $(CONFIGURE_ARGS);  		\
		$(PKGMAKE) $(BUILDTARGET) ;			\
		module purge; 					\
	)

install:: 
	(							\
		module purge; 					\
		if [ "$(MODULES)" !=  "" ]; then module load $(MODULES); fi; 			\
		cd $(SRC_DIR);					\
		if [ ! -d $(ROOT)/$(PKGROOT) ]; then mkdir -p $(ROOT)/$(PKGROOT); fi; \
		if [ "$(MAKEINSTALL)" == "" ]; then		\
			$(MAKE) prefix=$(ROOT)/$(PKGROOT) $(INSTALLTARGET);	\
		else 						\
			$(CUSTOM_MAKEINSTALL);				\
		fi;						\
		if [ "$(MODULENAME)" != "" -a "$(MODULESPATH)" != "" ]; then		\
			mkdir -p $(ROOT)/$(MODULESPATH);     				\
			$(INSTALL) -m 644 ../modulefile $(ROOT)/$(MODULESPATH)/$(MODULENAME);  	\
		fi;								\
		if [ "$(INSTALLEXTRA)" != "" ]; then $(CUSTOM_INSTALLEXTRA); fi; \
		module purge; 					\
	)

clean::
	rm -rf $(SRC_DIR) 
	rm -rf $(NAME).spec.in


