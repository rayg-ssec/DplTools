from pyramid.view import view_config
import json
from multiprocessing import Process,Queue
from pyramid.httpexceptions import HTTPBadRequest
import copy

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

def sortList(x):
    y=copy.deepcopy(x)
    y.sort()
    return y

@view_config(route_name='imagecustom',renderer='templates/imagecustom.pt')
def imagecustom(request):
    #print 'URLREQ: ',request.matched_route.name
    try:
        if 'source' in request.params and len(request.parms.getone('source'))>0:
            content=json.loads(request.params.getone('source'))
        else:
            fn='all_plots.json'
            if 'file' in request.params:
                fn=request.params.getone('file')
            content=json.load(open(safe_locate_file(fn),'r'))        
    except:
        return HTTPBadRequest()
    ret={}
    ret['sort']=sortList
    ret['subpath']=request.params.getone('subpath').split(',') if 'subpath' in request.params else 'display_defaults'
    prefixes=[]
    for f in range(0,len(ret['subpath'])):
        if f==0:
            prefixes.append('json')
        else:
            prefixes.append('json%i' % f)
    ret['jsonprefix']=prefixes
    #ret['file']=fn
    ret['original_content']=json.dumps(content, separators=(',',':'))
    bases={}
    for f in range(0,len(ret['subpath'])):
        ret[ret['jsonprefix'][f]] = content if len(ret['subpath'])==0 else content[ret['subpath'][f]]
        bases[ret['jsonprefix'][f]]= content if len(ret['subpath'])==0 else content[ret['subpath'][f]]
    ret['bases']=bases
    return ret #loadMeta(ret,'json','meta')

def getarrval(a,s):
    if s==None or len(s)==0:
        return a
    if isinstance(s,basestring):
        l=len(s)
        elements=[int(x) for x in s[1:(l-1)].split('][')]
        return getarrval(a,elements)
    else:
        if len(s)==1:
            return a[s[0]]
        return getarrval(a[s[0]],s[1:])

def setarrval(a,s,v):
    if s==None or len(s)==0:
        return a
    if isinstance(s,basestring):
        l=len(s)
        elements=[int(x) for x in s[1:(l-1)].split('][')]
        return setarrval(a,elements,v)
    else:
        if len(s)==1:
            if v!=None:
                a[s[0]]=v
            else:
                return a[s[0]]
        return setarrval(a[s[0]],s[1:],v)

def getdictval(d,ks):
    idxs=None
    if '[' in ks[0]:
        idxs=ks[0][ks[0].find('['):]
        ks[0]=ks[0][0:ks[0].find('[')]
    if ks[0] not in d:
        return None
    if len(ks)==1:
        return getarrval(d[ks[0]],idxs)
    return getdictval(getarrval(d[ks[0]],idxs),ks[1:])

def setdictval(d,ks,v):
    if len(ks)==1:
        if '[' in ks[0]:
            newks=ks[0][0:ks[0].find('[')]
            idxs=ks[0][ks[0].find('['):]
            if newks not in d:
                d[newks]=[]
            return setarrval(d[newks],idxs,v)
        else:
            d[ks[0]]=v
            return d
    if '[' in ks[0]:
        idxs=ks[0][ks[0].find('['):]
        ks[0]=ks[0][0:ks[0].find('[')]
    else:
        idxs=None
    if ks[0] not in d:
        if idxs==None:
            d[ks[0]]={}
        else:
            d[ks[0]]=[]
    setdictval(setarrval(d[ks[0]],idxs,None),ks[1:],v)

def oneleveldict(sd,dd={},ks=[]):
    if type(sd) not in (dict,list):
        dd['.'.join(ks)]=sd
        return dd
    if type(sd)==dict:
        for k in sd:
            oneleveldict(sd[k],dd,ks+[k])
    elif type(sd)==list:
        tmpks=copy.deepcopy(ks);
        for k in range(0,len(sd)):
            tmpks[-1]=ks[-1]+('[%i]' % k)
            #print tmpks
            oneleveldict(sd[k],dd,tmpks)
    return dd

def meta(d):
    if type(d) not in (dict,list):
        return '%s' % (type(d).__name__)
    if type(d)==dict:
        ret={}
        for x in d:
            ret[x]=meta(d[x])
    elif type(d)==list:
        ret=[]
        for x in d:
            ret.append(meta(x))
    return ret

def loadMeta(d,pref,mpref):
    ret={}
    ret[pref]=copy.deepcopy(d)
    ret[mpref]=meta(d)
    ret['jsonprefix']=pref
    ret['metaprefix']=mpref
    return ret

@view_config(route_name='generatejson',renderer='json')
def generatejson(request):
    try:
        if 'original_content' in request.params:
            sidedo=json.loads(request.params.getone('original_content'))
        else:
            fn=request.params.getone('file')
            sidedo=json.load(open(safe_locate_file(fn),'r'))
    except:
        return HTTPBadRequest()

    #print request.params
    if 'jsonprefix' not in request.params:
        return sidedo

    prefixes=request.params.getone('jsonprefix').split(',')
    subpaths=request.params.getone('subpath').split(',')
    for pidx in range(0,len(prefixes)):
        pref=prefixes[pidx]#request.params.getone('jsonprefix')
        subpath=subpaths[pidx]#request.params.getone('subpath')
        metpref='meta'
        sided=oneleveldict(loadMeta(sidedo if len(subpath)==0 else sidedo[subpath],pref,metpref))
        res={}
        res[pref]=sidedo if len(subpath)==0 else sidedo[subpath]
        allkeys=request.params.keys()
        mk=sided.keys()
        mk.sort()
        for f in mk:
            if not f.startswith(pref+'.'):
                continue
            if f not in allkeys:
                allkeys.append(f)
                #print 'added ',f
        for f in allkeys:
            if not f.startswith(pref + '.'):
                #print f,"doesn't start with",pref
                continue
            k=f
            ks=k.split('.')
            if 'doc' in ks or 'docs' in ks or 'documentation' in ks or 'parameters' in ks:
                continue
            if f not in request.params:
                if ks[-1]=='enable':
                    v='0'#special dumb case
                    #print k,'is being set to false'
                else:
                    print k,"wasn't in the form"
                    continue
            else:
                v=request.params.getone(f)
            metkey=metpref + f[len(pref):]
            if metkey in sided:
                tp=sided[metkey]
                if tp not in ['int','float','str','unicode']:
                    print tp
                if v.lower() in ['on','off','true','false','yes','no'] and tp=='int':
                    if v.lower() in ['on','true']:
                        v=1
                    else:
                        v=0
                else:
                    v=eval(tp+'(v)')
            #print 'setting value'
            #print ks
            if getdictval(res,ks)==v:
                continue
            print 'changing ',ks,'was',getdictval(res,ks),', setting to',v
            #print v
            setdictval(res,ks,v)
            #print res
        if len(subpath)==0:
            sidedo=res[pref]
        else:
            sidedo[subpath]=res[pref]
    return sidedo
