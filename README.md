# yaml2rpm
Generic Methodology for building RPMs
See full documentation in https://yaml2rpm.readthedocs.io

This is a bootstrap admix that provides building blocks needed for all other admixes.
These building blocks include templates, Makefiles, profile files, and a few python
packages that provide yaml files processing.

The goal is to reduce the package-specific configuration/build essentials into a yaml
file that goes through some automated steps to create an RPM. The building blocks
provide all essentials to achieve this goal.

This software uses the underlying Rocks methodology for automatically creating RPM spec
files to create packages. This software relies on only one Rocks-created software package
(provided in this repo), but otherwise is completely compatible with Generic CentOS (and RedHat). 

## Quickstart
Yaml2rpm is best built directly from the git repository.
Part of that build process will create RPMs that can be installed 
on other machines. On a reasonable system with good network connectivity 
(or locally-mirrored repositories) it takes roughly 2 minutes to set up
a system to build RPMS using yaml2rpm.

### Prerequisites
For a quick start testing on a standard CentOS machine or a singularity container:

Python 3 and its *argparse*, *socket*, *datetime* modules (provided via OS RPMS).
If you are using a very stripped-down CentOS image (similar to the official CentOS 9
image in Amazon, you will want to make certain you have the following packages and package groups installed

```
yum groupinstall "Development Tools" "Console Internet Tools"
yum install redhat-lsb wget zlib-devel environment-modules
. /etc/profile.d/modules.sh
```

### Building 
Do the following in the top-level directory

```bash
./first-build.sh
```
After this step is complete the following RPMs are built and installed:

- python-ruamel-yaml 
- python-ruamel-yaml-clib 
- rcic-module-path
- rcic-module-support 
- rocks-devel
- yaml2rpm

The **python-** RPMs provide Python modules for our default system Python install.
The **rcic-module-support**, **rcic-module-path**, and **yaml2rpm** provide all the building structure and support files for
the packages builds. They include a couple of profiles files that are added to the **/etc/profile.d**.

In order to proceed with next steps simply execute them (for future logins they will be automatically sourced by the login shell):

```bash
. /etc/profile.d/rcic-modules.sh 
. /etc/profile.d/yaml2rpm.sh
```
