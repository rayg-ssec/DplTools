from pyramid.view import view_config
import json
from multiprocessing import Process,Queue

def _back_locate_file(fn,q):
    try:
        from hsrl.utils.locate_file import locate_file
        ret=locate_file(fn)
        q.put(ret)
    except Exception, e:
        q.put(e)



def safe_locate_file(fn):
    Q=Queue()
    p=Process(target=_back_locate_file,args=(fn,Q))
    #print 'Checking availability for ',datasets,starttime,endtime,datetime.utcnow()
    p.start()
    retval=Q.get()
    #print retval,datetime.utcnow()
    p.join()
    if isinstance(retval,basestring):
        return retval
    raise retval


@view_config(route_name='imagecustom',renderer='templates/imagecustom.pt')
def imagecustom(request):
    #print 'URLREQ: ',request.matched_route.name
    if 'source' in request.params:
        content=json.loads(request.params.getone('source'))
    else:
        fn='all_plots.json'
        if 'display_defaults_file' in request.params:
            fn=request.params.getone('display_defaults_file')
            if os.path.sep in fn:
                fn=picnicsession.sessionfile(sessionid,sessiondict['display_defaults_file'])
        content=json.load(open(safe_locate_file(fn),'r'))        
    ret={}
    ret['jsonprefix']='json'
    #ret['file']=fn
    ret['original_content']=json.dumps(content, separators=(',',':'))
    ret['subpath']='display_defaults'
    ret[ret['jsonprefix']] = content[ret['subpath']]
    return ret #loadMeta(ret,'json','meta')

def setdictval(d,ks,v):
    if len(ks)==1:
        d[ks[0]]=v
        return d
    if ks[0] not in d:
        d[ks[0]]={}
    setdictval(d[ks[0]],ks[1:],v)

def oneleveldict(sd,dd={},ks=[]):
    if type(sd) is not type({}):
        dd['.'.join(ks)]=sd
        return dd
    for k in sd:
        oneleveldict(sd[k],dd,ks+[k])
    return dd

def meta(d):
    ret={}
    if type(d) is not type(ret):
        return '%s' % (type(d).__name__)
    for x in d:
        ret[x]=meta(d[x])
    return ret

def loadMeta(d,pref,mpref):
    ret={}
    ret[pref]=d
    ret[mpref]=meta(d)
    ret['jsonprefix']=pref
    ret['metaprefix']=mpref
    return ret

@view_config(route_name='generatejson',renderer='json')
def generatejson(request):
    if 'original_content' in request.params:
        sidedo=json.loads(request.params.getone('original_content'))
    else:
        fn=request.params.getone('file')
        sidedo=json.load(open(safe_locate_file(fn),'r'))
    if 'jsonprefix' in request.params: 
        pref=request.params.getone('jsonprefix')
        subpath=request.params.getone('subpath')
        metpref='meta'
        sided=oneleveldict(loadMeta(sidedo[subpath],pref,metpref))
        res={}
        res[pref]=sidedo[subpath]
        for f in request.params:
            if not f.startswith(pref + '.'):
                continue
            k=f
            ks=k.split('.')
            v=request.params.getone(f)
            metkey=metpref + f[len(pref):]
            if metkey in sided:
                tp=sided[metkey]
                if tp not in ['int','float']:
                    print tp
                if v.lower() in ['on','off','true','false'] and tp=='int':
                    if v.lower() in ['on','true']:
                        v=1
                    else:
                        v=0
                else:
                    v=eval(tp+'(v)')
            #print 'setting value'
            #print ks
            #print v
            setdictval(res,ks,v)
            #print res
        sidedo[subpath]=res[pref]
    return sidedo
