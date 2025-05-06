# Defaults.mk
# These are common defaults for generic builds
BUILDTARGET = 
INSTALLTARGET = install
CONFIGURE  = ./configure
CONFIGURE_ARGS = --prefix=$(PKGROOT)
RELEASE = 1
VENDOR = RCIC @ UC Irvine
PATCH_CMD = patch
PATCH_NONE = echo
PATCH_ARGS = -p1
