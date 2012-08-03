from pyramid.view import view_config
from dpl_hsrl_imagearchive import *
from datetime import datetime
from pyramid.httpexceptions import HTTPNotFound, HTTPTemporaryRedirect
from webob import Response
from hashlib import sha1 as hashfunc
import os
import calendar
import plistlib

staticresources={};

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
    URL='/%s/%s/%s/%04i/%02i/' % (atype,access,imtype,date.year,date.month)
    if imtype=='all':
        URL+='%02i/' % (date.day)
    return req.relative_url(URL,to_application=True)

@view_config(route_name='select_month')
def select_month(request):
    try:
        if not ('year' in request.params and 'month' in request.params):
            return HTTPTemporaryRedirect(location=request.relative_url('/%s/%s/%s/' % (request.params.getone('accessby'),
                                                                                       request.params.getone('accessto'),
                                                                                       request.params.getone('type')),
                                                                       to_application=True))
        selected=validdate(int(request.params.getone('year')),int(request.params.getone('month')))
        return HTTPTemporaryRedirect(location=monthurlfor(request,
                                                          request.params.getone('accessby'),
                                                          request.params.getone('accessto'),
                                                          request.params.getone('type'),
                                                          selected))
    except:
        return HTTPTemporaryRedirect(location=request.relative_url("/",to_application=True))

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
    #return HTTPTemporaryRedirect(location=request.relative_url("/",to_application=True))        

def dayurlfor(req,atype,access,date):
    returl='/%s/%s/%04i/%02i/%02i/' % (atype,access,date.year,date.month,date.day)
    if date.hour<12:
        returl+='am/'
    else:
        returl+='pm/'
    return req.relative_url(returl,to_application=True)

@view_config(route_name='select_day')
def select_day(request):
    try:
        if not ('year' in request.params and 'month' in request.params and 'day' in request.params and 'hour' in request.params):
            return HTTPTemporaryRedirect(location=request.relative_url('/%s/%s/' % (request.params.getone('accessby'),request.params.getone('accessto'))))
        selected=validdate(int(request.params.getone('year')),int(request.params.getone('month')),int(request.params.getone('day')),int(request.params.getone('hour')))
        return HTTPTemporaryRedirect(location=monthurlfor(request,
                                                          request.params.getone('accessby'),
                                                          request.params.getone('accessto'),
                                                          selected))
    except:
        return HTTPTemporaryRedirect(location=request.relative_url('/',to_application=True))

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
        return HTTPTemporaryRedirect(location=request.relative_url('/',to_application=True))

@view_config(route_name='image_request')
def image_request(request):
    #print request
    #print request.matchdict
    k=request.matchdict['statickey'];
    if k in staticresources:
        f=open(staticresources[k]['filename'])
        if f:
            mt=staticresources[k]['mimetype']
            return Response(content_type=mt,app_iter=f)
        staticresources.erase(k);
    return HTTPNotFound("Image doesn't exist in request cache")

def imageurlfor(req,inst,date,fname,fullfile):
    hashname=fname
    if date!=None:
        hashname='%s_%04i%02i%02i_' % (inst,date.year,date.month,date.day) + hashname
    if hashname not in staticresources:
        b={}
        b['filename']=fullfile
        if fullfile.endswith('.jpg'):
            b['mimetype']='image/jpeg'
        if fullfile.endswith('.png'):
            b['mimetype']='image/png'
        if 'mimetype' in b:
            staticresources[hashname]=b
    return req.relative_url('/statichash/'+ hashname,to_application=True) #req.static_url(fname)

def makecalendar(req,gen):
    entryvec=[]
    for i in gen:
        dayurl=None
        if i==None:
            imageurl=None
        else:
            if i['is_valid']: #is not a custom missing image
                dayurl=dayurlfor(req,req.matchdict['accesstype'],req.matchdict['access'],i['time'])
            imageurl=imageurlfor(req,i['instrument'],i['time'],i['filename'],i['path'])
            #print i[4]
        entryvec.append({'dayurl':dayurl,'imageurl':imageurl})
    return entryvec

