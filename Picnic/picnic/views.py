from pyramid.view import view_config
from dpl_hsrl_imagearchive import *
from datetime import datetime,timedelta
from pyramid.httpexceptions import HTTPNotFound, HTTPTemporaryRedirect
from webob import Response
from hashlib import sha1 as hashfunc
import os
import sys
import calendar
import plistlib
import multiprocessing
from sets import Set

setsfile='picnic/resources/portal_requestsets.json'

def safejoin(*args):
    tmp=os.path.abspath(args[0])
    tmpargs=[tmp]
    if len(args)>1:
        tmpargs.extend(args[1:])
    ret=os.path.join(*tmpargs)
    if not ret.startswith(tmpargs[0]):
        print "path " + ret + " doesn't start with " + tmpargs[0]
        return None
    if not ret.endswith(tmpargs[-1]):
        print "path " + ret + " doesn't end with " + tmpargs[-1]
        return None
    if len(tmpargs)>2:
        for p in tmpargs[1:(len(tmpargs)-1)]:
            if os.path.sep+p+os.path.sep not in ret:
                print "path " + ret + " doesn't with " + p
                return None
    return ret
    

def formsetsForInstruments(instruments,subset):
    iset=Set(instruments)
    setlist=[]
    sets=json.load(file(setsfile))[subset]
    for aset in sets:
        if 'enabled' in aset and len(Set(aset['enabled']) & iset)==0:
            continue
        if 'required' in aset and len(Set(aset['required']) & iset)!=len(Set(aset['required'])):
            continue
        setlist.append(aset)

    return setlist

staticresources={}

tasks={}

def makeformbutton(label,cgiurl,bdate,edate):
    return {'submit':label,'url':cgiurl,
            'inputs':[
                {'name':'byr','value':'%i' % bdate.year},
                {'name':'bmo','value':'%i' % bdate.month},
                {'name':'bdy','value':'%i' % bdate.day},
                {'name':'bhr','value':'%i' % bdate.hour},
                {'name':'bmn','value':'%i' % bdate.minute},
                {'name':'eyr','value':'%i' % edate.year},
                {'name':'emo','value':'%i' % edate.month},
                {'name':'edy','value':'%i' % edate.day},
                {'name':'ehr','value':'%i' % edate.hour},
                {'name':'emn','value':'%i' % edate.minute}
                ]
            }

def validdate(yearno,monthno,dayno=1,hourno=0,minuteno=0):
    while minuteno>=60:
        minuteno-=60
        hourno+=1
    while minuteno<0:
        minuteno+=60
        hourno-=1
    while hourno>23:
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

def monthurlfor(req,atype,access,imtype,date):
    if imtype=='all':
        return req.route_path('multiview',accesstype=atype,access=access,year=date.year,month=date.month,day=date.day)
    return req.route_path('month',accesstype=atype,access=access,thumbtype=imtype,year=date.year,month=date.month)

@view_config(route_name='select_month')
def select_month(request):
    try:
        if not ('year' in request.params and 'month' in request.params):
            return HTTPTemporaryRedirect(location=request.route_path('thumb',
                                                                    accesstype=request.params.getone('accessby'),
                                                                    access=request.params.getone('accessto'),
                                                                    thumbtype=request.params.getone('type')))
        selected=validdate(int(request.params.getone('year')),int(request.params.getone('month')))
        return HTTPTemporaryRedirect(location=monthurlfor(request,
                                                          request.params.getone('accessby'),
                                                          request.params.getone('accessto'),
                                                          request.params.getone('type'),
                                                          selected))
    except:
        return HTTPTemporaryRedirect(location=request.route_path("home"))

@view_config(route_name='thumb')
def redirect_month(request):
    #try:
        methodtype=request.matchdict['accesstype']
        methodkey=request.matchdict['access']
        subtypekey=request.matchdict['thumbtype']
        nowtime=datetime.utcnow()
        if 'year' in request.matchdict:
            yearno=int(request.matchdict['year'])
        else:
            yearno=nowtime.year
        if 'month' in request.matchdict:
            monthno=int(request.matchdict['month'])
        else:
            monthno=nowtime.month
        if 'day' in request.matchdict:
            dayno=int(request.matchdict['month'])
        elif monthno==nowtime.month and yearno==nowtime.year and subtypekey=='all':
            dayno=nowtime.day-3
            if dayno<=0:
                monthno-=1
                if monthno<=0:
                    monthno+=12
                    yearno-=1
                (dummy,daysinmonth)=calendar.monthrange(yearno,monthno)
                dayno+=daysinmonth
        else:
            dayno=1
        besttime=validClosestTime(methodtype,methodkey,datetime(yearno,monthno,dayno,0,0,0))
        return HTTPTemporaryRedirect(location=monthurlfor(request,methodtype,methodkey,subtypekey,besttime))
    #except:
    #return HTTPTemporaryRedirect(location=request.route_path("home"))        

