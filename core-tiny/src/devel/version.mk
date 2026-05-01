NAME = rocks-devel
RELEASE = 19
RPM.FILES="/etc/profile.d/*\\n/opt/rocks/share/devel/*"
RPM.EXTRAS="%define _use_internal_dependency_generator 0\\n%define __find_requires %{_builddir}/%{name}-%{version}/filter-requires.sh\\n%global source_date_epoch_from_changelog 0"
RPM.REQUIRES="createrepo redhat-lsb"
