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
```make
build:
	bunzip2 -c $(NAME)-$(VERSION).$(TARBALL_POSTFIX) | $(TAR) -xf -
	( 							\
		cd $(NAME)-$(VERSION);				\
		./configure --prefix=$(PKGROOT); 		\
		$(MAKE);					\
	)
```
This build target looks very similar to what you would do if your are building software without placing it into a package. And that is intentional.

In building literally hundreds of packages, the basic approach works quite well, but it comes that price of excessive code copying. The goal of the YAML-based generation of a package is to remove as much gratuitous "copy-and-paste" structure as possible.  While the above is very simple (and actually a quite common build motif), there are many variations on how something is built, what it is dependent upon, and the like.   In real use on, for example, academic computing clusters groupings of software have common dependencies.  A routine example is software that depends upon a newer version of gcc. The new version of gcc must be installed alongside the system version. The gcc-admin repository (https://github.com/RCIC-UCI-Public/gcc-admin) uses yaml2rpm to build an updated version of gcc, a module file, and some compatible libraries.  Those packages can then be installed and used to build other software.  

Yaml2rpm set out to solve part of the problem of building and packaging relatively complex software.  At its core, is creates packages in the RPM format, but without the pain of manually building  and maintaining spec files.  A developer who wants to build yaml2rpm-generated packages must still have some familiarity with RPM concepts and yum. 

## Quickstart

If you want to use prebuilt RPMS for testing on a standard CentOS machine, you can follow what is below. The following was
tested on the official CentOS 7 Amazon machine image.

If you want to build yaml2rpm RPMS and install them from source repo, see Building
### Prerequisites

1. Python 2 or 3. Required python modules: argparse, socket, datetime. There are 4 python modules that will be automatically
   built and installed during the "Building" step:
   
   - future: for compatibility of python 2/3 code
   - ruamel-yaml & ruamle-ycml-clib: used by the  main script gen-definitions.py
   - setuptools: for build python dependent packages.
   
1. If you are using a very stripped-down CentOS image (similar to the official CentOS 7 image in Amazon, you will 
   want to make certain you have the following packages and package groups installed
   ```bash
    yum groupinstall "Development Tools" "Console Internet Tools"
    yum install redhat-lsb wget zlib-devel environment-modules
    . /etc/profile.d/modules.sh
   ```

1. Install the development RPMS 

   Go to the [Development RPMS](https://github.com/RCIC-UCI-Public/development-RPMS#development-rpms) repository 
   for the latest pre-built RPMs and instructions. After following those instructions, you can build your first RPM from source.

### Building 
You may want to build the yaml2rpm rpms and install them from the source git repository.
Do the following in the top-level directory
You will need to set DISPLAY prior to doing this so that firefox can ask for your permission to read public data
```bash
./first-build.sh
```

After this step is complete the followign RPMs are built and installed:

- python-future
- python-setuptools
- python-ruamel-yaml 
- python-ruamel-yaml-clib 
- rcic-module-support 
- rcic-module-path
- yaml2rpm

The **python-** RPMs provide 4 needed python modules for your default  system python install.
The **rcic-module-support**, **rcic-module-path**, and **yaml2rpm** provide all the building structure and support files for
the packages builds. They include a couple of profiles files that are added to the **/etc/profile.d**.
In order to proceed with next steps simply execute them (for future logins they will be automatically sourced by the login shell):
```bash
. /etc/profile.d/rcic-modules.sh 
. /etc/profile.d/yaml2rpm.sh
```

# A simple test build
For a very simple build of an RPM, create a working directory (`workdir`) in this simple example. And then
download the source tarball into the workdir/sources directory.  Then create the cmake RPM, it will be placed in 
workdir/RPMS/x86_64
```bash
mkdir -p workdir/yamlspecs
cd workdir/yamlspecs; cp /opt/rocks/yaml2rpm/samples/* .
make download PKG=cmake
make download PKG=scons
make 
```
At the end of the process, you should have 4 RPMs in workdir/RPMS/x86_64/.  You could install them on the local machine
and have an updated version of cmake and scons, and corresponding environment modules. For example. the module for cmake 
can be loaded in order to use cmake:
```bash
module load cmake
which cmake
```

The version of cmake is defined in the versions.yaml file, if you wanted to update the version, you could edit that file, 
download the new source tarball directly from the source website and then rebuild a new package via
```bash
make download PKG=cmake
make cmake.pkg
make cmake-module.pkg
```

# A Deeper Example
GCC (the GNU compiler collection) is relatively complex build.  It is often useful to have an updated version of gcc on your system without destroying the system-supplied gcc.  The GCC build has to be done in a certain way, packages need to be named to be non-conflicting and other items.   If you have completed the Quickstart above you can build an updated version of gcc and a set a packages. **WARNING! This process will install RPMS as it builds. You should do this on a 'disposable' build system. It takes hours to compile a gcc.**

Here is the full process for building gcc using the gcc-admix repo
```bash
git clone https://github.com/RCIC-UCI-Public/gcc-admix.git
cd gcc-admix
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

# The YAML Definition file
The basic notion of the defintion file to record on the bare minimum needed to define a package. Since it is usual for groupings of packages to share some common definitions, the generator supports a "defaults" file.  Here is a very simple yaml file taken from the samples directory of the `yaml2rpm` package.
```yaml
 package: iperf version 3 network tester
  name: iperf
  version: "3.6"
  extension: tar.gz
  description: >
    iperf3 version {{ version }}. iperf is a tool for active measurements of the maximum achievable
    bandwidth on IP networks.  It supports tuning of various parameters
    related to timing, protocols, and buffers.  For each test it reports
    the measured throughput / bitrate, loss, and other parameters.
  vendor_source: https://downloads.es.net/pub/iperf/iperf-{{ version }}.tar.gz
  root: "{{ pkg_defaults.app_path }}/{{ name }}/{{ version }}"
  build:
    modules:
    target:
  install:
    installextra: $(INSTALL) -m 644  README* LICENSE $(ROOT){{ root }}
```
YAML is essentially key-value storage and indentation indicates "dotted" values. Yaml2rpm interprets {{ *variable* }} as a reference.  In this particular example 
```yaml
description: Iperf3 version {{ version }}
``` 
will be expanded to 
```yaml
description: Iperf3 version 3.6
```
Iperf is very well-behaved software source using the standard pattern of compilation/installation:
```bash
./configure
make
make install
```
The default configure invoked by yaml2rpm in this case would be 
```yaml
./configure --prefix={{ root }}
```  
This can be easily overridden for other software packaging patterns.

## pkg-defaults.yaml
It is useful to have defaults that can be shared by several packages.  In the samples/ directory the following `pkg-defaults.yaml` file is given:
```yaml
pkg_defaults:
  app_path: /data/apps
  foundation: /opt/software
  python_base: /usr/lib64/python2.7/
  python_pkgs: "{{ pkg_defaults.python_base }}/site-packages"
  module:
    path: /usr/share/Modules/modulefiles
    prepend_path:
      - PATH {{ root }}/bin
      - LD_LIBRARY_PATH {{ root }}/lib
      - MANPATH {{ root }}/share/man
      - PKG_CONFIG_PATH  {{ root }}/lib/pkgconfig
    logger:  exec /bin/logger -p local6.notice - t module-hpc $env(USER) {{ name }}/{{ version }}
```
This is for common definition, but nothing is referenced unless the package yaml file utilizes it. For example,
the `iperf.yaml` references: 
```yaml
root: "{{ pkg_defaults.app_path }}/{{ name }}/{{ version }}"
```
which will get fully resolved to
```yaml
root: /data/apps/iperf/3.6
```   
In yaml, the key `pkg_defaults.module.prepend_path` is a list.  Notice that its definition, `{{ root }}` is taken from definition in the package yaml file  `iperf.yaml`.  This is by design.  Indeed you should think of the variable universe as
coming from the files pair `package.yaml, pkg-defaults.yaml`. If you want the `pkg-defaults`-defined variable, you must prefix it (see python_pkgs above for an example).

## Using gen-defintions.py to query
	
The definitions parser `gen-defintions.py` allows you to query the resolved version of a variable - but only those keys defined in the `package.yaml` file and including keys that reference variables in the `pkg-defaults.yaml` file.  The syntax is:
```bash
gen-defintions.py  --query=varName packageName.yaml
```

To download, from the vendor source website the iperf tarball you could use
```bash
wget $(/opt/rocks/yaml2rpm/gen-definitions.py --query=vendor_source iperf.yaml)
```
query mode is used in creating the directory structure and copying files. It is also very helpful for the packager to debug resolved definitions. 