def dayurlfor(req,atype,access,date):
    if date.hour<12:
        hour='am'
    else:
        hour='pm'
    return req.route_path('date',accesstype=atype,access=access,
                         year=date.year,month=date.month,day=date.day,ampm=hour)

@view_config(route_name='select_day')
def select_day(request):
    try:
        if not ('year' in request.params and 'month' in request.params and 'day' in request.params and 'hour' in request.params):
            return HTTPTemporaryRedirect(location=request.route_path('today',
                                                                    accesstype=request.params.getone('accessby'),
                                                                    access=request.params.getone('accessto')))
        selected=validdate(int(request.params.getone('year')),int(request.params.getone('month')),int(request.params.getone('day')),int(request.params.getone('hour')))
        return HTTPTemporaryRedirect(location=monthurlfor(request,
                                                          request.params.getone('accessby'),
                                                          request.params.getone('accessto'),
                                                          selected))
    except:
        return HTTPTemporaryRedirect(location=request.route_path('home'))

@view_config(route_name='today')
def redirect_day(request):
    try:
        methodtype=request.matchdict['accesstype']
        methodkey=request.matchdict['access']
        nowtime=datetime.utcnow()
        if 'year' in request.matchdict:
            yearno=int(request.matchdict['year'])
        else:
            yearno=nowtime.year
        if 'month' in request.matchdict:
            monthno=int(request.matchdict['month'])
        else:
            monthno=nowtime.month
        if 'day' in request.matchdict:
            dayno=int(request.matchdict['day'])
        else:
            dayno=nowtime.day
        if 'ampm' in request.matchdict:
            ampm=request.matchdict['ampm']
            if ampm=='am':
                hourno=0
            else:
                hourno=12
        else:
            hourno=nowtime.hour
        besttime=validClosestTime(methodtype,methodkey,datetime(yearno,monthno,dayno,hourno,0,0))
        return HTTPTemporaryRedirect(location=dayurlfor(request,methodtype,methodkey,besttime))
    except:
        return HTTPTemporaryRedirect(location=request.route_path('home'))

imagepathcache={}
imagepathcacheage=None

def moddateoffile(f):
    return os.stat(f).st_mtime

@view_config(route_name='image_resource')
@view_config(route_name='session_resource')
def session_resource(request):
    fn=request.matchdict['filename']
    if 'session' in request.matchdict:
        f=safejoin('.','sessions',request.matchdict['session'],fn)
    elif 'accesstype' in request.matchdict:
        global imagepathcache
        global imagepathcacheage
        methodtype=request.matchdict['accesstype']
        methodkey=request.matchdict['access']
        yearno=int(request.matchdict['year'])
        monthno=int(request.matchdict['month'])
        dayno=int(request.matchdict['day'])
        #FIXME HACKY CACHY
        md=moddateoffile("/etc/dataarchive.plist")
        if imagepathcacheage==None or imagepathcacheage!=md:
            imagepathcacheage=md
            imagepathcache.clear()
        if methodtype not in imagepathcache or methodkey not in imagepathcache[methodtype]:
            if len(imagepathcache)==0:
                imagepathcacheage=moddateoffile("/etc/dataarchive.plist")
            tmpdp=dpl_hsrl_imagearchive(methodtype,methodkey,None,False,datetime(yearno,monthno,dayno,0,0,0),datetime(yearno,monthno,dayno,1,0,0))
            if methodtype not in imagepathcache:
                imagepathcache[methodtype]={}
            imagepathcache[methodtype][methodkey]=tmpdp.basepath
            
        f=safejoin(imagepathcache[methodtype][methodkey],'%04i' % yearno,'%02i' % monthno, '%02i' % dayno,'images',fn)
    else:
        return HTTPNotFound("File doesn't exist")
       
    m=None
    if not os.access(f,os.R_OK):
        return HTTPNotFound("File doesn't exist")
    if fn.endswith('.jpg'):
        m='image/jpeg'
    if fn.endswith('.png'):
        m='image/png'
    if fn=='logfile':
        m='text/plain'
    if fn.endswith('.json'):
        m='application/json'

    if m==None:
        return HTTPNotFound("File inaccessible")
    return Response(content_type=m,app_iter=file(f))

@view_config(route_name='resource_request')
def resource_request(request):
    #print request
    #print request.matchdict
    k=request.matchdict['statickey'];
    if k in staticresources:
        f=open(staticresources[k]['filename'])
        if f:
            mt=staticresources[k]['mimetype']
            return Response(content_type=mt,app_iter=f)
        staticresources.erase(k);
    return HTTPNotFound("File doesn't exist in request cache")

def staticurlfor(req,fname,fullfile):
    hashname=fname
    if hashname not in staticresources:
        b={}
        b['filename']=fullfile
        if fullfile.endswith('.jpg'):
            b['mimetype']='image/jpeg'
        if fullfile.endswith('.png'):
            b['mimetype']='image/png'
        if 'mimetype' in b:
            staticresources[hashname]=b
    return req.route_path('resource_request',statickey=hashname) #req.static_url(fname)

