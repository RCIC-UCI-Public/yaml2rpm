# This file is included on all of the bootstrap-* subdirs 
# It definess Download location for bootstrapped sources. Should 
# be where all other yaml2rpm sources are located

SURL = https://s3.us-west-1.wasabisys.com/admix-sources

# Pkg install target for bootstrap-* packages
pkginstall:
        (cd $(REDHAT.RPMS)/..; make createlocalrepo; yum -c yum.conf -y install $(NAME))

