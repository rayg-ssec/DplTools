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

def validdate(yearno,monthno,dayno=1,hourno=0):
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
    return datetime(yearno,monthno,dayno,hourno,0,0)

def monthurlfor(atype,access,imtype,date):
    return '/%s/%s/%s/%04i/%02i/' % (atype,access,imtype,date.year,date.month)

@view_config(route_name='select_month')
def select_month(request):
    if not ('accessto' in request.params and 'accessby' in request.params and 'type' in request.params):
        return HTTPTemporaryRedirect(location='/')
    if not ('year' in request.params and 'month' in request.params):
        return HTTPTemporaryRedirect(location='/%s/%s/%s/' % (request.params.getone('accessby'),request.params.getone('accessto'),request.params.getone('type')))
    selected=validdate(int(request.params.getone('year')),int(request.params.getone('month')))
    return HTTPTemporaryRedirect(location=monthurlfor(request.params.getone('accessby'),
                                                      request.params.getone('accessto'),
                                                      request.params.getone('type'),
                                                      selected))

def redirect_month(request):
    methodtype=request.matchdict['accesstype']
    methodkey=request.matchdict['access']
    subtypekey=request.matchdict['thumbtype']
    if 'year' in request.matchdict:
        yearno=int(request.matchdict['year'])
    else:
        yearno=datetime.utcnow().year
    if 'month' in request.matchdict:
        monthno=int(request.matchdict['month'])
    else:
        monthno=datetime.utcnow().month
    besttime=validClosestTime(methodtype,methodkey,datetime(yearno,monthno,1,0,0,0))
    return HTTPTemporaryRedirect(location=monthurlfor(methodtype,methodkey,subtypekey,besttime))


def dayurlfor(atype,access,date):
    returl='/%s/%s/%04i/%02i/%02i/' % (atype,access,date.year,date.month,date.day)
    if date.hour<12:
        returl+='am/'
    else:
        returl+='pm/'
    return returl

@view_config(route_name='select_day')
def select_day(request):
    if not ('accessto' in request.params and 'accessby' in request.params):
        return HTTPTemporaryRedirect(location='/')
    if not ('year' in request.params and 'month' in request.params and 'day' in request.params and 'hour' in request.params):
        return HTTPTemporaryRedirect(location='/%s/%s/' % (request.params.getone('accessby'),request.params.getone('accessto')))
    selected=validdate(int(request.params.getone('year')),int(request.params.getone('month')),int(request.params.getone('day')),int(request.params.getone('hour')))
    return HTTPTemporaryRedirect(location=monthurlfor(request.params.getone('accessby'),
                                                      request.params.getone('accessto'),
                                                      selected))
def redirect_day(request):
    methodtype=request.matchdict['accesstype']
    methodkey=request.matchdict['access']
    if 'year' in request.matchdict:
        yearno=int(request.matchdict['year'])
    else:
        yearno=datetime.utcnow().year
    if 'month' in request.matchdict:
        monthno=int(request.matchdict['month'])
    else:
        monthno=datetime.utcnow().month
    if 'day' in request.matchdict:
        dayno=int(request.matchdict['day'])
    else:
        dayno=datetime.utcnow().day
    if 'ampm' in request.matchdict:
        ampm=request.matchdict['ampm']
        if ampm=='am':
            hourno=0
        else:
            hourno=12
    else:
        hourno=datetime.utcnow().hour
    besttime=validClosestTime(methodtype,methodkey,datetime(yearno,monthno,dayno,hourno,0,0))
    #if besttime.hour<12:
    #    ampm='am'
    #else:
    #    ampm='pm'
    return HTTPTemporaryRedirect(location=dayurlfor(methodtype,methodkey,besttime))
    #'/%s/%s/%04i/%02i/%02i/%s/' % (methodtype,methodkey,besttime.year,besttime.month,besttime.day,ampm))

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

def imageurlfor(inst,date,fname,fullfile):
    hashname=fname
    if date!=None:
        hashname='%s_%04i%02i%02i_' % (inst,date.year,date.month,date.day) + hashname
    if hashname not in staticresources:
        b={}
        b['filename']=fullfile
        b['mimetype']='image/jpeg'
        staticresources[hashname]=b
    return '/statichash/'+ hashname #req.static_url(fname)

