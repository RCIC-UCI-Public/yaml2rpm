# Defaults.mk
# These are common defaults for generic builds
BUILDTARGET = 
INSTALLTARGET = install
CONFIGURE  = ./configure
CONFIGURE_ARGS = --prefix=$(PKGROOT)
REDHAT.ROOT = $(CURDIR)/../
RELEASE = 1
VENDOR = RCIC @ UC Irvine
