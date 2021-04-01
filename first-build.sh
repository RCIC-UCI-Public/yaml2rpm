#!/bin/bash
# This first-build script is here to bootstrap a vanilla OS install to be able to
# build RPMS using yaml2rpm
# Steps
#   1. clone the repository that holds the rocks-devel source (rockscluster github)
#   2. build and install rocks-devel RPM
#   3. build and install the yaml2rpm RPMS
#
# After completion, open a new bash shell or logout/in to get profiles sourced

DEVELREPO=core
ROCKSGIT=https://github.com/rocksclusters/core.git
DEVEL_BUILD_SCRIPT=build-devel-rpm.sh

## Clone, Build, and Install rocks-devel rpm
git clone $ROCKSGIT
pushd $DEVELREPO
./$DEVEL_BUILD_SCRIPT
popd

## Make sure environment-modules are installed
yum -y install environment-modules

## Get source tarballs
make download

## Build and Install
# use bash -l to ensure that any profile.d entries are sourced
bash -l -c make
bash -l -c "make YES=-y install"
## 
echo "=== First Build completed ==="
echo "Start a new bash shell or logout/login to make certain all profile.d scripts"
