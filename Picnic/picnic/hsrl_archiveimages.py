from pyramid.view import view_config
from datetime import datetime,timedelta
from pyramid.httpexceptions import HTTPNotFound, HTTPTemporaryRedirect
from webob import Response
import calendar
import picnicsession
import os
imagepathcache={}


from timeutils import validdate

from HSRLImageArchiveLibrarian import HSRLImageArchiveLibrarian
lib=HSRLImageArchiveLibrarian(indexdefault='site')

@view_config(route_name='image_resource')
def image_resource(request):
    fn=request.matchdict['filename']
    if 'accesstype' in request.matchdict:
        global imagepathcache
        global imagepathcacheage
        methodtype=request.matchdict['accesstype']
        methodkey=request.matchdict['access']
        yearno=int(request.matchdict['year'])
        monthno=int(request.matchdict['month'])
        dayno=int(request.matchdict['day'])
        #FIXME HACKY CACHY
        #md=moddateoffile("/etc/dataarchive.plist")
        #if imagepathcacheage==None or imagepathcacheage!=md:
        #    imagepathcacheage=md
        #    imagepathcache.clear()
        if methodtype not in imagepathcache or methodkey not in imagepathcache[methodtype]:
            #if len(imagepathcache)==0:
            #    imagepathcacheage=moddateoffile("/etc/dataarchive.plist")
            if methodtype not in imagepathcache:
                imagepathcache[methodtype]={}
            try:
                imagepathcache[methodtype][methodkey]=lib(**{methodtype[3:]:methodkey})['Path']
            except RuntimeError:
                return HTTPNotFound(methodtype[3:] + "-" + methodkey + " is invalid")
#  return HTTPNotFound("File doesn't exist")

            
        f=picnicsession.safejoin(imagepathcache[methodtype][methodkey],'%04i' % yearno,'%02i' % monthno, '%02i' % dayno,'images',fn)
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
    if fn.endswith('.nc') or fn.endswith('.cdf'):
        m='application/x-netcdf'

    if m==None:
        return HTTPNotFound("File inaccessible")
    return Response(content_type=m,app_iter=file(f))

def monthurlfor(req,atype,access,imtype,date):
    if imtype==None or imtype=='all':
        return req.route_path('multiview',accesstype=atype,access=access,year=date.year,month='%02i' % date.month,day='%02i' % date.day)
    return req.route_path('month',accesstype=atype,access=access,thumbtype=imtype,year=date.year,month='%02i' % date.month)

@view_config(route_name='select_month')
def select_month(request):
    try:
        if not ('year' in request.params and 'month' in request.params):
            return HTTPTemporaryRedirect(location=request.route_path('thumb',
                                                                    accesstype=request.params.getone('accessby'),
                                                                    access=request.params.getone('accessto'),
                                                                    thumbtype=request.params.getone('type')))
        selected=validdate(int(request.params.getone('year')),int(request.params.getone('month')))
        if 'day' in request.params:
            selected += timedelta(days=int(request.params.getone('day'))-1)
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
        try:
            mylib=HSRLImageArchiveLibrarian(**{methodtype[3:]:methodkey})
        except RuntimeError:
            return HTTPNotFound(methodtype[3:] + "-" + methodkey + " is invalid")
#            return HTTPTemporaryRedirect(location=request.route_path("home"))
        if 'thumbtype' in request.matchdict and request.matchdict['thumbtype']!='all':
            subtypekey=request.matchdict['thumbtype']
        else:
            subtypekey=None
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
        elif monthno==nowtime.month and yearno==nowtime.year and subtypekey==None:
            dayno=nowtime.day
        else:
            dayno=1
        d=validdate(yearno,monthno,dayno,0,0)
        besttime=mylib.validClosestTime(d)
        return HTTPTemporaryRedirect(location=monthurlfor(request,methodtype,methodkey,subtypekey,besttime))
    #except:
    #return HTTPTemporaryRedirect(location=request.route_path("home"))        

