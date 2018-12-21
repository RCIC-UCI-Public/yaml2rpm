## Handle automated loading/unloading of modules
set AUTOLOADED [string trim ${AUTOLOADED}]
if { [module-info mode load] } {setenv  ${envname} "${AUTOLOADED}"}
if { [module-info mode remove] && ! [module-info mode switch] } { UnloadPrereq "${AUTOLOADED}";  unsetenv $envname }