def makecalendar(req,gen):
    entryvec=[]
    for i in gen:
        dayurl=None
        if i==None:
            imageurl=None
        else:
            if i['is_valid']: #is not a custom missing image
                dayurl=dayurlfor(req,req.matchdict['accesstype'],req.matchdict['access'],i['time'])
            imageurl=req.route_path('image_resource',accesstype=req.matchdict['accesstype'],access=req.matchdict['access'],
                                    year=i['time'].year,month=i['time'].month,day=i['time'].day,filename=i['filename'])
            #print i[4]
        entryvec.append({'dayurl':dayurl,'imageurl':imageurl})
    return entryvec

@view_config(route_name='home',renderer='templates/portaltemplate.pt')
def portal_view(request):
    pl=plistlib.readPlist('/etc/dataarchive.plist')
    dirs=pl.Sites
    insts=pl.Instruments
    activeSites=[]
    activeSiteInfo={}
    activesites=[]
    inactivesites=[]

    siteid=0
    for site in dirs:
        if 'Windows' not in site or len(site.Windows)==0 or 'End' not in site.Windows[len(site.Windows)-1]:
            activeSites.append(siteid)
            activeSiteInfo[siteid]=site
        siteid+=1
        
    defaultaccesstype='by_site'
    for siteid in reversed(activeSites):
        n=activeSiteInfo[siteid]
        entry={}
        entry['name']=n.Name;
        linkset=[]
        linkarr=[]
        linkset.append({'name':"Archive:",'link':None})
        linkset.append({'link':request.route_path('thumb',accesstype=defaultaccesstype,access=siteid,thumbtype='all'),'name':'Multi-View'})

        ins=n.Instruments
        for i in ins:
            if i not in insts:
                continue
            inst=insts[i]
            if 'thumbsets' in inst and len(inst.thumbsets)>0:
                linkset.append({'link':request.route_path('thumb',accesstype=defaultaccesstype,access=siteid,thumbtype=inst.thumbsets[0].prefix),'name':i})
        linkarr.append(linkset)
        instlinks=len(linkset)
        linkset=[]
        if instlinks>3:
            imlink="http://lidar.ssec.wisc.edu/cgi-bin/ahsrldisplay/requestfigs.cgi?site=%i" % siteid
        else:
            imlink=request.route_path('imagegen',accesstype=defaultaccesstype,access=siteid)
        if instlinks>0:
            nclink="http://lidar.ssec.wisc.edu/cgi-bin/processeddata/retrievedata.cgi?site=%i" % siteid
        else:
            nclink=request.route_path('netcdfgen',accesstype=defaultaccesstype,access=siteid)
        linkarr.append([{'link':imlink,'name':"Custom Images"}])
        linkarr.append([{'link':nclink,'name':"Custom NetCDF"}])
        entry['linkarray']=linkarr
        activesites.append(entry)

    # activesites=reversed(activesites)

    siteid=len(dirs)
    for n in reversed(dirs):
        siteid-=1
        if siteid in activeSiteInfo:
            continue
        entry={}
        entry['name']=n.Name;
        linkset=[]
        linkarr=[]
        linkset.append({'name':"Archive:",'link':None})
        linkset.append({'link':request.route_path('thumb',accesstype=defaultaccesstype,access=siteid,thumbtype='all'),'name':'Multi-View'})

        ins=n.Instruments
        for i in ins:
            if i not in insts:
                continue
            inst=insts[i]
            if 'thumbsets' in inst and len(inst.thumbsets)>0:
                linkset.append({'link':request.route_path('thumb',accesstype=defaultaccesstype,access=siteid,thumbtype=inst.thumbsets[0].prefix),'name':i})
        linkarr.append(linkset)
        instlinks=len(linkset)
        linkset=[]
        if instlinks>3:
            imlink="http://lidar.ssec.wisc.edu/cgi-bin/ahsrldisplay/requestfigs.cgi?site=%i" % siteid
        else:
            imlink=request.route_path('imagegen',accesstype=defaultaccesstype,access=siteid)
        if instlinks>0:
            nclink="http://lidar.ssec.wisc.edu/cgi-bin/processeddata/retrievedata.cgi?site=%i" % siteid
        else:
            nclink=request.route_path('netcdfgen',accesstype=defaultaccesstype,access=siteid)
        linkarr.append([{'link':imlink,'name':"Custom Images"}])
        linkarr.append([{'link':nclink,'name':"Custom NetCDF"}])
        entry['linkarray']=linkarr
        inactivesites.append(entry)
    
    return { 
        'activesites':activesites,'inactivesites':inactivesites,
        'pagename':'HSRL Data Portal'
        }

