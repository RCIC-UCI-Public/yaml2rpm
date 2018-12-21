## Handle automated loading/unloading of modules. This is intended
## to be included at the end of a environment module specification
## (C) 2018-2019 UC Regents
## Research Cyberinfrastructure Center, UC Irvine
## Author: Philip M. Papadopoulos
set AUTOLOADED [string trim ${AUTOLOADED}]
if { [module-info mode load] } {setenv  ${envname} "${AUTOLOADED}"}
if { [module-info mode remove] && ! [module-info mode switch] } { UnloadPrereq "${AUTOLOADED}";  unsetenv $envname }
