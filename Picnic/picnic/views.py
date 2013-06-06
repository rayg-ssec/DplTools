from pyramid.view import view_config
from datetime import datetime,timedelta
from pyramid.httpexceptions import HTTPNotFound, HTTPTemporaryRedirect
from webob import Response
import os
import calendar
import picnicsession
import jsgen
from multiprocessing import Process,Queue
import json
import time
import traceback
import logging
log = logging.getLogger(__name__)
import server_archive


from timeutils import validdate

from HSRLImageArchiveLibrarian import HSRLImageArchiveLibrarian
lib=HSRLImageArchiveLibrarian(indexdefault='site')

def sessionUrls(request,sessionid,extensions):
    try:
        fl=os.listdir(picnicsession.sessionfile(sessionid,None))
        fl.sort()
    except:
        return
    for f in fl:
        for e in extensions:
            if f.endswith(e):
                yield {'url':request.route_path('session_resource',session=sessionid,filename=f),'name':f}
                break

@view_config(route_name='imageresult',renderer='templates/imageresult.pt')
def imageresult(request):
    #print 'URLREQ: ',request.matched_route.name
    sessionid=request.matchdict['session']#request.session.get_csrf_token();#params.getone('csrf_token')
    #folder=picnicsession.sessionfolder(sessionid);
    #sessiontask=tasks[sessionid]
    #session=sessiontask['session']
    #scan session folder for images
    session=picnicsession.loadsession(sessionid)

    if 'starttime' in session:
        session['starttime']=datetime.strptime(session['starttime'],picnicsession.json_dateformat)
    if 'endtime' in session:
        session['endtime']=datetime.strptime(session['endtime'],picnicsession.json_dateformat)
    #send to template
    return { 'imageurls':sessionUrls(request,sessionid,('.png','.jpg')) , 'plainurls':sessionUrls(request,sessionid,('.json','.cdl')), 'session':session, 'timedelta':timedelta } 

@view_config(route_name='netcdfresult',renderer='templates/netcdfresult.pt')
def netcdfresult(request):
    #print 'URLREQ: ',request.matched_route.name
    sessionid=request.matchdict['session']#request.session.get_csrf_token();#params.getone('csrf_token')
    #folder=picnicsession.sessionfolder(sessionid);
    #sessiontask=tasks[sessionid]
    #session=sessiontask['session']
    #scan session folder for images
    session=picnicsession.loadsession(sessionid)

    if 'starttime' in session:
        session['starttime']=datetime.strptime(session['starttime'],picnicsession.json_dateformat)
    if 'endtime' in session:
        session['endtime']=datetime.strptime(session['endtime'],picnicsession.json_dateformat)
    fullfilename=picnicsession.sessionfile(sessionid,session['filename'])#safejoin(folder,session['filename'])
    try:
        from netCDF4 import Dataset
        nc=Dataset(fullfilename,'r')
        inf=picnicsession.infoOfFile(fullfilename)
        e=None
    except Exception, err:
        nc=None
        inf=[None,None,0,None]
        e=err
    if nc==None:
        print nc
        print 'Failed to open netcdf dataset'
        print err
    #print file(safejoin(folder,'logfile')).read()
    #send to template
    return { 'imageurls':sessionUrls(request,sessionid,('.png','.jpg')), 'plainurls':sessionUrls(request,sessionid,('.json','.cdl')), 'session':session,
        'datetime':datetime, 'timedelta':timedelta, 'nc':nc ,'info':inf, 'printNumber':picnicsession.printNumber}

@view_config(route_name='multinetcdfresult',renderer='templates/multinetcdfresult.pt')
def multinetcdfresult(request):
    #print 'URLREQ: ',request.matched_route.name
    sessionid=request.matchdict['session']#request.session.get_csrf_token();#params.getone('csrf_token')
    #folder=picnicsession.sessionfolder(sessionid);
    #sessiontask=tasks[sessionid]
    #session=sessiontask['session']
    #scan session folder for images
    session=picnicsession.loadsession(sessionid)

    if 'starttime' in session:
        session['starttime']=datetime.strptime(session['starttime'],picnicsession.json_dateformat)
    if 'endtime' in session:
        session['endtime']=datetime.strptime(session['endtime'],picnicsession.json_dateformat)

    return { 'plainurls':sessionUrls(request,sessionid,('.json','.cdl')), 'session':session,
        'datetime':datetime, 'timedelta':timedelta, 'printNumber':picnicsession.printNumber, 'sessionActive':picnicsession.sessionActive(session)}



