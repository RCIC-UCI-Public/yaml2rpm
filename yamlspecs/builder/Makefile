# This is a generic Makefile that is called from generate spec files.
# in particular, in the %build section of the generated Makefile, the
# build target of the this Makefile is invoked.
# similarly, the install target is called by the %install section of the 
# generated spec file

-include $(ROCKSROOT)/etc/Rules.mk
include Rules.mk
include Override.mk


# use "make" unless PKGMAKE has been specified
ifndef  PKGMAKE
PKGMAKE = $(MAKE) 
endif

## These exist so that CUSTOM_* can be used in shell scripts without
## creating syntax errors

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

ifndef NO_SRC_DIR 
MODFILE_DIR = ..
DO_CD = True 
else
MODFILE_DIR = .
DO_CD = False
endif 

### Any OS-release specific things should go here
# Defaults:
AUTOMODULE=""

__OS_MAJOR_RELEASE=$(shell /bin/cat /etc/os-release | grep ^REDHAT_SUPPORT_PRODUCT_VERSION | /usr/bin/cut -f 2 -d\" | /usr/bin/cut -f 1 -d.)

# RHEL8 (and rebuilds) 
ifeq ($(__OS_MAJOR_RELEASE),8) 
AUTOMODULE="--auto"
endif

#################################################################

%: %.in
	$(SED) $(SEDSCRIPT) $^ > $@


# Usual build case:
#        The SRC tarball (which is most often the downloaded tar source, unchanged)
#        1. unpack the tarball
#        2. change into the source directory then 
#             a. apply patches
#             b. apply any changes prior to configure step 
#             c. configure the package
#             d. build the software
# Unusual build case:
#        1. There is no src tarball (often just some files that need installing and packaging)
#        2. Same as above (but definitions should override steps)
build:
	- $(CAT-COMPRESS) $(SRC_TARBALL) |  $(UNTAR)
	(							\
		module purge; 					\
		if [ "$(MODULES)" !=  "" ]; then module $(AUTOMODULE) load $(MODULES); fi;	\
		[ $(DO_CD) == True ] && cd $(SRC_DIR);    	\
		$(PATCH_METHOD) $(PATCH_ARGS) < ../$(PATCH_FILE);  		\
		$(PRECONFIGURE);				\
		$(CONFIGURE) $(CONFIGURE_ARGS);  		\
		$(PKGMAKE) $(BUILDTARGET) ;			\
		module purge; 					\
	)

install:: 
	(							\
		module purge; 					\
		if [ "$(MODULES)" !=  "" ]; then module $(AUTOMODULE) load $(MODULES); fi;	\
		[ $(DO_CD) == True ] && cd $(SRC_DIR);		\
		if [ ! -d $(ROOT)/$(PKGROOT) ]; then mkdir -p $(ROOT)/$(PKGROOT); fi; \
		if [ "$(MAKEINSTALL)" == "" ]; then		\
			$(MAKE) prefix=$(ROOT)$(PKGROOT) $(INSTALLTARGET);	\
		else 						\
			$(CUSTOM_MAKEINSTALL);				\
		fi;						\
		if [ "$(MODULENAME)" != "" -a "$(MODULESPATH)" != "" ]; then		\
			mkdir -p $(ROOT)/$(MODULESPATH);     				\
			$(INSTALL) -m 644 $(MODFILE_DIR)/modulefile $(ROOT)/$(MODULESPATH)/$(MODULENAME);  	\
		fi;								\
		if [ "$(INSTALLEXTRA)" != "" ]; then $(CUSTOM_INSTALLEXTRA); fi; \
		module purge; 					\
	)

clean::
	- rm -rf $(SRC_DIR) 
	- rm -rf $(NAME).spec.in