@view_config(route_name='date',renderer='templates/datetemplate.pt')
def date_view(request):
    methodtype=request.matchdict['accesstype']
    methodkey=request.matchdict['access']
    yearno=int(request.matchdict['year'])
    monthno=int(request.matchdict['month'])
    dayno=int(request.matchdict['day'])
    ampm=request.matchdict['ampm']
    neg_ampm=None
    ampm_range=None
    if ampm=='am':
        hourno=0
        ampm_range='00:00-12:00'
    else:
        hourno=12
        ampm_range='12:00-00:00'
    selectdate=validdate(yearno,monthno,dayno,hourno)
    priordate=validdate(selectdate.year,selectdate.month,selectdate.day,selectdate.hour-12)
    nextdate=validdate(selectdate.year,selectdate.month,selectdate.day,selectdate.hour+12)
    vdate=None
    try:
        vdate=validClosestTime(methodtype,methodkey,selectdate)
    except:
        pass
    if vdate==None or vdate<selectdate or vdate>=nextdate:
        return redirect_day(request)
    priorlinkdate=validLaterTime(methodtype,methodkey,priordate)
    if priorlinkdate>=selectdate:
        priorlinkdate=validPriorTime(methodtype,methodkey,priordate)
    nextlinkdate=validLaterTime(methodtype,methodkey,nextdate)
    pagename='%s' % (methodkey)
    pagedesc=None
    pagedesc=selectdate.strftime('%B %e, %Y ') + ampm_range
    hightothumb={
        'bscat_depol':'bscat'
    }
    highimage=('bscat_depol')
    tgen=dpl_hsrl_imagearchive(methodtype,methodkey,None,False,selectdate,nextdate)
    if hasattr(tgen,'availableImagePrefixes'):
        highimage=tgen.availableImagePrefixes
    caltypes=None
    if hasattr(tgen,'availableThumbPrefixes'):
        caltypes=tgen.availableThumbPrefixes
    currenttime=datetime.utcnow();
    entries=[]
    for i in highimage:
        img=None
        try:
            gen=dpl_hsrl_imagearchive(methodtype,methodkey,i,False,selectdate,nextdate)
            if hasattr(gen,'SiteName'):
                pagename = gen.SiteName
            if hasattr(gen,'lowresform'):
                hightothumb[i]=gen.lowresform
            elif i not in hightothumb:
                hightothumb[i]=None
            for newimg in gen:
                img=newimg
        except KeyError as e:
            return HTTPNotFound(e)
        if img:
            calurl=monthurlfor(request,methodtype,methodkey,hightothumb[i],selectdate)
            imageurl=request.route_path('image_resource',accesstype=methodtype,access=methodkey,year=img['time'].year,month=img['time'].month,day=img['time'].day,filename=img['filename'])
            entries.append({'calurl':calurl,'imageurl':imageurl})
    nextlink=None
    prevlink=None
    if currenttime>nextdate and nextlinkdate:
        nextlink=dayurlfor(request,methodtype,methodkey,nextlinkdate)
    if priorlinkdate:
        prevlink=dayurlfor(request,methodtype,methodkey,priorlinkdate)
    ds=dpl_hsrllore_datasetForSite(int(methodkey))
    if len(entries)>1:
        imlink="http://lidar.ssec.wisc.edu/cgi-bin/ahsrldisplay/requestfigs.cgi"
    else:
        imlink=request.route_path('imagegen',accesstype=methodtype,access=methodkey)
    if len(entries)>0:
        nclink="http://lidar.ssec.wisc.edu/cgi-bin/processeddata/retrievedata.cgi"
    else:
        nclink=request.route_path('netcdfgen',accesstype=methodtype,access=methodkey)
    redirectbuttons=[]
    redirectbuttons.append(makeformbutton("Customize Image",imlink,selectdate,nextdate))
    redirectbuttons[-1]['inputs'].append({'name':'site','value':methodkey})#if nclink becomes from here, this parameter isn't needed
    redirectbuttons[-1]['inputs'].append({'name':'minalt','value':'0'})
    redirectbuttons[-1]['inputs'].append({'name':'maxalt','value':'15'})
    redirectbuttons.append(makeformbutton("Generate NetCDF",nclink,selectdate,nextdate))
    redirectbuttons[-1]['inputs'].append({'name':'site','value':methodkey})#if nclink becomes from here, this parameter isn't needed
    redirectbuttons[-1]['inputs'].append({'name':'minalt','value':'0'})
    redirectbuttons[-1]['inputs'].append({'name':'maxalt','value':'15'})
    redirectbuttons.append(makeformbutton("Show LogBook","http://lidar.ssec.wisc.edu/cgi-bin/logbook/showlogbook.cgi",selectdate,nextdate))
    redirectbuttons[-1]['inputs'].append({'name':'minalt','value':'0'})
    redirectbuttons[-1]['inputs'].append({'name':'maxalt','value':'15'})
    redirectbuttons[-1]['inputs'].append({'name':'dataset','value':'%i' % ds[0]})
    return { 
        'entries':entries,'caltypes':caltypes,
        'newmonthform':request.route_path("select_month"),'methodtype':methodtype,'methodkey':methodkey,
        'thistime':selectdate,'redirectbuttons':redirectbuttons,
        'prevlink':prevlink,'nextlink':nextlink,'pagename':pagename, 'pagedesc':pagedesc}

