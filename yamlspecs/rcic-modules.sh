
# on RHEL8 load/unload prereq modules automatically
if [ ! -v MODULES_AUTO_HANDLING ]; then
   export MODULES_AUTO_HANDLING=1
fi

if [ -f /opt/rcic/Modules/init/bash ]; then
  . /opt/rcic/Modules/init/bash
fi
