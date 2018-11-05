# yaml2rpm
Generic Methodology for building RPMS
This software uses the underlying Rocks methodology for automatically creating RPM spec
files to create packages.  Where it differs from Rocks is that a 
YAML-based specification of a package is used to define the specific details of a 
component, instead of a subdirectory structure for each package (see the rocksclusters github rolls for many examples of the subdirectory structure.

Most (open-source) software starts with a source tarball, extracts the tarball, 
configures for the local environment,  executes "make" and then executes "make install".
In the above, "make" might be "cmake" or some other software-specific tool. The last step,
to turn the result of the above, community-standard, process into an installable package
is often deemed too time-consuming or difficult. The advantages of creating a package include:
  - File system conflicts resulting from different software builds are flagged prior-to-install
  - Software dependency resolution staves off many errors when attempting to remove
    a key software package that other packages depend upon
  - Binary packages can be "compiled once" and reused in testing, staging, production 
    environments
  - System tools (e.g., yum) can be used a common tool to interrogate the file system for
    integrity, ownership of specific files and other items.

This software relies on only one Rocks-created software package, but otherwise is completely compatible with Generic CentOS (And RedHat). 


**Simplified overview of approach**
The approach used here is one where programatic translations are used to progressively used to create a subdirectory structure that mirrors the way Rocks (an example of building qrencode -  https://github.com/rocksclusters/base/blob/master/src/qrencode) builds RPMS.  In that structure, an RPM spec file is automatically created and files are put in appropriate places in which rpmbuild (https://linux.die.net/man/8/rpmbuild) can successfully build a package.  The generated spec file must define a source in a %source as well as %build, %install, %file and other RPM-specific directives.  In particular, the %source is a tarball of the directory (e.g. the foundation-python directory). Prior to creating the tarball, upstream tarball (e.g. qrencode-3.4.0.tar.bz2) of the actual code is placed in this directory.  The generated spec file, calls the build target of the Makefile in this directory.  In this example the section looks like:
```
build:
	bunzip2 -c $(NAME)-$(VERSION).$(TARBALL_POSTFIX) | $(TAR) -xf -
	( 							\
		cd $(NAME)-$(VERSION);				\
		./configure --prefix=$(PKGROOT); 		\
		$(MAKE);					\
	)
```
This build target looks very similar to what you would do if your are building software without placing it into a package. And that is intentional.

In building literally hundreds of packages, the basic approach works quite well, but it comes that price of excessive code copying. The goal of the YAML-based generation of a package is to remove as much gratuitous "copy-and-paste" structure as possible.
