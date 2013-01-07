import dplkit.role.librarian
from datetime import datetime,timedelta
import plistlib
import json
import os
import re

def modTime(filepath):
    return os.stat(filepath).st_mtime

class HSRLImageArchiveSearchResultIterator:
    def _getpathfordate(self,date):
        return os.path.join(self.path,'%i' % date.year, '%02i' % date.month, '%02i' % date.day, 'images')


    def __init__(self,host):
        self.host=host
        self.path=host.base['Path']
        self.time=host.start
        self.prefix=0

    def __repr__(self):
        return "HSRLImageArchiveSearchResultIterator(%s)[%s]" % (self.host,self.time)

    def next(self):
        if self.time==None or (self.host.end!=None and self.host.end<=self.time):
            raise StopIteration
        ret={'time':self.time,'filename':None,'hasHighres':False,'ampm':('am' if self.time.hour<12 else 'pm')}
        ret.update(self.host.prefix[self.prefix])
        d=self._getpathfordate(self.time)
        if os.access(d,os.R_OK):
            fnpatt=self.host.prefix[self.prefix]['prefix'] + self.host.middlematch + '_' + ret['ampm']
            newestfile=None
            newesttime=None
            for suff in self.host.suffix:
                patt=fnpatt+suff
                po=re.compile('^'+patt+'$')
                for f in os.listdir(d):
                    m=po.match(f)
                    #print f
                    #print m
                    if m!=None:
                        mt= modTime(os.path.join(d,f))
                        if newesttime==None or newesttime>mt:
                            newestfile=f
                            newesttime=mt
                if newestfile!=None:
                    #print "found " , newestfile
                    ret['filename']=newestfile
                    ret['hasHighres']=True
                    break
            if ret['filename']==None:
                for suff in self.host.suffix:
                    if ret['filename']!=None:
                        break
                    patt='missing_'+ ret['ampm'] + suff
                    po=re.compile('^'+patt+"$")
                    for f in os.listdir(d):
                        m=po.match(f)
                        #print f
                        #print m
                        if m!=None:
                            ret['filename']=f
                            break

        self.prefix=self.prefix+1
        if self.prefix>=len(self.host.prefix):
            self.prefix=0
            self.time=self.host.nextTime(self.time)
        return ret


class HSRLImageArchiveSearchResult:
    def _nextTime(self,tm):
        return tm+timedelta(days=.5)

    def floorTime(self,tm):
        return datetime(tm.year,tm.month,tm.day,0 if tm.hour<12 else 12,0,0)

    def ceilTime(self,tm):
        flr=self.floorTime(tm)
        if flr==tm:
            return tm
        return self._nextTime(flr)

    def nextTime(self,tm):
        r=self._nextTime(tm)
        if 'Windows' in self.base:
            r=self.lib.validLaterTime(r,self.base['Windows'])
        return r

    def __init__(self,host,base,start,end,prefix,isthumb):
        self.lib=host
        self.base=base
        self.start=self.floorTime(start)
        if end==None:
            self.end=self.nextTime(self.start)
        else:
            self.end=self.ceilTime(end)
        if prefix==None or prefix.__class__==list:
            prefixes=prefix
        else:
            prefixes=[prefix]
        self.isthumb=isthumb
        self.middlematch='_[0-9]{8}T[0-9]{4}_[0-9]{4}_[0-9]{2}'
        if self.isthumb:
            self.prefix=[]
            for inst in self.base['Instruments']:
                for pref in self.lib.instrument(inst)['thumbsets']:
                    if prefixes==None or pref['prefix'] in prefixes:
                        self.prefix.append({'prefix':pref['prefix'],'instrument':inst,'name':pref['name']})
            self.suffix=["_thumb.png","_thumb.jpg"]
        else:
            self.prefix=[]
            for inst in self.base['Instruments']:
                for pref in self.lib.instrument(inst)['imagesets']:
                    if prefixes==None or pref in prefixes:
                        self.prefix.append({'prefix':pref,'instrument':inst,'name':pref})
            self.suffix=[".png",".jpg"]

    def __repr__(self):
        secondstep=self.nextTime(self.start)
        if secondstep>=self.end:
            rangestr="%s" % (self.start)
        else:
            rangestr="%s-%s" % (self.start,self.end)
        return 'HSRLImageArchiveSearchResult(%s,%s,%s,%s,%s)' % (self.lib,self.base['Path'],self.prefix,rangestr,self.suffix)

    def _getpathfordate(self,date):
        return os.path.join(self.base['Path'],'%i' % date.year, '%02i' % date.month, '%02i' % date.day, 'images')

    def __iter__(self):
        time=self.start
        prefix=0
        #return HSRLImageArchiveSearchResultIterator(self)
        while not (time==None or (self.end!=None and self.end<=time)):
            ret={'time':time,'filename':None,'hasHighres':False,'ampm':('am' if time.hour<12 else 'pm')}
            ret.update(self.prefix[prefix])
            d=self._getpathfordate(time)
            if os.access(d,os.R_OK):
                fnpatt=self.prefix[prefix]['prefix'] + self.middlematch + '_' + ret['ampm']
                newestfile=None
                newesttime=None
                for suff in self.suffix:
                    patt=fnpatt+suff
                    po=re.compile('^'+patt+'$')
                    for f in os.listdir(d):
                        m=po.match(f)
                        #print f
                        #print m
                        if m!=None:
                            mt= modTime(os.path.join(d,f))
                            if newesttime==None or newesttime>mt:
                                newestfile=f
                                newesttime=mt
                    if newestfile!=None:
                        #print "found " , newestfile
                        ret['filename']=newestfile
                        ret['hasHighres']=True
                        break
                if ret['filename']==None:
                    for suff in self.suffix:
                        if ret['filename']!=None:
                            break
                        patt='missing_'+ ret['ampm'] + suff
                        po=re.compile('^'+patt+"$")
                        for f in os.listdir(d):
                            m=po.match(f)
                            #print f
                            #print m
                            if m!=None:
                                ret['filename']=f
                                break

            prefix=prefix+1
            if prefix>=len(self.prefix):
                prefix=0
                time=self.nextTime(time)
            yield ret



