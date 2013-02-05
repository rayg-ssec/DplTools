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


External Files needed (see examples in resources): 
/etc/dataarchive.plist to configure the data sites, storage locations, and available datasets. location can be overridden using environment HSRL_DATA_ARCHIVE_CONFIG
operational hsrl_python code in the PYTHONPATH, including HSRL_CONFIG environment variable.