def dayurlfor(req,atype,access,date):
    if date.hour<12:
        hour='am'
    else:
        hour='pm'
    return req.route_path('date',accesstype=atype,access=access,
                         year=date.year,month='%02i' % date.month,day='%02i' % date.day,ampm=hour)

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
        try:
            mylib=HSRLImageArchiveLibrarian(**{methodtype[3:]:methodkey})
        except RuntimeError:
            return HTTPNotFound(methodtype[3:] + "-" + methodkey + " is invalid")

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
        besttime=mylib.validClosestTime(datetime(yearno,monthno,dayno,hourno,0,0))
        return HTTPTemporaryRedirect(location=dayurlfor(request,methodtype,methodkey,besttime))
    except:
        return HTTPTemporaryRedirect(location=request.route_path('home'))

@view_config(route_name='home',renderer='templates/portaltemplate.pt')
def dplportal_view(request):
    return { 
        'lib':lib,
        'pagename':'HSRL Data Portal'
        }

@view_config(route_name='date',renderer='templates/datetemplate.pt')
def date_view(request):
    methodtype=request.matchdict['accesstype']
    methodkey=request.matchdict['access']
    try:
        mylib=HSRLImageArchiveLibrarian(**{methodtype[3:]:methodkey})
    except RuntimeError:
        return HTTPNotFound(methodtype[3:] + "-" + methodkey + " is invalid")
#        return HTTPTemporaryRedirect(location=request.route_path("home"))
    yearno=int(request.matchdict['year'])
    monthno=int(request.matchdict['month'])
    dayno=int(request.matchdict['day'])
    ampm=request.matchdict['ampm']
    hourno=-1
    ampm_range=None
    if ampm=='am':
        hourno=0
        ampm_range='00:00-12:00'
    elif ampm=='pm':
        hourno=12
        ampm_range='12:00-00:00'
    try:
        selectdate=datetime(yearno,monthno,dayno,hourno)
        #print selectdate
        realtime=mylib.validClosestTime(selectdate)
        #print realtime
        if realtime.date()!=selectdate.date() or realtime.hour!=hourno:
            return redirect_day(request)
    except ValueError, e:
        print e
        return redirect_day(request)
    return { 'lib':mylib,
        'calendar':calendar,'timedelta':timedelta,'datetime':datetime,
        'newmonthform':request.route_path("select_month"),'methodtype':methodtype,'methodkey':methodkey,
        'thistime':selectdate}
 

@view_config(route_name='month',renderer='templates/monthtemplate.pt')
@view_config(route_name='multiview',renderer='templates/monthtemplate.pt')
def month_view(request):
    methodtype=request.matchdict['accesstype']
    methodkey=request.matchdict['access']
    isMulti='thumbtype' not in request.matchdict or request.matchdict['thumbtype']=='all'
    try:
        mylib=HSRLImageArchiveLibrarian(**{methodtype[3:]:methodkey})
    except RuntimeError:
        return HTTPNotFound(methodtype[3:] + "-" + methodkey + " is invalid")
#        return HTTPTemporaryRedirect(location=request.route_path("home"))
    yearno=int(request.matchdict['year'])
    monthno=int(request.matchdict['month'])
    dayno=1
    if 'day' in request.matchdict:
        if not isMulti:
            return redirect_month(request)
        dayno=int(request.matchdict['day'])
    elif isMulti:
        return redirect_month(request)
    #datasetdesc=methodkey
    #imagedesc=subtypekey
    #print request.matched_route.__dict__.keys()
    try:
        thismonth=datetime(yearno,monthno,dayno)
        #print thismonth
        realtime=mylib.validClosestTime(thismonth)
        #print realtime
        if (isMulti and realtime.date()!=thismonth.date()) or (not isMulti and (realtime.year!=yearno or realtime.month!=monthno)):
            return redirect_month(request)
    except ValueError, e:
        print e
        return redirect_month(request)
    if not isMulti:#'thumbtype' in request.matchdict:
        selectedtype=request.matchdict['thumbtype']
    else:
        selectedtype=None
    return {'lib':mylib,
            'selectedtype':selectedtype,'methodtype':methodtype,'methodkey':methodkey,
            'thistime':thismonth,
            'calendar':calendar,'timedelta':timedelta,'datetime':datetime,
            'missingimageurl':request.static_path('picnic:static/missing_thumb.jpg'),
            'blankimageurl':request.static_path('picnic:static/blank_thumb.jpg')}
