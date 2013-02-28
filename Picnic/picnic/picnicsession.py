from pyramid.view import view_config
import os,sys
import json
from pyramid.httpexceptions import HTTPNotFound, HTTPTemporaryRedirect
from webob import Response
from datetime import datetime,timedelta
import time
import multiprocessing

json_dateformat='%Y.%m.%dT%H:%M:%S'

class PicnicTaskWrapper:
    def __init__(self,sessionid):
        self.__task=None
        self.expiretime=datetime.utcnow()
        self.__exitcode=None
        self.sessionid=sessionid

    #def __repr__(self):
    def __updatesession(self):
        tses=loadsession(self.sessionid)
        tses['rescode']=self.__exitcode
        storesession(tses)


    def new_task(self,sessionid,*args, **kwargs):
        self.terminate()
        self.sessionid=sessionid
        self.__task=multiprocessing.Process(*args, **kwargs)

    def is_alive(self):
        return self.__task!=None and self.__task.is_alive()

    def terminate(self):
        if self.is_alive():
            self.__task.terminate()
            self.__exitcode='terminated'
            self.__updatesession()

    def task(self):
        return self.__task

    def join(self):
        if self.is_alive():
            self.__task.join()
            self.exitcode()
            self.__task=None

    def start(self,*args, **kwargs):
        if self.__task==None:
            return None
        self.updateExpireTime(*args, **kwargs)
        return self.__task.start()

    def exitcode(self):
        if self.is_alive():
            self.__exitcode=None
        elif self.__task!=None:
            self.__exitcode=self.__task.exitcode
            self.__updatesession()
            self.__task=None
        return self.__exitcode

    def checkExpireTime(self,now=datetime.utcnow()):
        if self.expiretime<=now:
            self.terminate()

    def updateExpireTime(self,updateseconds=30,now=datetime.utcnow(),force_time=None):
        if force_time!=None:
            self.expiretime=force_time
        else:
            self.expiretime=now+timedelta(seconds=updateseconds)