@view_config(route_name='month',renderer='templates/monthtemplate.pt')
@view_config(route_name='multiview',renderer='templates/monthtemplate.pt')
def month_view(request):
    methodtype=request.matchdict['accesstype']
    methodkey=request.matchdict['access']
    if 'thumbtype' in request.matchdict:
        subtypekey=request.matchdict['thumbtype']
    else:
        subtypekey='all'
    isMulti=(subtypekey=='all')
    yearno=int(request.matchdict['year'])
    monthno=int(request.matchdict['month'])
    dayno=1
    if 'day' in request.matchdict:
        if not isMulti:
            return redirect_month(request)
        dayno=int(request.matchdict['day'])
    elif isMulti:
        return redirect_month(request)
    datasetdesc=methodkey
    imagedesc=subtypekey
    thismonth=validdate(yearno,monthno,dayno)
    if isMulti:
        pagedesc=thismonth.strftime('%B %e, %Y')+' - '+validdate(thismonth.year,thismonth.month,thismonth.day+3).strftime('%B %e, %Y')
        nextmonth=validdate(thismonth.year,thismonth.month,thismonth.day+4)
        prevmonth=validdate(thismonth.year,thismonth.month,thismonth.day-4)
    else:
        pagedesc=thismonth.strftime('%B %Y')
        nextmonth=validdate(thismonth.year,thismonth.month+1)
        prevmonth=validdate(thismonth.year,thismonth.month-1)
    vdate=None
    try:
        vdate=validClosestTime(methodtype,methodkey,thismonth)
    except:
        pass
    if vdate==None or vdate<thismonth or vdate>=nextmonth:
        return redirect_month(request)
    priorlinkdate=validLaterTime(methodtype,methodkey,prevmonth)
    if priorlinkdate>=thismonth:
        priorlinkdate=validPriorTime(methodtype,methodkey,prevmonth)
    nextlinkdate=validLaterTime(methodtype,methodkey,nextmonth)
    currenttime=datetime.utcnow();
    endthismonth=nextmonth
    if subtypekey=='depol' or subtypekey=='bscat':
        pagedesc+=' 0-15km'
    nextlink=None
    prevlink=None
    
    if currenttime<=nextmonth:
        endthismonth=currenttime
    elif nextlinkdate:
        nextlink=monthurlfor(request,request.matchdict['accesstype'],methodkey,subtypekey,nextlinkdate)
    if priorlinkdate:
        prevlink=monthurlfor(request,request.matchdict['accesstype'],methodkey,subtypekey,priorlinkdate)

    caltypes=[]
    arr=[]
    entrynames=[]
    if isMulti:
        thumbs=dpl_hsrllore_simpleThumbPrefixes(int(methodkey))
    else:
        thumbs=(subtypekey,)

    for thumbtype in thumbs:
      try:
        usewindowstart=validLaterTime(methodtype,methodkey,thismonth)
        usewindowend=validPriorTime(methodtype,methodkey,endthismonth)
        #print 'range'
        #print usewindowstart
        #print usewindowend
        gen=dpl_hsrl_imagearchive(methodtype,methodkey,thumbtype,True,usewindowstart,usewindowend)
        if hasattr(gen,'SiteName'):
            datasetdesc=gen.SiteName
        if hasattr(gen,'ImageName'):
            imagedesc=gen.ImageName
        if hasattr(gen,'availableThumbPrefixes'):
            caltypes=gen.availableThumbPrefixes
      except KeyError as e:
        return HTTPNotFound(e)
      pagename='%s - %s' % (datasetdesc,imagedesc)
      entrynames.append(imagedesc)
      arr.append(makecalendar(request,gen))
    if subtypekey=="all":
        pagename='%s - Multi-View' % datasetdesc
    return {'project':'Picnic',
            'allentries':arr,'entrynames':entrynames,'newmonthform':request.route_path("select_month"),
            'selectedtype':subtypekey,'methodtype':methodtype,'methodkey':methodkey,
            'firsttime':validLaterTime(methodtype,methodkey,datetime(1990, 1, 1, 0, 0, 0)),
            'thistime':thismonth,
            'lasttime':validPriorTime(methodtype,methodkey,currenttime),
            'caltypes':caltypes,'monthnames':calendar.month_name,
            'missingimageurl':staticurlfor(request,'missing_thumb.jpg',safejoin('/data/web_temp/clients/null','missing_thumb.jpg')),
            'blankimageurl':staticurlfor(request,'blank_thumb.jpg',safejoin('/data/web_temp/clients/null','blank_thumb.jpg')),
            'prevlink':prevlink,'nextlink':nextlink,'pagename':pagename, 'pagedesc':pagedesc}

