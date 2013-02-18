from pyramid.view import view_config
import os,sys
import json
from pyramid.httpexceptions import HTTPNotFound, HTTPTemporaryRedirect
from webob import Response
from datetime import datetime
import time
import multiprocessing

json_dateformat='%Y.%m.%dT%H:%M:%S'

tasks={}
taskupdatetimes={}
#imagepathcacheage=None

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


# requests take 4 stages:
# - fork/dispatch: sets up session, logfile, forks, and calls specific function
# - parse parameters
# - construct DPL
# - execute

dispatched=False
dispatchers={}

def addDispatchers(d):
    dispatchers.update(d)

def taskdispatch(dispatcher,request,session,logstream=None):
    if logstream!=None:
        os.dup2(logstream.fileno(),sys.stdout.fileno())
        os.dup2(logstream.fileno(),sys.stderr.fileno())
    updateSessionComment(session,'dispatching')
    dispatchers[dispatcher](request,session,isBackground=(None if logstream==None else True))
 
def sessionfile(sessionid,filename,create=False):
    if not isinstance(sessionid,basestring):
        sessionid = sessionid['sessionid']
    fold=_sessionfolder(sessionid)
    if filename==None:
        return fold
    if create and not os.access(fold,os.R_OK):
        os.mkdir(fold)
    return safejoin(fold,filename)

def _sessionfolder(sessionid):
    if sessionid==None:
        return safejoin('.','sessions')
    return safejoin('.','sessions',sessionid);

def loadsession(sessionid):
    return json.load(file(sessionfile(sessionid,"session.json")))

def storesession(session):
    json.dump(session,file(sessionfile(session['sessionid'],'session.json',create=True),'w'),indent=4,separators=(',', ': '))


def updateSessionComment(sessionid,value):
    if isinstance(sessionid,basestring):
        print 'WARNING: Loading session, rather than using session directly'
        session = loadsession(sessionid)
    else:
        session = sessionid
    session['comment']=value
    print datetime.utcnow(),' Updating Session Comment :',value
    storesession(session)

def newSessionProcess(dispatch,request,session):
    sessionid=session['sessionid']
    taskupdatetimes[sessionid]=datetime.utcnow()
    logfilepath=sessionfile(sessionid,'logfile',create=True)
    stdt=file(logfilepath,'w')
    tasks[sessionid]=multiprocessing.Process(target=taskdispatch,args=(dispatch,request,session,stdt))
    session['comment']='inited'
    session['logfileurl']= request.route_path('session_resource',session=sessionid,filename='logfile')
    dispatchers[dispatch](request,session,False)
    storesession(session)
    print 'starting task for ',sessionid, ' dispatch named ', dispatch
    tasks[sessionid].start()
    stdt.close()
  

def moddateoffile(f):
    return os.stat(f).st_mtime

@view_config(route_name='session_resource')
def session_resource(request):
    fn=request.matchdict['filename']
    if 'session' in request.matchdict:
        f=sessionfile(request.matchdict['session'],fn)
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
    session=None
    retry=10
    while session==None and retry>0:
        try:
            session=loadsession(sessionid)
        except:
            time.sleep(.05)
            session=None
            retry=retry-1
    if session==None:
        return HTTPTemporaryRedirect(location=request.route_path('progress_withid',session=sessionid))

    if sessionid in tasks and tasks[sessionid]!=None and tasks[sessionid].is_alive():
        #load intermediate if not
        nowtime=datetime.utcnow()
        taskupdatetimes[sessionid]=nowtime

        for sesid in tasks:
            if tasks[sesid]!=None and tasks[sesid].is_alive() and (nowtime-taskupdatetimes[sesid]).total_seconds()>60.0:
                tasks[sesid].terminate()
                print 'terminated task for ',sesid

        return {'pagename':session['name'],'progresspage':request.route_path('progress_withid',session=sessionid),
            'sessionid':sessionid,'destination':session['finalpage'],'session':session}
    #load next page if complete
    if sessionid in tasks and tasks[sessionid]!=None:
        rescode=tasks[sessionid].exitcode
    else:
        rescode='unknown (old task)'
    print 'finished task for ',sessionid, ' with result code ', rescode
    return HTTPTemporaryRedirect(location=session['finalpage'])


#### STATUS bits

def infoOfFile(fn):
    tmp=os.stat(fn)
    return (datetime.utcfromtimestamp(tmp.st_ctime),datetime.utcfromtimestamp(tmp.st_mtime),tmp.st_size)

from operator import itemgetter
            
@view_config(route_name='status',renderer='templates/status.pt')
def statuspage(request):
    folder=_sessionfolder(None)#safejoin('.','sessions');
    sess=os.listdir(folder)
    sessinfo=[(n,infoOfFile(safejoin(folder,n))[0],tasks[n].is_alive() if n in tasks and tasks[n]!=None else False,tasks[n] if n in tasks else None) for n in sess]
    sessinfo.sort(key=itemgetter(1),reverse=True)
    if 'purge' in request.params:
        purgefrom=request.params.getone('purge')
        found=False
        for (sessid,sdate,running,task) in sessinfo:
            if sessid==purgefrom:
                found=True
                continue
            if found:
                sesf=_sessionfolder(sessid)
                fs=os.listdir(sesf)
                for f in fs:
                    os.unlink(safejoin(sesf,f))
                    print 'unlinked ',safejoin(sesf,f)
                os.rmdir(sesf)
                print 'unlinked ',sesf
        if found:
            return HTTPTemporaryRedirect(location=request.route_path('status'))
    if 'terminate' in request.params:
        terminate=request.params.getone('terminate')
        found=False
        for (sessid,sdate,running,task) in sessinfo:
            if sessid==terminate:
                print 'will try to terminate ',sessid
                if sessid in tasks and tasks[sessid] and tasks[sessid].is_alive():
                    tasks[sessid].terminate()
                    return HTTPTemporaryRedirect(location=request.route_path('status'))
                break
    runningtasks=0
    for ses in tasks:
        if tasks[ses]!=None and tasks[ses].is_alive():
            runningtasks=runningtasks+1
    return {'sessions':sess,
            'sessioninfo':sessinfo,
            'runningtasks':runningtasks,
            'datetime':datetime,'timedelta':timedelta}

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
    folder=_sessionfolder(sessionid);
    session=loadsession(sessionid)
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
        session=loadsession(sessionid)
    else:
        session=None
    return {'task':task,
            'files':filelist,
            'fileinfo':filelistinfo,
            'session':session,
            'running':running,
            'sessionid':sessionid}