def makecalendar(req,gen):
    entryvec=[]
    for i in gen:
        dayurl=None
        if i==None:
            imageurl=None
        else:
            if not i[3]: #is not a custom missing image
                dayurl=dayurlfor(req.matchdict['accesstype'],req.matchdict['access'],i[1])
            imageurl=imageurlfor(i[0],i[1],i[2],i[4])
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
        #linkset.append({'link':"/cgi-bin/archive/month?site=%i&type=all" % siteid,'name':'Multi-View'})

        ins=n.Instruments
        for i in ins:
            if i not in insts:
                continue
            inst=insts[i]
            if 'thumbsets' in inst and len(inst.thumbsets)>0:
                linkset.append({'link':"/by_site/%i/%s/" % (siteid,inst.thumbsets[0].prefix),'name':i})
        linkarr.append(linkset)
        linkset=[]
        linkarr.append([{'link':"http://lidar.ssec.wisc.edu/cgi-bin/ahsrldisplay/requestfigs.cgi?site=%i" % siteid,
                         #'link':"/by_site/%i/custom_rti/" % siteid ,
                         'name':"Custom Images"}])
        linkarr.append([{'link':"http://lidar.ssec.wisc.edu/cgi-bin/processeddata/retrievedata.cgi?site=%i" % siteid,
                         #'link':"/by_site/%i/custom_netcdf/" % siteid ,
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
        #linkset.append({'link':"/cgi-bin/archive/month?site=%i&type=all" % siteid,'name':'Multi-View'})

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
        linkarr.append([{'link':"http://lidar.ssec.wisc.edu/cgi-bin/ahsrldisplay/requestfigs.cgi?site=%i" % siteid,
                         #'link':"/by_site/%i/custom_rti/" % siteid,
                         'name':"Custom Images"}])
        linkarr.append([{'link':"http://lidar.ssec.wisc.edu/cgi-bin/processeddata/retrievedata.cgi?site=%i" % siteid,
                         #'link':"/by_site/%i/custom_netcdf/" % siteid,
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
    vdate=validClosestTime(methodtype,methodkey,selectdate)
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
        except KeyError:
            return HTTPNotFound("%s doesn't resolve using method %s" % (methodkey,request.matchdict['accesstype']))
        if img:
            calurl=monthurlfor(request.matchdict['accesstype'],methodkey,hightothumb[i],selectdate)
            imageurl=imageurlfor(img[0],img[1],img[2],img[4])
            entries.append({'calurl':calurl,'imageurl':imageurl})
    nextlink=None
    prevlink=None
    if datetime.utcnow()>nextdate and nextlinkdate:
        nextlink=dayurlfor(request.matchdict['accesstype'],methodkey,nextlinkdate)
    if priorlinkdate:
        prevlink=dayurlfor(request.matchdict['accesstype'],methodkey,priorlinkdate)
    return { 
        'entries':entries,
        'prevlink':prevlink,'nextlink':nextlink,'pagename':pagename, 'pagedesc':pagedesc}

@view_config(route_name='month',renderer='templates/monthtemplate.pt')
def month_view(request):
    methodtype=request.matchdict['accesstype']
    methodkey=request.matchdict['access']
    subtypekey=request.matchdict['thumbtype']
    yearno=int(request.matchdict['year'])
    monthno=int(request.matchdict['month'])
    datasetdesc=methodkey
    imagedesc=subtypekey
    thismonth=validdate(yearno,monthno)
    nextmonth=validdate(thismonth.year,thismonth.month+1)
    prevmonth=validdate(thismonth.year,thismonth.month-1)
    vdate=validClosestTime(methodtype,methodkey,thismonth)
    if vdate==None or vdate<thismonth or vdate>=nextmonth:
        return redirect_month(request)
    priorlinkdate=validLaterTime(methodtype,methodkey,prevmonth)
    if priorlinkdate>=thismonth:
        priorlinkdate=validPriorTime(methodtype,methodkey,prevmonth)
    nextlinkdate=validLaterTime(methodtype,methodkey,nextmonth)
    #    currenttime=datetime.utcnow();
    endthismonth=nextmonth
    pagedesc=thismonth.strftime('%B %Y')
    if subtypekey=='depol' or subtypekey=='bscat':
        pagedesc+=' 0-15km'
    nextlink=None
    prevlink=None
    if datetime.utcnow()<=nextmonth:
        endthismonth=datetime.utcnow()
    elif nextlinkdate:
        nextlink=monthurlfor(request.matchdict['accesstype'],methodkey,subtypekey,nextlinkdate)
    if priorlinkdate:
        prevlink=monthurlfor(request.matchdict['accesstype'],methodkey,subtypekey,priorlinkdate)

    caltypes=[]

    try:
        usewindowstart=validLaterTime(methodtype,methodkey,thismonth)
        usewindowend=validPriorTime(methodtype,methodkey,endthismonth)
        #print 'range'
        #print usewindowstart
        #print usewindowend
        gen=dpl_hsrl_imagearchive(methodtype,methodkey,subtypekey,True,usewindowstart,usewindowend)
        if hasattr(gen,'SiteName'):
            datasetdesc=gen.SiteName
        if hasattr(gen,'ImageName'):
            imagedesc=gen.ImageName
        if hasattr(gen,'availableThumbPrefixes'):
            caltypes=gen.availableThumbPrefixes
    except KeyError:
        return HTTPNotFound("%s doesn't resolve using method %s" % (methodkey,request.matchdict['accesstype']))
    pagename='%s - %s' % (datasetdesc,imagedesc)
    arr=makecalendar(request,gen)
    return {'project':'Picnic',
            'entries':arr,'newmonthform':"/selectmonth",'selectedtype':subtypekey,'methodtype':methodtype,'methodkey':methodkey,
            'firsttime':validLaterTime(methodtype,methodkey,datetime(1990, 1, 1, 0, 0, 0)),
            'thistime':thismonth,
            'lasttime':validPriorTime(methodtype,methodkey,datetime.utcnow()),
            'caltypes':caltypes,'monthnames':calendar.month_name,
            'missingimageurl':imageurlfor(None,None,'missing_thumb.jpg',os.path.join('/data/web_temp/clients/null','missing_thumb.jpg')),
            'blankimageurl':imageurlfor(None,None,'blank_thumb.jpg',os.path.join('/data/web_temp/clients/null','blank_thumb.jpg')),
            'prevlink':prevlink,'nextlink':nextlink,'pagename':pagename, 'pagedesc':pagedesc}