def makedpl(mystdout,dplparameters,processingfunction,session,precall=None):
    os.dup2(mystdout.fileno(),sys.stdout.fileno())
    os.dup2(mystdout.fileno(),sys.stderr.fileno())
    from hsrl.dpl_experimental.dpl_rti import dpl_rti
    if precall!=None:
        precall(session,dplparameters)
    print 'DPL_RTI Init Parameters:'
    print dplparameters
    dplc=dpl_rti(*dplparameters)
    processingfunction(dplc,session)

def dp_images_setup(session,dplparms):
    import hsrl.data_stream.display_utilities as du
    (disp,conf)=du.get_display_defaults('all_plots.json')
    #else:#fixme should this be enable_all()?
    #    (disp,conf)=du.get_display_defaults('web_plots.json')
    if None not in session['figstocapture']: # None indicates all should be captured, so if its not, scan structure
        data_req='images'
        for fi in disp.get_attrs(): # for each figure
            if 'enable' in disp.get_labels(fi): # if it can be enabled/disabled
                if fi in session['figstocapture']: #if requested, enable it
                    disp.set_value(fi,'enable',1)
                    if fi.startswith('show'):
                        data_req='images housekeeping'
                else:
                    disp.set_value(fi,'enable',0) #otherwise disable it
    else:
        data_req= 'images housekeeping'

    session['display_defaults']=disp
    while len(dplparms)<10:
        dplparms.append(None)
    dplparms[9]=data_req

def dp_images(dplc,session):
    import hsrl.data_stream.open_config as oc
    import hsrl.data_stream.display_utilities as du
    import hsrl.calibration.cal_read_utilities as cru
    import json
    import hsrl.graphics.graphics_toolkit as gt
    instrument=session['dataset']
    sessionid=session['sessionid']
    disp=session['display_defaults']

    folder=safejoin('.','sessions',sessionid);
    
    rs=None
    for n in dplc:
        #print 'loop'
        figs=du.show_images(instrument,n,dplc.rs_init.sounding,
                            dplc.rs_init.rs_constants,
                            dplc.rs_static.processing_defaults,
                            disp,
                            dplc.rs_init.last_sounding_time,
                            dplc.rs_static.max_alt,None)
        #print n.rs_inv.beta_a_backscat_par
        #print n.rs_inv.times
        # force a redraw
        rs=n
        fignum=0

        alreadycaptured=[]

        for x in session['figstocapture']:#plt._pylab_helpers.Gcf.get_all_fig_managers():
            if x in alreadycaptured:
                continue
            alreadycaptured.append(x)
            if x == None:
                tmp=[ f for f in figs ];
                tmp.sort()
                session['figstocapture'].extend(tmp)
                continue
            figname=safejoin(folder,'figure%04i_%s.png' % (fignum,x))
            fignum = fignum + 1
        #      print 'updating  %d' % x.num
            if x not in figs:
                f=file(figname,'w')
                f.close()
                continue
        
            fig = figs.figure(x)#plt.figure(x.num)
        
      # QApplication.processEvents()
            
            fig.canvas.draw()
            #fig.canvas.
            fig.savefig(figname,format='png',bbox_inches='tight')
    
@view_config(route_name='imageresult',renderer='templates/imageresult.pt')
def imageresult(request):
    sessionid=request.matchdict['session']#request.session.get_csrf_token();#params.getone('csrf_token')
    folder=safejoin('.','sessions',sessionid);
    #sessiontask=tasks[sessionid]
    #session=sessiontask['session']
    #scan session folder for images
    session=json.load(file(safejoin(folder,"session.json")))
    ims = []
    try:
        fl=os.listdir(folder)
    except:
        fl=[]
    for f in fl:
        if f.endswith('.png'):
            ims.append( request.route_path('session_resource',session=sessionid,filename=f) )
    ims.sort()
    #send to template
    return { 'imageurls':ims, 'logfileurl':session['logfileurl'],'logbookurl':session['logbookurl'],
             'sitename':session['name'], 'site':session['site'] ,
             'timespan':'FIXMEtimespan', 'rangespan':'FIXMErangespan' } 
    
