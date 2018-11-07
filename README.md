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


## Motivation
The approach used here is one where programmatic translations are used to progressively create a subdirectory structure that mirrors the way Rocks (an example of building a qrencode RPM -  https://github.com/rocksclusters/base/blob/master/src/qrencode) builds RPMS.  In that structure, an RPM spec file is automatically created and files are put in appropriate places in which rpmbuild (https://linux.die.net/man/8/rpmbuild) can successfully build a package.  The generated spec file must define a source in a %source as well as %build, %install, %file and other RPM-specific directives.  In particular, the %source is a tarball of this directory in github (e.g. the base/src/qrencode directory). However, prior to creating the tarball, the upstream tarball (e.g. qrencode-3.4.0.tar.bz2) must be placed in base/src/qrencode directory.  The automatically generated spec file, the `%build` directive invokes the `build` target of the Makefile provided here.   In this example the section looks like:
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

In building literally hundreds of packages, the basic approach works quite well, but it comes that price of excessive code copying. The goal of the YAML-based generation of a package is to remove as much gratuitous "copy-and-paste" structure as possible.  While the above is very simple (and actually a quite common build motif), there are many variations on how something is built, what it is dependent upon, and the like.   In real use on, for example, academic computing clusters groupings of software have common dependencies.  A routine example is software that depends upon a newer version of gcc. The new version of gcc must be installed alongside the system version. The gcc-pkgs repository (https://github.com/RCIC-UCI-Public/gcc-pkgs) uses yaml2rpm to build an updated version of gcc, a module file, and some compatible libraries.  Those packages can then be installed and used to build other software.  

Yaml2rpm set out to solve part of the problem of building and packaging relatively complex software.  At its core, is creates packages in the RPM format, but without the pain of manually building  and maintaining spec files.  A developer who wants to build yaml2rpm-generated packages must still have some familiarity with RPM concepts and yum. 

## Quickstart

If you want to use prebuilt RPMS for testing on a standard CentOS machine, you can follow what is below. The following was
tested on the official CentOS 7 Amazon machine image.

-Preparation-
If you are using a very stripped-down CentOS image (similar to the official CentOS 7 image in Amazon, you will want to make
certain you have the following packages and package groups installed
```
 yum groupinstall "Development Tools" "Console Internet Tools"
 yum install redhat-lsb wget zlib-devel environment-modules
 . /etc/profile.d/modules.sh
```

At this point, you can install the development RPMS and then build your first RPM from source.

```
wget https://github.com/RCIC-UCI-Public/development-RPMS/raw/master/rocks-devel-7.1-10.x86_64.rpm
wget https://github.com/RCIC-UCI-Public/development-RPMS/raw/master/yaml2rpm-1.0-1.x86_64.rpm
yum install rocks-devel-7.1-10.x86_64.rpm yaml2rpm-1.0-1.x86_64.rpm redhat-lsb environment-modules
. /etc/profile.d/rocks-devel.sh
```
For a very simple test build of an RPM, create a working directory (`workdir`) in this simple example. And then
download the source tarball into the workdir/sources directory.  Then create the cmake RPM, it will be placed in 
workdir/RPMS/x86_64
```
mkdir -p workdir/yamlspecs
mkdir -p workdir/sources
cd workdir/yamlspecs; cp /opt/rocks/yaml2rpm/samples/* .
NAME=cmake
WEBSRC=$(/opt/rocks/yaml2rpm/gen-definitions.py --query=vendor_source ${NAME}.yaml)
(cd ../sources; wget ${WEBSRC})
make ${NAME}.pkg
```
at the end of the process, you should have an RPM in workdir/RPMS/x86_64.  You could install it on the local machine
and have an updated version of cmake, with a environment so that you could load it with
```
module load cmake
which cmake
```

The version of cmake is defined in the cmake.yaml file, if you wanted to update the version, you could edit that file, download the new source tarball directly from the source website and then rebuild a new package.

# A Deeper Example
GCC (the GNU compiler collection) is relatively complex build.  It is often useful to have an updated version of gcc on your system without destroying the system-supplied gcc.  The GCC build has to be done in a certain way, packages need to be named to be non-conflicting and other items.   If you have completed the Quickstart above you can build an updated version of gcc and a set a packages. **WARNING! This process will install RPMS as it builds. You should do this on a 'disposable' build system. It takes hours to compile a gcc. **

Here is the full process for building gcc using the gcc-pkgs repo
```
git clone https://github.com/RCIC-UCI-Public/gcc-pkgs.git
cd gcc-pkgs
make download
cd yamlspecs
(make bootstrap &> /tmp/bootstrap-gcc.log; make &> /tmp/build-gcc.log) &
```
An optional last step would be to unbootstrap the system, which will remove any locally-built and installed RPMS that result from
the bootstrap process. 
```
make unbootstrap
```
At this point, you should have a compatible set of RPMS for gcc and some key supporting libraries. 



