Picnic README

Purpose of Picnic:
Demonstration and testing ground of multiple DPL datasources as a web portal
Current version only consists of HSRL data access, but will be expanded into other instruments in an instrument-agnostic way

Requirements:
Fully operational Pyramid install (with waitress)
matplotlib
NetCDF4
dependencies from hsrl_python
bottleneck, matplotlib, numpy, scipy, NetCDF4, pycdf

All can be retrieved via pip or easy_install. Development environment is based off of ShellB3
https://groups.ssec.wisc.edu/employee-info/for-programmers/scriptonomicon/ShellB3/shellb3-overview


External Files and Environment Variables needed (see examples in resources): 
HSRL_DATA_ARCHIVE_CONFIG=/etc/dataarchive.plist to configure the data sites, storage locations, and available datasets. location can be overridden using environment HSRL_DATA_ARCHIVE_CONFIG
PYTHONPATH should point to Picnic and an operational version of hsrl_python code
HSRL_CONFIG for the hsrl_python code
FTPPATH must point to a writable location on disk to store multiple output requests. actual content will be stored as $(FTPPATH)/username/sessionid/* and $(FTPPATH)/username/filename_with_sessionid.tar.bz2
FTPURL must point to the same location as FTPPATH, but as a completely parallel URL for listing and retrieval of its content by remote
SESSIONFOLDER location for each session's working directory to be stored.  default is './sessions'