tasks={}
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
    retry=5;
    ret=None
    while ret==None and retry>0:
        try:
            ret=json.load(file(sessionfile(sessionid,"session.json")))
        except:
            retry-=1
            time.sleep(.2)
    return ret

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
    logfilepath=sessionfile(sessionid,'logfile',create=True)
    if sessionid in tasks and tasks[sessionid].is_alive():
        print 'cancelling stale task for ',sessionid
        tasks[sessionid].terminate()
        tasks[sessionid].join()
    else:
        tasks[sessionid]=PicnicTaskWrapper(sessionid=sessionid)
    session['rescode']=''
    folder=_sessionfolder(sessionid)
    for s in os.listdir(folder):
        if s.startswith('.') or s=='logfile' or s.endswith('.json') or s.endswith('.nc'):
            continue
        os.unlink(safejoin(folder,s))
    stdt=file(logfilepath,'w')
    tasks[sessionid].new_task(sessionid=sessionid,target=taskdispatch,args=(dispatch,request,session,stdt))
    session['comment']='inited'
    session['logfileurl']= request.route_path('session_resource',session=sessionid,filename='logfile')
    dispatchers[dispatch](request,session,False)
    storesession(session)
    print 'starting task for ',sessionid, ' dispatch named ', dispatch
    tasks[sessionid].start(updateseconds=120)
    stdt.close()
    return HTTPTemporaryRedirect(location=makeUserCheckURL(request,request.route_path('progress_withid',session=sessionid)))

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
    print 'URLREQ: ',request.matched_route.name
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

    if sessionid in tasks and tasks[sessionid].is_alive():
        #load intermediate if not
        now=datetime.utcnow()
        tasks[sessionid].updateExpireTime(now=now)

        for sesid in tasks:
            if tasks[sesid].is_alive():
                tasks[sesid].checkExpireTime(now=now)

        return {'pagename':session['name'],'progresspage':request.route_path('progress_withid',session=sessionid),
            'sessionid':sessionid,'destination':session['finalpage'],'session':session}
    #load next page if complete
    if sessionid in tasks:
        rescode=tasks[sessionid].exitcode()
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
    _sess=os.listdir(folder)
    sess=[]
    for s in _sess:
        if s.startswith('.') or not os.path.isdir(safejoin(folder,s)):
            continue
        sess.append(s)
    sessinfo=[{'sessionid':n,'startTime':infoOfFile(safejoin(folder,n))[0],'running':tasks[n].is_alive() if n in tasks and tasks[n]!=None else False,'task':tasks[n].task() if n in tasks else None,'session':loadsession(n)} for n in sess]
    sessinfo.sort(key=itemgetter('startTime'),reverse=True)
    if 'purge' in request.params:
        purgefrom=request.params.getone('purge')
        found=False
        for inf in sessinfo:#(sessid,sdate,running,task) in sessinfo:
            if inf['sessionid']==purgefrom:
                found=True
                continue
            if found:
                sesf=_sessionfolder(inf['sessionid'])
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
        for inf in sessinfo:
            if inf['sessionid']==terminate:
                sessid=inf['sessionid']
                print 'will try to terminate ',sessid
                if sessid in tasks and tasks[sessid].is_alive():
                    tasks[sessid].terminate()
                    return HTTPTemporaryRedirect(location=request.route_path('status'))
                break
    runningtasks=0
    for ses in tasks:
            if tasks[ses].is_alive():
                runningtasks=runningtasks+1
            else:
                tasks[ses].exitcode()#update the session exitcode

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
    if sessionid in tasks:
        task=tasks[sessionid]
        running=task.is_alive()
        if not running:
            tses=loadsession(sessionid)
            if 'rescode' not in tses or tses['rescode']=='':
                tses['rescode']=task.exitcode()
                storesession(tses)
    else:
        task=None
        running=False
    if os.access(folder,os.R_OK):
        filelist=os.listdir(folder)
        filelist.sort()
        filelistinfo=[]
        for f in filelist:
            inf=infoOfFile(safejoin(folder,f))
            filelistinfo.append({'name':f,'stats':[inf[2],inf[0],inf[1]]})
    else:
        filelist=None
        filelistinfo=None
    if 'session.json' in filelist:
        session=loadsession(sessionid)
    else:
        session=None
    return {'task':task.task(),
            'files':filelist,
            'fileinfo':filelistinfo,
            'session':session,
            'running':running,
            'sessionid':sessionid}


def isValidEmailAddress(stringval):
    s=stringval.split('@')
    if len(s)!=2:
        return False
    return True

datacookiename="datauser"
keyfield="email"
reqfields=("email","name",)
optionalfields=("org",)
doHaveUserTracking=None

def haveUserTracking():
    global doHaveUserTracking
    if doHaveUserTracking==None:
        try:
            import cgi_datauser
            doHaveUserTracking=True
        except:
            doHaveUserTracking=False
    return doHaveUserTracking

def makeUserCheckURL(request,destination,destparms=None):#only works with a simple destination
    if not haveUserTracking():
        return destination
    returl=request.route_path('userCheck')+'?URL='+destination
    parms={}
    if destparms!=None:
        parms.update(destparms)
    for f in reqfields+optionalfields:
        if f in request.params:
            parms[f]=request.params.getone(f)
    if len(parms)>0:
        returl+='&' + '&'.join([(f+'='+parms[f]) for f in parms])
    return returl