class HSRLImageArchiveLibrarian(dplkit.role.librarian.aLibrarian):
    def timeintersection(self,startt,endt,windows=None):
        if windows==None:
            windows=self.defaultwindows
        ret=[]
        if startt>endt:
            return ret
        if windows==None or len(windows)==0:
            tmp={'Start':startt,'End':endt}
            ret.append(tmp)
            return ret
        for i in windows:
            if i['Start']>=endt or ('End' in i and i['End']<=startt):
                continue
            tmp={'Start':startt,'End':endt}
            if startt<i['Start']:
                tmp['Start']=i['Start']
            if 'End' in i and endt>i['End']:
                tmp['End']=i['End']
            ret.append(tmp)
        return ret

    def validPriorTime(self,t,windows=None):
        if windows==None:
            windows=self.defaultwindows
        #print 'valid prior to ' , t , ' in windows ' , windows
        tmp=self.timeintersection(datetime(1990,1,1,0,0,0),t,windows)
        #print 'result = ' , tmp
        if len(tmp)==0:
            return None
        r=tmp[-1]['End']-timedelta(seconds=1)
        if r>datetime.utcnow():
            return datetime.utcnow()
        return r

    def validLaterTime(self,t,windows=None):
        if windows==None:
            windows=self.defaultwindows
        #print 'valid later than ' , t , ' in windows ' , windows
        tmp=self.timeintersection(t,datetime.utcnow(),windows)
        #print 'result = ' , tmp
        if len(tmp)==0:
            return None
        return tmp[0]['Start']

    def validClosestTime(self,t,windows=None):
        if windows==None:
            windows=self.defaultwindows
        p=self.validPriorTime(t,windows)
        n=self.validLaterTime(t,windows)
        if p==None:
            return n
        if n==None or (t-p)<=(n-t):
            return p
        return n
 
    def dontusevaliddate(yearno,monthno,dayno=1,hourno=0,minuteno=0):
        if hourno.__class__==str:
            hourno=0 if hourno=='am' else 12
        while minuteno>=60:
            minuteno-=60
            hourno+=1
        while minuteno<0:
            minuteno+=60
            hourno-=1
        while hourno>=24:
            hourno-=24
            dayno+=1
        while hourno<0:
            hourno+=24
            dayno-=1
        while monthno>12:
            monthno-=12
            yearno+=1
        while monthno<=0:
            monthno+=12
            yearno-=1
        (dummy,daysinmonth)=calendar.monthrange(yearno,monthno)
        while dayno>daysinmonth:
            dayno-=daysinmonth
            monthno+=1
            if monthno>12:
                monthno-=12
                yearno+=1
            (dummy,daysinmonth)=calendar.monthrange(yearno,monthno)
        while dayno<=0:
            monthno-=1
            if monthno<=0:
                monthno+=12
                yearno-=1
            (dummy,daysinmonth)=calendar.monthrange(yearno,monthno)
            dayno+=daysinmonth
        return datetime(yearno,monthno,dayno,hourno,minuteno,0)   

    def archive(self):
        mt=modTime(self.dataarchive_path)
        if mt!=self._archivemodtime:
            self._archive=plistlib.readPlist(self.dataarchive_path)
            self._archivemodtime=mt
        return self._archive

    def __init__(self, defaultsearchtype='site', defaultsearchbase=None, dataarchive_path=None,site=None,instrument=None,dataset=None,indexdefault=None):
        """ Initializer determines types of searches that this will be doing
            :param dataarchive_path: location of dataarchive.plist, default is /etc/dataarchive.plist
            :param defaultsearchtype: default searchtype for finding data
                instrument - hsrl_python json method of only mapping the instrument name to a path
                dataset    - dataarchive mapping instrument name to a path (int or string)
                site       - dataarchive mapping a site id (by order in the plist) to time, location, and instrument set
        """

        super(HSRLImageArchiveLibrarian,self).__init__()
        self.dataarchive_path=dataarchive_path
        self.defaultsearchtype=defaultsearchtype
        self.defaultsearchbase=defaultsearchbase
        if site!=None:
            self.defaultsearchtype='site'
            self.defaultsearchbase=site
        if instrument!=None:
            self.defaultsearchtype='instrument'
            self.defaultsearchbase=instrument
        if dataset!=None:
            self.defaultsearchtype="dataset"
            self.defaultsearchbase=dataset
        if indexdefault!=None:
            self.defaultsearchtype=indexdefault
            self.defaultsearchbase=None

        if self.defaultsearchtype!=None and self.defaultsearchtype not in ['instrument','dataset','site']:
            raise KeyError('invalid method type ' + self.defaultsearchtype)
        if self.dataarchive_path==None:
            self.dataarchive_path="/etc/dataarchive.plist"
        self._archive=None
        self._archivemodtime=None
        self.archive()
        self.defaultwindows=None
        self.defaultsite=self()
        try:
            if 'Windows' in self.defaultsite:
                self.defaultwindows=self.defualtsite['Windows']
        except AttributeError:
            pass
 
    def __repr__(self):
        if self.defaultsearchbase:
            desc='%s,%s' % (self.defaultsearchtype,self.defaultsearchbase)
        else:
            desc='%s' % (self.defaultsearchtype)
        return 'HSRLImageArchiveLibrarian(%s)' % (desc)

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

        ins=self.archive()['Instruments']
        k=ins.keys()
        kl=[x.lower() for x in k]
        nl=name.lower()
        return ins[k[kl.index(nl)]]

    def widesearch(self,searchtype,searchbase,start,end,isactive,reverseOrder):
            if searchtype=='instrument':
                from hsrl.data_stream.open_config import open_config
                fd = open_config('hsrl_python.json')
                prefs = json.load(fd)['data_dir']
                fd.close()
                for k in prefs.keys():
                    inst={'Name':k,'Path':prefs[k],'Instruments':[k]}
                    if searchbase!=None:
                        if searchbase.lower()==k.lower():
                            yield inst
                            return
                    else:
                        yield inst
                return
            if searchtype=='dataset':
                dsets=self.archive()['Datasets']
                if reverseOrder:
                    order=range(len(dsets)-1,-1,-1)
                else:
                    order=range(len(dsets))
                for dsetidx in order:
                    dset=dsets[dsetidx]
                    dset['DatasetID']=dsetidx
                    dset['Instruments']=[dset['Name']]
                    if searchbase!=None:
                        try:
                            dsi=int(searchbase)
                            if dsetidx==dsi:
                                yield dset
                                return
                        except:
                            if searchbase.lower()==dset['Name'].lower():
                                yield dset
                                return
                    else:
                        yield dset
                return
            if searchtype=='site':
                includeTimeCheck=(start!=None or end!=None)
                if start==None:
                    start=datetime(1990,1,1,0,0,0)
                if end==None:
                    end=datetime(2100,1,1,0,0,0)
                includeActiveCheck=(isactive!=None)
                searchsite=None
                if searchbase!=None:
                    try:
                        searchsite=int(searchbase)
                    except:
                        raise RuntimeError("%s parameter %s not found" %(searchtype,searchbase))
                sites=self.archive()['Sites']
                if reverseOrder:
                    order=range(len(sites)-1,-1,-1)
                else:
                    order=range(len(sites))
                for siteidx in order:
                    site=sites[siteidx]
                    site['SiteID']=siteidx
                    if includeActiveCheck:
                        hadActive=False
                        for w in site['Windows']:
                            if 'End' not in w:
                                hadActive=True
                        if isactive!=hadActive:
                            if searchbase!=None and siteidx==searchsite:
                                yield None
                                return
                            continue
                    if includeTimeCheck:
                        w=self._timeintersection(start,end,site['Windows'])
                        if len(w)==0:
                            if searchbase!=None and siteidx==searchsite:
                                yield None
                                return
                            continue
                        site['Windows']=w
                    if searchbase!=None:
                        if siteidx==searchsite:
                            yield site
                            return
                    else:
                        yield site
                return
            raise RuntimeError("%s is an unknown search type" %(searchtype))

    def search(self, searchtype=None,searchbase=None,start=None,end=None,isactive=None,prefix=None,isthumb=None,site=None,instrument=None,dataset=None,index=None,reverseOrder=False):
        """ This is the primary interface of the Librarian, exposing all personalities of the dataarchive list
            meta searchtype with searchbase=None and defaultsearchbase=None (def): #FIXME these will probably change to actual instrument/dataset/site parameters. This will be specifying one of those 3 to a new parameter "index"
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
                        DatasetID - (dataset only)
            data searchtype with searchbase set: # fixme with index unset, one of these must be set
                None          - use init default
                instrument    - name an instrument
                dataset       - name an instrument (string) or integer instrument index (int)
                site          - integer site index
                additional keys:
                    searchbase - key used in the searchtype.
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
            searchtype=self.defaultsearchtype
        if searchbase==None:#default init value
            searchbase=self.defaultsearchbase
        if site!=None:
            searchtype='site'
            searchbase=site
        if instrument!=None:
            searchtype='instrument'
            searchbase=instrument
        if dataset!=None:
            searchtype="dataset"
            searchbase=dataset
        if index!=None:
            searchtype=index
            searchbase=None
        if prefix==None and isthumb==None:#want a list of disk catalogs, or a specified catalog (not an imagesearch)
            ret=self.widesearch(searchtype,searchbase,start,end,isactive,reverseOrder)
            if searchbase==None:
                return ret
            for x in ret:
                return x
        return HSRLImageArchiveSearchResult(host=self,base=self.search(searchtype,searchbase),start=start,end=end,prefix=prefix,isthumb=isthumb)


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
    print lib('site',15)
    m=lib('site',16,start=datetime(2012,12,1,3,0,0),end=datetime(2012,12,3,12,0,0),prefix='bscat',isthumb=True)
    m=lib('site',1,start=datetime(2004,11,1,0,0,0),end=datetime(2004,12,1,0,0,0),prefix='bscat',isthumb=True)
    print lib('site',1)
    print m
    for x in m:
        print x
    p=[thumb['prefix'] for thumblist in [[dict({'Instrument':instrument}.items()+x.items()) for x in lib.instrument(instrument)['thumbsets']] for instrument in lib('site',2)['Instruments']] for thumb in thumblist]
    print p
    #print [t['prefix'] for t in p] #[lib.instrument(i)['thumbsets'] for i in lib()['Instruments']]]
    selectedtype='depol'
    #print ''.join([('' if thumb['prefix']!=b else thumb['instrument'] + ' ' + thumb['name'] ) for thumblist in [ [dict({'instrument':instrument}.items()+x.items()) for x in lib.instrument(instrument)['thumbsets']] for instrument in lib('site',2)['Instruments']] for thumb in thumblist])
    print 'Multi-View' if selectedtype==None else ''.join([''.join([('' if thumb['prefix']!=selectedtype else (thumb['instrument'] + ' ' + thumb['name']) ) for thumblist in [ [dict({'instrument':instrument}.items()+x.items()) for x in lib.instrument(instrument)['thumbsets']] for instrument in lib('site',2)['Instruments']] for thumb in thumblist]),' Full Month View'])