@view_config(route_name='imagereq')
def imagerequest(request):
    #print 'URLREQ: ',request.matched_route.name
    session=request.session
    sessionid=session.new_csrf_token()
    sessiondict={}
    if 'loadedsession' in request.params:
        print 'loading session for id',sessionid
        sessiondict=request.params.getone('loadedsession',None)
    sessiondict['sessionid']=sessionid
    sessiondict['finalpage']=request.route_path('imageresult',session=sessionid);
    return picnicsession.newSessionProcess("newimages",request,sessiondict)

@view_config(route_name='reimagereq')
def reimagerequest(request):
    #print 'URLREQ: ',request.matched_route.name
    sessionid=request.matchdict['session']#request.session.get_csrf_token();#params.getone('csrf_token')
    #folder=picnicsession.sessionfolder(sessionid);
    session=picnicsession.loadsession(sessionid)
    if True:
        oldsessionid=sessionid
        pysession=request.session
        sessionid=pysession.new_csrf_token()
        session['sessionid']=sessionid
        session['finalpage']=request.route_path('imageresult',session=sessionid);
        for f in ('display_parameters.json','process_parameters.json'):
            picnicsession.storejson(sessionid,picnicsession.loadjson(oldsessionid,f),f)
    return picnicsession.newSessionProcess("createimages",request,session)
   

@view_config(route_name='netcdfreimage')
def netcdfreimage(request):
    #print 'URLREQ: ',request.matched_route.name
    sessionid=request.matchdict['session']#request.session.get_csrf_token();#params.getone('csrf_token')
    #folder=picnicsession.sessionfolder(sessionid);
    session=picnicsession.loadsession(sessionid)
    return picnicsession.newSessionProcess("readnetcdf",request,session)
 

@view_config(route_name='netcdfreq')
def netcdfrequest(request):
    #print 'URLREQ: ',request.matched_route.name
    session=request.session
    sessionid=session.new_csrf_token()
    sessiondict={}
    sessiondict['sessionid']=sessionid
    if request.params.getone('filemode')=='single':
        sessiondict['finalpage']=request.route_path('netcdfresult',session=sessionid);
        return picnicsession.newSessionProcess("newnetcdf",request,sessiondict)
    sessiondict['finalpage']=request.route_path('multinetcdfresult',session=sessionid);
    picnicsession.newSessionProcess("newmultinetcdf",request,sessiondict,force_time=datetime.utcnow()+timedelta(days=1))
    time.sleep(1)
    return HTTPTemporaryRedirect(location=sessiondict['finalpage'])

def dataAvailabilityBack(Q,datasets,mode,modeval,starttime,endtime):
    """ called from javascript """
    ret=[]
    try:
      log.debug('dataAvailabilityBack: time range (%s to %s)' ,repr(starttime),repr(endtime) )
      if 'lidar' in datasets:
        times=[]
        fn=None
        t=None

        from hsrl.dpl_netcdf.HSRLLibrarian import HSRLLibrarian
        datalib=HSRLLibrarian(**{mode:modeval})
        srchres=datalib(start=starttime,end=endtime)
        for x in srchres:
            times.append(srchres.parseTimeFromFile(x))
            if len(times)==2:
                break
            fn=x
            t=times[0]

        success=False
        if len(times)==0:
            success=False
            print 'no data'
        elif len(times)>=2:
            success=True
            print 'more than 1'
        elif t>=starttime and t<=endtime:
            success=True
            print 'time in range'
        elif starttime>datetime.utcnow():
            success=False
        elif 'data' in x and (starttime-t).total_seconds()<(60*60):
            success=True
            print 'data time may intersect'
        elif 'data' not in x and (starttime-t).total_seconds()<(3*60*60):
            success=True
            print 'cal time may intersect'

        if success:
            ret.append("lidar")
    except RuntimeError, e:
        print e
        print traceback.format_exc()      
        print 'exception while looking for data availability'
        pass
    Q.put(ret)

