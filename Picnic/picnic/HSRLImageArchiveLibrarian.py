import dplkit.role.librarian
from datetime import datetime
import plistlib
import json

class HSRLImageArchiveLibrarian(dplkit.role.librarian.aLibrarian):
    def __init__(self, dataarchive_path=None, methodtype='site'):
        """ Initializer determines types of searches that this will be doing
            :param dataarchive_path: location of dataarchive.plist, default is /etc/dataarchive.plist
            :param methodtype: default basic method for finding data
                instrument - hsrl_python json method of only mapping the instrument name to a path
                dataset    - dataarchive mapping instrument name to a path (int or string)
                site       - dataarchive mapping a site id (by order in the plist) to time, location, and instrument set
        """

        super(HSRLImageArchiveLibrarian,self).__init__()
        self.dataarchive_path=dataarchive_path
        if methodtype not in ['instrument','dataset','site']:
            raise KeyError('invalid method type ' + methodtype)
        self.methodtype=methodtype
        if self.dataarchive_path==None:
            self.dataarchive_path="/etc/dataarchive.plist"
    def instrument(self,name):
        """instrument info
            instrument      - get info about individual instrument streams (always from dataarchive)
                metaframe takes shape of:
                    type
                    datasets
                    imagesets (prefix)
                    thumbsets
                        prefix
                        name
        """

        ins=plistlib.readPlist(self.dataarchive_path)['Instruments']
        k=ins.keys()
        kl=[x.lower() for x in k]
        nl=name.lower()
        return ins[k[kl.index(nl)]]

    def search(self, searchtype=None,searchbase=None,start=None,end=None,isactive=None,prefix=None,isthumb=None):
        """ This is the primary interface of the Librarian, exposing all personalities of the dataarchive list
            meta searchtype with searchbase=None (def):
               None        - use init default
               instrument  - using hsrl_python, list all matching instruments
               dataset     - using dataarchive, list all matching instruments
               site        - using dataarchive, list all matching sites info
                    site mode supports start/end, and isactive.
                        if start or end is specified, the site is only included if the windows intersect start/end. if only one is specified, its unbounded on the other end
                    if isactive is true, only sites with an open-ended window is included. if false, the inverse
                    metaframe takes shape of:
                        Name - long name
                        Path - base directory of data
                        Instruments - list of instruments (can be used with "instrument" search)
                        SiteID - (site only) site index
            data searchtype with searchbase set:
                None          - use init default
                instrument    - name an instrument
                dataset       - name an instrument (string) or integer instrument index (int)
                datasetindex  - same as by_dataset
                site          - integer site index
                additional keys:
                    searchbase - key used in the searchtype
                    prefix     - image prefix
                    isthumb    - true if is a thumbnail search, false if not
                metaframe takes shape of:
                    imagename
                    imagepath
                    fullimagepath
                    starttime
                    endtime
        """
        if searchtype==None:#default init value
            searchtype=self.methodtype
        if searchbase==None:#want a list of disk catalogs
            if searchtype=='instrument':
                from hsrl.data_stream.open_config import open_config
                fd = open_config('hsrl_python.json')
                prefs = json.load(fd)
                prefs = prefs['data_dir']
                fd.close()
                ret=[]
                for k in prefs.keys():
                    ret.append({'Name':k,'Path':prefs[k],'Instruments':[k]})
                return ret
            if searchtype=='dataset':
                ret=[]
                dsets=plistlib.readPlist(self.dataarchive_path)['Datasets']
                for dset in dsets:
                    dset['Instruments']=[dset['Name']]
                    ret.append(dset)
                return ret
            if searchtype=='site':
                includeTimeCheck=(start!=None or end!=None)
                if start==None:
                    start=datetime(1990,1,1,0,0,0)
                if end==None:
                    end=datetime(2100,1,1,0,0,0)
                includeActiveCheck=(isactive!=None)
                ret=[]
                sites=plistlib.readPlist(self.dataarchive_path)['Sites']
                for siteidx in range(0,len(sites)):
                    site=sites[siteidx]
                    site['SiteID']=siteidx
                    if includeActiveCheck:
                        hadActive=False
                        for w in site['Windows']:
                            if 'End' not in w:
                                hadActive=True
                        if isactive!=hadActive:
                            continue
                    if includeTimeCheck:
                        hadIntersection=False
                        for w in site['Windows']:
                            if w['Start']<end and (('End' not in w) or w['End']>start):
                                hadIntersection=True
                        if not hadIntersection:
                            continue
                    ret.append(site)
                return ret



        #if searchtype=='by_instrument': #python json
        #    if not os.environ.has_key('HSRL_CONFIG'):
        #        raise RuntimeError, 'HSRL_CONFIG needs to direct to the folder containing hsrl_python.json'
        #   #parse json, get path of instrument's data
        #    fd=open(os.path.join(os.environ['HSRL_CONFIG'],'hsrl_python.json'));
        #    dict=json.load(fd)
        #    fd.close()
        #    self.basepath=dict['data_dir'][inst];
        #else:
        #    pl=plistlib.readPlist('/etc/dataarchive.plist')    
        #    if searchtype=='by_datasetname':#plist instrument name
        #        pass
        #    elif searchtype=='by_dataset':#plist instrument name, in order in plist
        #        pass
        #    elif searchtype=='by_site':#plist site, in order in plist
        #        pass


if __name__=='__main__':
    lib=HSRLImageArchiveLibrarian()
    for x in lib():
        print x
    for x in lib('instrument'):
        print x
    for x in lib('dataset'):
        print x
    for x in lib(isactive=False):
        print x