@view_config(route_name='home',renderer='templates/portaltemplate.pt')
def portal_view(request):
    pl=plistlib.readPlist('/etc/dataarchive.plist')
    dirs=pl.Sites
    insts=pl.Instruments
    retstr=''#<UL>\n'
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

    for siteid in reversed(activeSites):
        n=activeSiteInfo[siteid]
        entry={}
        entry['name']=n.Name;
        linkset=[]
        linkarr=[]
        linkset.append({'name':"Archive:",'link':None})
        linkset.append({'link':"/by_site/%i/all/" % siteid,'name':'Multi-View'})

        ins=n.Instruments
        for i in ins:
            if i not in insts:
                continue
            inst=insts[i]
            if 'thumbsets' in inst and len(inst.thumbsets)>0:
                linkset.append({'link':"/by_site/%i/%s/" % (siteid,inst.thumbsets[0].prefix),'name':i})
        linkarr.append(linkset)
        linkset=[]
        linkarr.append([{#'link':"http://lidar.ssec.wisc.edu/cgi-bin/ahsrldisplay/requestfigs.cgi?site=%i" % siteid,
                         'link':"/by_site/%i/custom_rti/" % siteid ,
                         'name':"Custom Images"}])
        linkarr.append([{#'link':"http://lidar.ssec.wisc.edu/cgi-bin/processeddata/retrievedata.cgi?site=%i" % siteid,
                         'link':"/by_site/%i/custom_netcdf/" % siteid ,
                         'name':"Custom NetCDF"}])
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
        linkset.append({'link':"/by_site/%i/all/" % siteid,'name':'Multi-View'})

        ins=n.Instruments
        for i in ins:
            if i not in insts:
                continue
            inst=insts[i]
            if 'thumbsets' in inst and len(inst.thumbsets)>0:
                linkset.append({'link':"/by_site/%i/%s/" % (siteid,inst.thumbsets[0].prefix),'name':i})
                retstr+="- <a href=\"/by_site/%i/%s/\">%s</a>\n" % (siteid,inst.thumbsets[0].prefix,i);
        linkarr.append(linkset)
        linkset=[]
        linkarr.append([{#'link':"http://lidar.ssec.wisc.edu/cgi-bin/ahsrldisplay/requestfigs.cgi?site=%i" % siteid,
                         'link':"/by_site/%i/custom_rti/" % siteid,
                         'name':"Custom Images"}])
        linkarr.append([{#'link':"http://lidar.ssec.wisc.edu/cgi-bin/processeddata/retrievedata.cgi?site=%i" % siteid,
                         'link':"/by_site/%i/custom_netcdf/" % siteid,
                         'name':"Custom NetCDF"}])
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
    pagedesc=selectdate.strftime('%B %d, %Y ') + ampm_range
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
            calurl=monthurlfor(request,request.matchdict['accesstype'],methodkey,hightothumb[i],selectdate)
            imageurl=imageurlfor(request,img['instrument'],img['time'],img['filename'],img['path'])
            entries.append({'calurl':calurl,'imageurl':imageurl})
    nextlink=None
    prevlink=None
    if currentime>nextdate and nextlinkdate:
        nextlink=dayurlfor(request,request.matchdict['accesstype'],methodkey,nextlinkdate)
    if priorlinkdate:
        prevlink=dayurlfor(request,request.matchdict['accesstype'],methodkey,priorlinkdate)
    redirectbuttons=[]
    redirectbuttons.append(makeformbutton("Customize Image","http://lidar.ssec.wisc.edu/cgi-bin/ahsrldisplay/requestfigs.cgi",selectdate,nextdate))
    redirectbuttons[-1]['inputs'].append({'name':'minalt','value':'0'})
    redirectbuttons[-1]['inputs'].append({'name':'maxalt','value':'15'})
    redirectbuttons[-1]['inputs'].append({'name':'site','value':methodkey})
    redirectbuttons.append(makeformbutton("Generate NetCDF","http://lidar.ssec.wisc.edu/cgi-bin/processeddata/retrievedata.cgi",selectdate,nextdate))
    redirectbuttons[-1]['inputs'].append({'name':'minalt','value':'0'})
    redirectbuttons[-1]['inputs'].append({'name':'maxalt','value':'15'})
    redirectbuttons[-1]['inputs'].append({'name':'site','value':methodkey})
    redirectbuttons.append(makeformbutton("Show LogBook","http://lidar.ssec.wisc.edu/cgi-bin/logbook/showlogbook.cgi",selectdate,nextdate))
    redirectbuttons[-1]['inputs'].append({'name':'minalt','value':'0'})
    redirectbuttons[-1]['inputs'].append({'name':'maxalt','value':'15'})
    redirectbuttons[-1]['inputs'].append({'name':'site','value':methodkey})
    redirectbuttons[-1]['inputs'].append({'name':'dataset','value':'%i' % dpl_hsrllore_datasetForSite(int(methodkey))})
    return { 
        'entries':entries,'caltypes':caltypes,
        'newmonthform':request.relative_url("/selectmonth",True),'methodtype':methodtype,'methodkey':methodkey,
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
        pagedesc=thismonth.strftime('%D %B %Y')
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
            'allentries':arr,'entrynames':entrynames,'newmonthform':request.relative_url("/selectmonth",True),'selectedtype':subtypekey,'methodtype':methodtype,'methodkey':methodkey,
            'firsttime':validLaterTime(methodtype,methodkey,datetime(1990, 1, 1, 0, 0, 0)),
            'thistime':thismonth,
            'lasttime':validPriorTime(methodtype,methodkey,currenttime),
            'caltypes':caltypes,'monthnames':calendar.month_name,
            'missingimageurl':imageurlfor(request,None,None,'missing_thumb.jpg',os.path.join('/data/web_temp/clients/null','missing_thumb.jpg')),
            'blankimageurl':imageurlfor(request,None,None,'blank_thumb.jpg',os.path.join('/data/web_temp/clients/null','blank_thumb.jpg')),
            'prevlink':prevlink,'nextlink':nextlink,'pagename':pagename, 'pagedesc':pagedesc}


@view_config(route_name='netcdfgen',renderer='templates/netcdfrequest.pt')
@view_config(route_name='imagegen',renderer='templates/imagerequest.pt')
def form_view(request):
    methodtype=request.matchdict['accesstype']
    methodkey=request.matchdict['access']
    if methodtype=='by_site':
        pathname='site'
        pathidx=int(methodkey)
    lasttime=validClosestTime(methodtype,methodkey,datetime.utcnow())
    endtime=validdate(lasttime.year,lasttime.month,lasttime.day,lasttime.hour,lasttime.minute-(lasttime.minute%5))
    starttime=validdate(endtime.year,endtime.month,endtime.day,endtime.hour-2,endtime.minute)
    (instruments,name)=dpl_hsrllore_simpleDatasets(int(methodkey))
    return {'project':'Picnic',
            'bdate':starttime,
            'edate':endtime,'monthnames':calendar.month_name,
            'datasets':instruments,pathname:pathidx,
            'sitename':name}