@view_config(route_name='dataAvailability')
def dataAvailability(request):
    #site=request.params.getone('site')
    starttime=request.params.getone('time0')
    endtime=request.params.getone('time1')
    srctypes=['site','dataset','instrument'] 
    mode = None
    for srctype in srctypes:
        if srctype in request.params:
            mode=srctype
            modeval=request.params.getone(mode)
            break
    if mode == None:
        return HTTPNotFound('unknown data storage search method')
    datasets=[]
    if 'datasets' in request.params:
        datasets.extend(request.params.getone('datasets').split(','))
    else:
        try:
            instruments=lib(**{mode:modeval})['Instruments']
            for inst in instruments:
                datasets.extend(lib.instrument(inst)['datasets'])
        except RuntimeError:
            return HTTPNotFound("unknown data storage search method 2")
    starttime=datetime.strptime(starttime[:4] + '.' + starttime[4:],'%Y.%m%dT%H%M')#some OSes strptime don't assue %Y consumes 4 characters
    endtime=datetime.strptime(endtime[:4] + '.' + endtime[4:],'%Y.%m%dT%H%M')
    Q=Queue()
    if True:
      p=Process(target=dataAvailabilityBack,args=(Q,datasets,mode,modeval,starttime,endtime))
      #print 'Checking availability for ',datasets,starttime,endtime,datetime.utcnow()
      p.start()
      retval=Q.get()
      #print retval,datetime.utcnow()
      p.join()
    else:
      dataAvailabilityBack(Q,datasets,mode,modeval,starttime,endtime)
      retval=Q.get()
      
    #print datetime.utcnow()

        #print "Success = " , success
    # if other sets, add checks here using librarians
    #print 'data availability check for ' , mode, '-', modeval, ' src = ', datasets, ' , result = ', retval
    
    response=request.response
    response.content_type='text/plain'
       
    response.body=','.join(retval)
    return response

@view_config(route_name='logbook')
def logbook(request):
    methodtype=request.matchdict['accesstype']
    methodkey=request.matchdict['access']
    try:
        datasetid=lib('dataset',lib(**{methodtype:methodkey})['Instruments'][0])['DatasetID']
    except RuntimeError:
        return HTTPNotFound(methodtype + "-" + methodkey + " is invalid")
#        return HTTPTemporaryRedirect(location=request.route_path("home"))
    parms={'dataset':'%i' % datasetid}
    for f in ['byr','bmo','bdy','bhr','bmn','eyr','emo','edy','ehr','emn','rss']:
        if f in request.params:
            parms[f]=request.params.getone(f)
    return HTTPTemporaryRedirect(location='http://lidar.ssec.wisc.edu/cgi-bin/logbook/showlogbook.cgi?'+'&'.join([(k + '=' + parms[k]) for k in parms.keys()]))


class idxholder:
    def __init__(self):
        self.ctr=0

    def increment(self):
        self.ctr+=1

    def value(self):
        return self.ctr

    def __repr__(self):
        return '%i' % self.value()

def setGen(sets,startid,count,cid=None):
    if cid==None:
        cid=idxholder()
        toplayer=False
    else:
        toplayer=False
    for s in sets:
        if 'disabled' in s and s['disabled']!=0:
            continue
        if 'sets' not in s:
            #print 'singleton set',sets['name'],startid,count,cid
            if cid.value()>=startid and cid.value()<(startid+count):
                if toplayer:
                    print startid,count,cid,s['name']
                yield (s,)
            cid.increment()
        else:
            for ss in setGen(s['sets'],startid,count,cid):
                if toplayer:
                    print startid,count,cid,s['name'],tuple([x['name'] for x in ss])
                #print 'returning iterated set',sets['name'],(s['name'],)+ss,startid,count,cid
                yield (s,)+ss


def setCount(sets):
    return len(tuple(setGen(sets,0,100)))

