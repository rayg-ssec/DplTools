from pyramid.view import view_config

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
    fn=request.params.getone('file')
    from hsrl.utils.locate_file import locate_file
    sidedo=json.load(open(locate_file(fn),'r'))
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
