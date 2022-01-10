
# on RHEL8 load/unload prereq modules automatically
if [ ! -v MODULES_AUTO_HANDLING ]; then
   export MODULES_AUTO_HANDLING=1
fi

# Tell module to command to not be chatty
if [ ! -v MODULES_VERBOSITY ]; then
   export MODULES_VERBOSITY=concise
fi

if [ -f /opt/rcic/Modules/init/bash ]; then
  . /opt/rcic/Modules/init/bash
fi