@view_config(route_name='netcdfgen',renderer='templates/netcdfrequest.pt')
@view_config(route_name='imagegen',renderer='templates/imagerequest.pt')
def form_view(request):
    #print 'URLREQ: ',request.matched_route.name
    methodtype=request.matchdict['accesstype']
    methodkey=request.matchdict['access']
    try:
        mylib=HSRLImageArchiveLibrarian(**{methodtype:methodkey})
    except RuntimeError:
        return HTTPNotFound(methodtype + "-" + methodkey + " is invalid")
#        return HTTPTemporaryRedirect(location=request.route_path("home"))
    st=mylib()
    instruments=st['Instruments']
    instcount=len(instruments)
    name=st['Name']
    datasets=[]
    for inst in instruments:
        datasets.extend(lib.instrument(inst)['datasets'])

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
        lasttime=mylib.validClosestTime(datetime.utcnow())
        endtime=validdate(lasttime.year,lasttime.month,lasttime.day,lasttime.hour,lasttime.minute-(lasttime.minute%5))
        starttime=validdate(endtime.year,endtime.month,endtime.day,endtime.hour-2,endtime.minute)

    oldformparmsdict={methodtype:methodkey, 'forcematlab':'yes',
                      'byr':'%i' % starttime.year,
                      'bmo':'%i' % starttime.month,
                      'bdy':'%i' % starttime.day,
                      'bhr':'%i' % starttime.hour,
                      'bmn':'%i' % starttime.minute,
                      'eyr':'%i' % endtime.year,
                      'emo':'%i' % endtime.month,
                      'edy':'%i' % endtime.day,
                      'ehr':'%i' % endtime.hour,
                      'emn':'%i' % endtime.minute,
                      'minalt':'%i' % minalt,'maxalt':'%i' % maxalt}
    oldformparams='&'.join((k+'='+oldformparmsdict[k]) for k in oldformparmsdict.keys())
    #print oldformparams

    if request.matched_route.name=='netcdfgen':
        oldurl="http://lidar.ssec.wisc.edu/cgi-bin/processeddata/retrievedata.cgi?%s" % (oldformparams)
    if request.matched_route.name=='imagegen':
        oldurl="http://lidar.ssec.wisc.edu/cgi-bin/ahsrldisplay/requestfigs.cgi?%s" % (oldformparams)
    if False:#instcount>3 :#more than just HSRL. python doesn't support it yet
        return HTTPTemporaryRedirect(location=oldurl)


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
            'edate':endtime,'calendar':calendar,'timedelta':timedelta,'datetime':datetime,
            'altrange':[minalt,maxalt],'alts':alts,
            'timeresvals':timeresvals,'altresvals':altresvals,
            'timeres':timeres,'altres':altres,
            'imagesets':jsgen.formsetsForInstruments(datasets,'images'),
            'netcdfsets':jsgen.formsetsForInstruments(datasets,'netcdf'),
            'datasets':datasets,'method':methodtype,methodtype:methodkey,
            'oldurl':oldurl,
            'netcdfdestinationurl':request.route_url('netcdfreq',_host=hosttouse,_port=porttouse),
            'imagedestinationurl':request.route_url('imagereq',_host=hosttouse,_port=porttouse),
            'cdltemplates':{
                "hsrl_nomenclature.cdl":"UW HSRL(NetCDF4)",
                "hsrl_cfradial.cdl":"NCAR CFRadial",
                "hsrl3_processed.cdl":"UW Processed (NetCDF3)",
                "hsrl3_raw.cdl":"UW Raw (NetCDF3)",
                "custom":"User Provided:"
            },
            'cdltemplateorder':[ "hsrl_nomenclature.cdl","hsrl_cfradial.cdl","hsrl3_processed.cdl","hsrl3_raw.cdl","custom"],
            'userTracking':picnicsession.haveUserTracking(),
            #'usercheckurl':request.route_path('userCheck'),#'http://lidar.ssec.wisc.edu/cgi-bin/util/userCheck.cgi',
            'dataAvailabilityURL':request.route_path('dataAvailability'),
            'sitename':name,'setCount':setCount,'setGen':setGen,'make_archived_widget':server_archive.make_archived_widget,'archived_widget_head':server_archive.archived_widget_head}