@view_config(route_name='imagereq')
def imagerequest(request):
    session=request.session
    sessionid=session.new_csrf_token()
    sessiondict={}
    #sessionid=request.POST['csrf_token']
    #add task status to list
    #print request.route_path('imageresult')
    sessiondict['finalpage']=request.route_path('imageresult',session=sessionid);
    tasks[sessionid]=None
    #load parameters
    #print request.params

    method='site'
    methodkey=int(request.params.getone(method));
    starttime=datetime(int(request.params.getone('byr')),
                       int(request.params.getone('bmo')),
                       int(request.params.getone('bdy')),
                       int(request.params.getone('bhr')),
                       int(request.params.getone('bmn')),
                       0)
    endtime=datetime(int(request.params.getone('eyr')),
                     int(request.params.getone('emo')),
                     int(request.params.getone('edy')),
                     int(request.params.getone('ehr')),
                     int(request.params.getone('emn')),
                     0)
    timeres=(endtime-starttime).total_seconds()/640 #640 pixels wide
    altmin=float(request.params.getone('lheight'))*1000
    altmax=float(request.params.getone('height'))*1000
    altres=(altmax-altmin)/480 # 480 pixels high
    #contstruct dpl
    (instruments,name,datasetname)=dpl_hsrllore_simpleDatasets(int(methodkey))
    imagesetlist=formsetsForInstruments(instruments,'images')
 
    figstocapture=[]
    for i in imagesetlist:
        #print i
        try:
            setmode=request.params.getone(i['formname'])
            figstocapture.extend(i['sets'][setmode]['figs'])
        except:
            pass
    #print figstocapture

    #return HTTPTemporaryRedirect(location=request.route_path('progress_withid',session=sessionid))

    #dplc=dpl_rti(datasetname,starttime,endtime,timedelta(seconds=timeres),endtime-starttime,altmin,altmax,altres);#alt in m
    #construct image generation parameters
    sessiondict['dataset']=datasetname
    sessiondict['name']=name
    sessiondict['site']=methodkey
    sessiondict['sessionid']=sessionid
    sessiondict['figstocapture']=figstocapture
    #if None in session['figstocapture']:

    folder=safejoin('.','sessions',sessionid);
    os.mkdir(folder)
  
    #start process
    logfilepath=safejoin(folder,'logfile')
    stdt=file(logfilepath,'w')
    tasks[sessionid]=multiprocessing.Process(target=makedpl,args=(stdt,[datasetname,starttime,endtime,timedelta(seconds=timeres),endtime-starttime,altmin,altmax,altres],dp_images,sessiondict,dp_images_setup))
    tasks[sessionid].start()
    stdt.close()
    sessiondict['logfileurl']= request.route_path('session_resource',session=sessionid,filename='logfile') 
    sv=dpl_hsrllore_datasetForSite(methodkey)
    #print sv
    sessiondict['logbookurl']='http://lidar.ssec.wisc.edu/cgi-bin/logbook/showlogbook.cgi?dataset=%i&rss=off&byr=%i&bmo=%i&bdy=%i&bhr=%i&bmn=%i&eyr=%i&emo=%i&edy=%i&ehr=%i&emn=%i' % (sv[0],starttime.year,starttime.month,starttime.day,starttime.hour,starttime.minute,endtime.year,endtime.month,endtime.day,endtime.hour,endtime.minute)

    json.dump(sessiondict,file(safejoin(folder,'session.json'),'w'))
    
    #redirect to the progress page
    return HTTPTemporaryRedirect(location=request.route_path('progress_withid',session=sessionid))


@view_config(route_name='dataAvailability')
def dataAvailability(request):
    site=request.params.getone('site')
    starttime=request.params.getone('time0')
    endtime=request.params.getone('time1')
    p, childStdout = os.pipe()
    pid=os.fork()
    if pid==0:
        os.close(p)
        os.dup2(childStdout,sys.stdout.fileno())
        os.execv("/home/jpgarcia/hsrl.git/ahsrl/compressedread/dataAvailability",("/home/jpgarcia/hsrl.git/ahsrl/compressedread/dataAvailability",'p',site,starttime,endtime))
        sys.exit()
    os.close(childStdout)
    os.waitpid(pid,0)
    response=request.response
    response.content_type='text/plain'
    
    response.body=os.read(p,4096)
    os.close(p)
    return response
    
@view_config(route_name='progress')
def progress_getlastid(request):
    sessionid=request.session.get_csrf_token()  #get_cookies['session']#POST['csrf_token']
    return HTTPTemporaryRedirect(location=request.route_path("progress_withid",session=sessionid))
    
@view_config(route_name='progress_withid',renderer='templates/progress.pt')
def progresspage(request):
    sessionid=request.matchdict['session']#session.get_csrf_token()  #get_cookies['session']#POST['csrf_token']
    #check status of this task
    #if sessionid not in tasks:
    #    return HTTPNotFound('Invalid session')
    folder=safejoin('.','sessions',sessionid);
    session=json.load(file(safejoin(folder,"session.json")))
    if sessionid in tasks and tasks[sessionid]!=None and tasks[sessionid].is_alive():
        #load intermediate if not
        return {'pagename':session['name'],'progresspage':request.route_path('progress_withid',session=sessionid),'sessionid':sessionid,'destination':session['finalpage']}
    #load next page if complete
    return HTTPTemporaryRedirect(location=session['finalpage'])

