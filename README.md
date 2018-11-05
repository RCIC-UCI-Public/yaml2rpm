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


