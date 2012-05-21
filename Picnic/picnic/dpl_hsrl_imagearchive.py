#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import math
#import pytz
import os
import re
import json
import plistlib

class simpleobject(object):
    pass

def validPriorTime(method,instrument,atime):
    tmp=dpl_hsrl_imagearchive(method,instrument,None,None,datetime.datetime(1990,1,1,0,0,0),atime)
    if tmp.timewindows and len(tmp.timewindows)>0:
        tmpt=tmp.timewindows[len(tmp.timewindows)-1].End
        tmpt-=datetime.timedelta(0,1)
        return tmpt
    return None

def validLaterTime(method,instrument,atime):
    tmp=dpl_hsrl_imagearchive(method,instrument,None,None,atime,datetime.datetime.utcnow())
    if tmp.timewindows and len(tmp.timewindows)>0:
        return tmp.timewindows[0].Start
    return None

def validClosestTime(method,instrument,atime):
    p=validPriorTime(method,instrument,atime)
    n=validLaterTime(method,instrument,atime)
    if p==None:
        return n
    if n==None or (atime-p)<=(n-atime):
        return p
    return n

class dpl_hsrl_imagearchive(object):
    def _findThumbPrefixes(self,insts,instrumentlist):
        ret={}
        for i in instrumentlist:
            if i in insts:
                for j in insts[i].thumbsets:
                    ret[j.name]=j.prefix
        return ret

    def _findImagePrefixes(self,insts,instrumentlist):
        ret=[]
        for i in instrumentlist:
            if i in insts:
                for j in insts[i].imagesets:
                    ret.append(j)
        return ret
        
    def _suffixfortime(self,timed):
        tmpst='.jpg'
        if self.thumb:
            tmpst='_thumb'+tmpst;
        if timed.timetuple().tm_hour<12:
            return '_am'+tmpst
        return '_pm'+tmpst

    def _getpathfor_json(self,inst):
        if not os.environ.has_key('HSRL_CONFIG'):
            raise RuntimeError, 'HSRL_CONFIG needs to direct to the folder containing hsrl_python.json'
        #parse json, get path of instrument's data
        fd=open(os.path.join(os.environ['HSRL_CONFIG'],'hsrl_python.json'));
        dict=json.load(fd)
        fd.close()
        path=dict['data_dir'][inst];
        return path

    def _getpathfor_systemplist_site(self,sitenumber,prefix=None,is_thumb=False):
        pl=plistlib.readPlist('/etc/dataarchive.plist')
        dirs=pl.Sites
        insts=pl.Instruments
        try:
            dataarchive=dirs[sitenumber]
        except:
            raise KeyError('invalid site number %i' % sitenumber)
        self.SiteName=dataarchive.Name
        self.availableThumbPrefixes=self._findThumbPrefixes(insts,dataarchive.Instruments)
        self.availableImagePrefixes=self._findImagePrefixes(insts,dataarchive.Instruments)
        if prefix!=None:
            for i in dataarchive.Instruments:
                if i in insts:
                    if is_thumb:
                        for thumbd in insts[i].thumbsets:
                            if prefix==thumbd.prefix:
                                self.ImageName=thumbd.name
                    else:
                        for imaged in insts[i].imagesets:
                            if prefix==imaged:
                                self.lowresform=insts[i].thumbsets[0].prefix
        return (dataarchive.Path,dataarchive.Windows)

    def _getpathfor_systemplist_dataset_idx(self,datasetidx,prefix=None,is_thumb=False):
        pl=plistlib.readPlist('/etc/dataarchive.plist')
        dirs=pl.Datasets
        insts=pl.Instruments
        try:
            dataarchive=dirs[sitenumber]
        except:
            raise KeyError('invalid dataset number %i' % datasetidx)
        #self.SiteName=dataarchive.Name
        if prefix!=None and dataarchive.Name in insts:
            if is_thumb:
                for thumbd in insts[dataarchive.Name].thumbsets:
                    if prefix==thumbd.prefix:
                        self.ImageName=thumbd.name
            else:
                self.lowresform=insts[dataarchive.Name].thumbsets[0].prefix
        self.availableThumbPrefixes=self._findThumbPrefixes(insts,list(dataarchive.Name))
        self.availableImagePrefixes=self._findImagePrefixes(insts,list(dataarchive.Name))
        return (dataarchive.Path,None)

    def _getpathfor_systemplist_dataset_name(self,instname,prefix=None,is_thumb=False):
        pl=plistlib.readPlist('/etc/dataarchive.plist')
        dirs=pl.Datasets
        insts=pl.Instruments
        dataarchive=None
        inst=instname.lower()
        for i in dirs:
            if i.Name.lower()==inst:
                dataarchive=i
        if dataarchive==None:
            raise KeyError('invalid dataset name %s' % instname)
        if prefix!=None and dataarchive.Name in insts:
            if is_thumb:
                for thumbd in insts[dataarchive.Name].thumbsets:
                    if prefix==thumbd.prefix:
                        self.ImageName=thumbd.name
            else:
                self.lowresform=insts[dataarchive.Name].thumbsets[0].prefix
        self.availableThumbPrefixes=self._findThumbPrefixes(insts,list(dataarchive.Name))
        self.availableImagePrefixes=self._findImagePrefixes(insts,list(dataarchive.Name))
        #self.SiteName=dataarchive.Name
        return (dataarchive.Path,None)

    def _getpathfordate(self,date):
        tup=date.timetuple()
        return os.path.join(self.basepath,'%i' % tup.tm_year, '%02i' % tup.tm_mon, '%02i' % tup.tm_mday, 'images')

    def _timeintersection(self,startt,endt,windows):
        ret=list()
        if windows==None or len(windows)==0:
            tmp=simpleobject()
            tmp.Start=startt;
            tmp.End=endt;
            ret.append(tmp)
            return ret
        for i in windows:
            #print 'window'
            #print i
            #print 'start'
            #print startt
            #print 'end'
            #print endt
            if i.Start>=endt or ('End' in i and i.End<=startt):
                continue
            tmp=simpleobject()
            tmp.Start=startt
            tmp.End=endt
            if startt<i.Start:
                tmp.Start=i.Start
            if 'End' in i and endt>i.End:
                tmp.End=i.End
            ret.append(tmp)
        return ret

    def _findnewestfile(self,path,reg):
        #print 'searching %s for %s\n' % (path, reg)
        try:
            fl = os.listdir(path)
        except:
            return None
        for f in fl:
            m =re.search(reg, f)
            if m:
                return f
        return None
        
    def __init__(self,method,instrument,prefix,is_thumb,start_time_datetime,end_time_datetime):
        #self.currenttime=pytz.UTC.localize(start_time_datetime)
        #self.endtime=pytz.UTC.localize(end_time_datetime)
        if method=='by_instrument':
            self.basepath=self._getpathfor_json(instrument)
            self.timewindows=None
        elif method=='by_datasetname':
            (self.basepath, self.timewindows)=self._getpathfor_systemplist_dataset_name(instrument,prefix,is_thumb)
        elif method=='by_dataset':
            (self.basepath, self.timewindows)=self._getpathfor_systemplist_dataset_idx(int(instrument),prefix,is_thumb)
        elif method=='by_site':
            (self.basepath, self.timewindows)=self._getpathfor_systemplist_site(int(instrument),prefix,is_thumb)
        else:
            raise KeyError('Invalid DPL image location method %s' % method)
        self.currenttime=start_time_datetime
        self.endtime=end_time_datetime
        self.timewindows=self._timeintersection(self.currenttime,self.endtime,self.timewindows)
        self.timewindowidx=0
        self.firstRun=True
        self.pref=prefix
        self.thumb=is_thumb
        self.deltime=datetime.timedelta(0,12*60*60,0)
        self.inst=instrument
        self.currentfilename=None

    def __iter__(self):
        return self

    def next(self):
        if self.firstRun:
            self.firstRun=False
        else:
            self.currenttime+=self.deltime;
        if self.timewindowidx>=len(self.timewindows):
            self.currentfilename=None
            raise StopIteration()
        if (self.timewindows[self.timewindowidx].End-self.currenttime)<datetime.timedelta(0,10,0):
            self.timewindowidx+=1
            if self.timewindowidx>=len(self.timewindows):
                self.currentfilename=None
                raise StopIteration()
            selfcurrenttime=self.timewindows[self.timewindowidx].Start

        fn=None

        matchstr='^%s_........T.*%s' % ( self.pref, self._suffixfortime( self.currenttime ) )
        pdate=self._getpathfordate(self.currenttime)

        fn=self._findnewestfile(pdate,matchstr)
        placeholder=False

        if fn==None:
            matchstr='^missing%s' % self._suffixfortime(self.currenttime)
            fn=self._findnewestfile(pdate,matchstr)
            #print 'looking for missing image on %i.%02i.%02iT%02i.%02i matching %s in %s. got %s.' % (self.currenttime.year,self.currenttime.month,self.currenttime.day, self.currenttime.hour ,self.currenttime.minute, matchstr, pdate, fn)
            placeholder=True

        if fn:
            self.currentfilename=os.path.join(pdate,fn);
            return (self.inst,self.currenttime,fn,placeholder,self.currentfilename)
        else:
            self.currentfilename=fn;
            return None

if __name__ == '__main__':
    dplhsrlimage=dpl_hsrl_imagearchive('by_instrument','bagohsrl','bscat',True,datetime.datetime(2012,5,10,0,0,0),datetime.datetime(2012,5,20,0,0,0))
    for i in dplhsrlimage:
        print i
    dplhsrlimage=dpl_hsrl_imagearchive('by_datasetname','bagohsrl','bscat',True,datetime.datetime(2012,5,10,0,0,0),datetime.datetime(2012,5,20,0,0,0))
    for i in dplhsrlimage:
        print i
    dplhsrlimage=dpl_hsrl_imagearchive('by_site','0','bscat_depol',False,datetime.datetime(2004,4,26,0,0,0),datetime.datetime(2004,5,20,0,0,0))
    if hasattr(dplhsrlimage,'SiteName'):
        print dplhsrlimage.SiteName
    #for i in dplhsrlimage:
        #print i