@view_config(route_name='netcdfgen',renderer='templates/netcdfrequest.pt')
@view_config(route_name='imagegen',renderer='templates/imagerequest.pt')
def form_view(request):
    methodtype=request.matchdict['accesstype']
    methodkey=request.matchdict['access']
    if methodtype=='by_site':
        pathname='site'
        pathidx=int(methodkey)
    (instruments,name,datasetname)=dpl_hsrllore_simpleDatasets(pathidx)

    try:
        starttime=validdate(int(request.params.getone('byr')),
                            int(request.params.getone('bmo')),
                            int(request.params.getone('bdy')),
                            int(request.params.getone('bhr')),
                            int(request.params.getone('bmn')))
        endtime=validdate(int(request.params.getone('eyr')),
                          int(request.params.getone('emo')),
                          int(request.params.getone('edy')),
                          int(request.params.getone('ehr')),
                          int(request.params.getone('emn')))
        maxalt=float(request.params.getone('maxalt'))
        minalt=float(request.params.getone('minalt'))
    except:
        #print 'fallback'
        #print request.POST
        #print request.GET
        minalt=0
        maxalt=15
        lasttime=validClosestTime(methodtype,methodkey,datetime.utcnow())
        endtime=validdate(lasttime.year,lasttime.month,lasttime.day,lasttime.hour,lasttime.minute-(lasttime.minute%5))
        starttime=validdate(endtime.year,endtime.month,endtime.day,endtime.hour-2,endtime.minute)

    #print request
    # used in both forms, but simplifies template
    alts=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,20,25,30] #in kilometers
    # these are only used in netcdf, and not form-configurable. this simplifies the template
    altres=30
    timeres=30
    altresvals=[7.5,15,30,45,60,75,90,120,150,300,450,600,900,1200] # in meters
    timeresvals=[2.5,5,10,15,30,60,120,180,240,300,600,900,1200,3600,43200] # in seconds

                                                                            #print instruments

    hosttouse=None
    porttouse=None
    if "X-Forwarded-Host" in request.headers:
        hosttouse=request.headers['X-Forwarded-Host']
        porttouse=''

    return {'project':'Picnic',
            'bdate':starttime,
            'edate':endtime,'monthnames':calendar.month_name,
            'altrange':[minalt,maxalt],'alts':alts,
            'timeresvals':timeresvals,'altresvals':altresvals,
            'timeres':timeres,'altres':altres,
            'imagesets':formsetsForInstruments(instruments,'images'),
            'netcdfsets':formsetsForInstruments(instruments,'netcdf'),
            'datasets':instruments,pathname:pathidx,
            'netcdfdestinationurl':request.route_url('netcdfreq',_host=hosttouse,_port=porttouse),
            'imagedestinationurl':request.route_url('imagereq',_host=hosttouse,_port=porttouse),
            'dataAvailabilityURL':request.route_path('dataAvailability'),
            'sitename':name}

def infoOfFile(fn):
    tmp=os.stat(fn)
    return (datetime.utcfromtimestamp(tmp.st_ctime),datetime.utcfromtimestamp(tmp.st_mtime),tmp.st_size)

from operator import itemgetter
            
@view_config(route_name='status',renderer='templates/status.pt')
def statuspage(request):
    folder=safejoin('.','sessions');
    sess=os.listdir(folder)
    sessinfo=[(n,infoOfFile(safejoin(folder,n))[0],tasks[n].is_alive() if n in tasks and tasks[n]!=None else False,tasks[n] if n in tasks else None) for n in sess]
    sessinfo.sort(key=itemgetter(1),reverse=True)
    runningtasks=0
    for ses in tasks:
        if tasks[ses]!=None and tasks[ses].is_alive():
            runningtasks=runningtasks+1
    return {'sessions':sess,
            'sessioninfo':sessinfo,
            'runningtasks':runningtasks}

@view_config(route_name='debug',renderer='templates/debug.pt')
def debugpage(request):
    info=[]
    info.append({'name':'Python','content':sys.executable})
    info.append({'name':'Python Version','content':sys.version})
    info.append({'name':'Python platform','content':sys.platform})
    info.append({'name':'Python Path','content':os.getenv('PYTHONPATH',"")})
    return {'simpleinfos':info}

@view_config(route_name='debugsession',renderer='templates/debugsession.pt')
def debugsession(request):
    sessionid=request.matchdict['session']
    folder=safejoin('.','sessions',sessionid);
    session=json.load(file(safejoin(folder,"session.json")))
    if sessionid in tasks and tasks[sessionid]!=None:
        task=tasks[sessionid]
        running=task.is_alive()
    else:
        task=None
        running=False
    if os.access(folder,os.R_OK):
        filelist=os.listdir(folder)
        filelist.sort()
        filelistinfo=[]
        for f in filelist:
            inf=infoOfFile(safejoin(folder,f))
            filelistinfo.append((f,inf[2],inf[0],inf[1]))
    else:
        filelist=None
        filelistinfo=None
    if 'session.json' in filelist:
        session=json.load(file(safejoin(folder,"session.json")))
    else:
        session=None
    return {'task':task,
            'files':filelist,
            'fileinfo':filelistinfo,
            'session':session,
            'running':running,
            'sessionid':sessionid}
