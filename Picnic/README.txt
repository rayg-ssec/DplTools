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

Thumbnail tips:
example crontab:
============
HSRL_CONFIG=/home/jpgarcia/DEPLOYED/hsrl_python.git/hsrl_config
PYTHONPATH=/home/jpgarcia/DEPLOYED/DplTools.git/DplKit/python:/home/jpgarcia/DEPLOYED/hsrl_python.git:$PYTHONPATH
TIMESHIFT=-3600
2 * * * * /home/jpgarcia/DEPLOYED/hsrl_python.git/hsrl/dpl_experimental/makearchiveimages.py ahsrl_20km gvhsrl mf2hsrl nshsrl bagohsrl ahsrl_singapore gvhsrl_gvhsrl mf2hsrl_amf2hsrl nshsrl_yeu bagohsrl_msn
============
makearchiveimages.py is a commandline tool for creating thumbnails.
parameters are instrument names from the hsrl_python configuration json, and optionally dates (now if left off).  Processing logs are kept in files named ./[instrument]_[YYYY.MM.DD.HH].log
examples:
 'gvhsrl 2013.05.05.12' will make a PM thumbnail for 2013.05.05, placing the images in the images folder for that date in the data folder
 'ahsrl 2013.03.05.12 2013.05.05.00' make 2 thumbnails for ahsrl for the specified time windows
 'ahsrl 2013.03.05.12 .. 2013.05.05.00' make Many thumbnails for ahsrl for the specified time range
 'bagohsrl 2013.03.05.12 .. gvhsrl' make Many thumbnails for bagohsrl from the specified time to now, and make a current thumbnail for the gvhsrl

additional 'suffix' parameters (HACKY)
_##km = max altitude of ## km
_xxxxxx = make an image of the last 24hours (not day-aligned), and move it to os.getenv('DAYSTORE')/xxxxxx_current.png
Environment parameters:
DAYSTORE = where to store 24hour images
TIMESHIFT = seconds to shift 'now'. used with crontab so '12:01' doesn't trigger a near-empty image of the next 12 hours, but a complete image of the last 12 hours.
FORCE_FOREGROUND = if set to a non-empty string, will cause processes to run in the foreground one at a time, and not make a .log file.

FIXME trimming whitespace borders from images currently uses ImageMagick's 'mogrify' command... this should be fixed to use PIL standard functions




External Files and Environment Variables needed (see examples in resources): 
HSRL_DATA_ARCHIVE_CONFIG=/etc/dataarchive.plist to configure the data sites, storage locations, and available datasets. location can be overridden using environment HSRL_DATA_ARCHIVE_CONFIG
PYTHONPATH should point to Picnic and an operational version of hsrl_python code
HSRL_CONFIG for the hsrl_python code
FTPPATH must point to a writable location on disk to store multiple output requests. actual content will be stored as $(FTPPATH)/username/sessionid/* and $(FTPPATH)/username/filename_with_sessionid.tar.bz2
FTPURL must point to the same location as FTPPATH, but as a completely parallel URL for listing and retrieval of its content by remote
SESSIONFOLDER location for each session's working directory to be stored.  default is './sessions'
SERVERSIDE_ARCHIVEPATH location for server-side storage of user configurations (display and processing), selectable from a widget, and listed in a cookie. file are stored in this folder, capped at 64k in size, named by a token and a 12-character sha1 hash (example: PROC_0123456789ab), and also cataloged in a json file to retain order, and have a human-readable name. default is './serverarchive'. users can select which of these are presented to them in the web interface. hash collisions prevent a new file from being written or modified.
