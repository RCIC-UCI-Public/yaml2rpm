NAME 		= bin-python
VERSION 	= 3
RELEASE 	= 2
RPM.DESCRIPTION     = Use alternatives to set /usr/bin/python to /usr/bin/python3. Also provides /usr/bin/python for RPMS that require unversioned python. It will not change an existing /usr/bin/python file. It will do NONE of the above if installed on Redhat/CentOS 7
RPM.ARCH        = noarch
ifneq ($(strip $(ROCKS.OS.VERSION.MAJOR)), 7)
RPM.PROVIDES    = /usr/bin/python
RPM.REQUIRES    = /usr/sbin/alternatives /usr/bin/python3 /etc/os-release
else
RPM.REQUIRES    = /etc/os-release
endif
RPM.SCRIPTLETS.FILE = scriptlets
RPM.ROOT	= /usr/share/$(NAME)
RPM.FILES	= $(RPM.ROOT)