@view_config(route_name='userCheck',renderer='templates/userCheck.pt')
def userCheck(request):
    print 'URLREQ: ',request.matched_route.name
    try:
        import cgi_datauser
    except:
        print "Couldn't load cgi_datauser from hsrl git codebase. user tracking disabled"
        parms=''
        jumpurl=''
        if "PARAMS" in request.params:
            parms='?'+request.params.getone('PARAMS')
        if len(parms)<=1:
            parms='?'+request.query_string#os.environ.get("QUERY_STRING","");
        if "URL" in request.params:
            jumpurl=request.params.getone('URL')
        if len(jumpurl)<=0:
            jumpurl='/'
            parms=''
        dest=jumpurl + parms
        return HTTPTemporaryRedirect(location=dest)
    dbc=cgi_datauser.lidarwebdb()
    info={};
    doForm=True
    fromSQL=False
    indebug=False #True
    if (keyfield in request.params and len(request.params.getone(keyfield))>0) or datacookiename in request.cookies or indebug:#fixme maybe not read cookie here, just grab from form
        doForm=False
        if keyfield in request.params and len(request.params.getone(keyfield))>0:
            if not isValidEmailAddress(request.params.getone(keyfield)):
                doForm=True
            else:
                info[keyfield]=request.params.getone(keyfield)
                hasreq=True;
                for f in reqfields:
                    if f in request.params and len(request.params.getone(f))>0:
                        info[f]=request.params.getone(f)
                    else:
                        hasreq=False
                for f in optionalfields:
                    if f in request.params and len(request.params.getone(f))>0:
                        info[f]=request.params.getone(f)
                if not hasreq:#work by lookup
                    ti=dbc.getUserByEMail(info[keyfield])
                    if ti:
                        info=ti
                        fromSQL=True
        elif datacookiename in request.cookies:
            ti=dbc.getUserByUID(request.cookies[datacookiename])
            if ti:
                info=ti
                fromSQL=True
        elif indebug: #DEBUG ONLY
            ti=dbc.getUserByEMail("null")
            if ti==None:
                dbc.addClient({'email':'null','name':'bubba'})
                ti=dbc.getUserByEMail("null")
            info=ti
            fromSQL=True
        for f in reqfields:
            if not info.has_key(f):
                doForm=True
                break
    if not doForm:
        if not fromSQL:
            uid=dbc.addClient(info)
        else:
            uid=info['uid']
        if uid!=None:
            parms=''
            jumpurl=''
            if "PARAMS" in request.params:
                parms='?'+request.params.getone('PARAMS')
            if len(parms)<=1:
                parms='?'+request.query_string#os.environ.get("QUERY_STRING","");
            if "URL" in request.params:
                jumpurl=request.params.getone('URL')
            if len(jumpurl)<=0:
                jumpurl='/'
                parms=''
            dest=jumpurl + parms
            if False and indebug:
                print "Content-Type: text/plain"
                print
                if len(cookies)>0:
                    print cookies
                else:
                    print "No cookies"
                print "jump to %s" % dest
            else:
                bod="""
                <HTML><HEAD>
                <META HTTP-EQUIV="Refresh" CONTENT="0;url=%s">
                <TITLE>Registered</TITLE>
                </HEAD><BODY></BODY></HTML>
               """  % dest
            resp = Response(body=bod,content_type="text/html")
            resp.set_cookie(datacookiename,uid,max_age=timedelta(weeks=12))
            return resp
    #form
    #info=dbc.getUserByEMail("null")
    #print "Content-Type: text/html"
    #if len(cookies)>0:
    #    print cookies
    #print
    if "URL" in request.params:
        info["URL"]=request.params.getone('URL')
    else:
        info["URL"]=""
    info["PARAMS"]=request.query_string#os.environ.get("QUERY_STRING","")
    info["MYURL"]=request.path#os.environ.get("SCRIPT_NAME","")

    fields=("email","name","org");
    fielddesc={"email":"E-Mail Address",
               "name":"Name",
               "org":"Organization"}

    return { 'MYURL': info['MYURL'],
             'URL': info['URL'],
             'PARAMS': info['PARAMS'],
             'fields': fields,
             'info': info,
             'fielddesc': fielddesc,
             'reqfields': reqfields}
