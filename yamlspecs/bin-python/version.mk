NAME 		= bin-python
VERSION 	= 3
RELEASE 	= 1
RPM.DESCRIPTION     = Use alternatives to set /usr/bin/python to /usr/bin/python3. Also provides /usr/bin/python for RPMS that require unversioned python. It will not change an existing /usr/bin/python file.
RPM.ARCH        = noarch
RPM.REQUIRES    = /usr/sbin/alternatives /usr/bin/python3
RPM.PROVIDES    = /usr/bin/python
RPM.SCRIPTLETS.FILE = scriptlets
RPM.ROOT	= /usr/share/$(NAME)
RPM.FILES	= $(RPM.ROOT)