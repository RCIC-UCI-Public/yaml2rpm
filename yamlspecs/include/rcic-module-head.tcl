#####################################################################
## This is for generic module autoloading. It keeps track 
## of Autoloaded modules.  This type of functionality is becoming part
## of the environment modules (and LUA modules). This particular code
## will eventually be not needed.
##
## It is intended to be sourced in specific environment module files
## See examples in yaml2rpm-generated RPMS
## Load and Unload functions
## (C) 2018-2019 UC Regents
## Research Cyberinfrastructure Center, UC Irvine
## Author: Philip M. Papadopoulos

proc LoadPrereq { a } {
    global AUTOLOADED
    if { ! [is-loaded $a] } {
	module load $a
	# if the module name isn't in the AUTOLOADED environment, add it
	if { [string first $a $AUTOLOADED] < 0 } {
		append AUTOLOADED " ${a}"
	}
    }
}

proc UnloadPrereq { a } {
	set mods [ split $a ]
	foreach mod $mods {
		module unload $mod 
	}
}

## This defines an environment variable that tracks which modules this
## module has autoloaded.
#t reads the existing environment for the use case of
#  $ module load foo; module load foo
#  The second load would wipe out the record of autoloaded modules

set envname "__AUTOLOAD_[module-info name]"
regsub -all {[[:punct:]]} $envname _ envname
if { [info exists ::env($envname)] } {
	set envcontents $::env($envname)
} else {
	set envcontents "" 
}
set AUTOLOADED $envcontents 
set AUTOLOADED [string trim ${AUTOLOADED}]
if { [module-info mode switch1] } { UnloadPrereq "${AUTOLOADED}" }
if { [module-info mode switch2] } { LoadPrereq "${AUTOLOADED}" }
