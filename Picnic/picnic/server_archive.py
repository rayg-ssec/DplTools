import locking
from pyramid.view import view_config
from datetime import timedelta,datetime
import json
import bz2 as compressor
import base64
import hashlib
import os
from pyramid.httpexceptions import HTTPNotFound, HTTPTemporaryRedirect


archivecookie='archive_list'
archivepath=os.getenv('SERVERSIDE_ARCHIVEPATH','./serverarchive')
_catalog_lock = None

def catalog_lock():
    global _catalog_lock
    if _catalog_lock==None:
        try:
            _catalog_lock = locking.SharedRWLock(os.path.join(archivepath,'archive.json'))
        except:
            print "Path %s doesn't exist" % (archivepath)
            raise
    return _catalog_lock


def _get_archive_dictionary(request):
    #get cookie
    if archivecookie not in request.cookies:
        return {}
    asciicompr=request.cookies[archivecookie]
    if asciicompr[0]=='{':
        strval=asciicompr
    else:
        compr=base64.b64decode(asciicompr)
        #decompress
        strval=compressor.decompress(compr)
    #parse
    return json.loads(strval)

def _set_archive_dictionary(request,d):
    #dump to string
    strval=json.dumps(d, separators=(',',':'))
    #compress
    compr=compressor.compress(strval)
    asciicompr=base64.b64encode(compr)
    #store as cookie
    print 'compressed value:',asciicompr
    print 'ascii value',strval
    if len(strval)<len(asciicompr):
        cval=strval
    else:
        cval=asciicompr
    print 'Cookie has length %s (from %s)' % (len(cval),'ascii' if cval==strval else 'compressed')
    request.response.set_cookie(archivecookie,cval,max_age=timedelta(weeks=12))

def _get_archive_catalog():#ro
    try:
        return json.load(file(os.path.join(archivepath,'archive.json'),'r'))
    except:
        return {'descriptions':{}}

def _set_archive_catalog(d):#w
    json.dump(d,file(os.path.join(archivepath,'archive.json'),'w'),indent=4,separators=(',', ': '))

def get_complete_list(json_type_token):#ro
    catalog_lock().sharedLock()
    d=_get_archive_catalog()
    shown=[]
    if json_type_token in d:
        for h in d[json_type_token]:
            if get_archived_file(json_type_token,h) and h in d['descriptions'] and h not in shown:
                shown.append(h)
                #print 'complete',h
                yield h
    catalog_lock().unlock()


def get_archive_list(request,json_type_token):#ro
    r=_get_archive_dictionary(request)
    if json_type_token not in r:
        return
    catalog_lock().sharedLock()
    da=_get_archive_catalog()
    shown=[]
    for h in r[json_type_token]:
        if get_archived_file(json_type_token,h) and h in da['descriptions'] and h not in shown:
            shown.append(h)
            #print 'select',h
            yield h
    catalog_lock().unlock()

def append_to_archive_list(request,json_type_token,h):#w
    r=_get_archive_dictionary(request)
    if json_type_token not in r:
        r[json_type_token]=[]
    if h in r[json_type_token]:
        return False
    r[json_type_token].append(h)
    _set_archive_dictionary(request,r)
    return True

def remove_from_archive_list(request,json_type_token,h):#w
    r=_get_archive_dictionary(request)
    if json_type_token in r and h in r[json_type_token]:
        r[json_type_token].remove(h)
        _set_archive_dictionary(request,r)
        return True
    return False

def replace_archive_list(request,json_type_token,ha):
    r=_get_archive_dictionary(request)
    r[json_type_token]=ha
    _set_archive_dictionary(request,r)

#fixme read/write lock for the catalog
def store_archived_json(request,json_type_token,description,content):#w
    cs=json.dumps(content, separators=(',',':'))
    store_archived_file(request,json_type_token,description,cs)

def hashval_for(content,length=12):
    h=hashlib.sha1()
    h.update(content)
    hashval=h.hexdigest()
    if length<len(hashval):
        hashval=hashval[:length]
    return hashval

def hashval_verify(content,hashval):
    return hashval_for(content,len(hashval))==hashval

def store_archived_file(request,json_type_token,description,cs):
    if len(cs)>1024*64:
        return False
    catalog_lock().exclusiveLock()
    hashval=hashval_for(cs)
    #write to file
    da=_get_archive_catalog()
    if json_type_token not in da:
        da[json_type_token]=[]
    if hashval in da[json_type_token]:
        catalog_lock().unlock()
        return False
    file(_path_for_file(json_type_token,hashval),'w').write(cs)

    append_to_archive_list(request,json_type_token,hashval)

    da[json_type_token].append(hashval)
    da['descriptions'][hashval]=description
    _set_archive_catalog(da)
    catalog_lock().unlock()
    return True

def remove_archived_file(json_type_token,hashval):#w
    catalog_lock().exclusiveLock()
    try:
        os.unlink(_path_for_file(json_type_token,hashval))
    except:
        pass
    da=_get_archive_catalog()
    dostore=False
    if json_type_token in da and hashval in da[json_type_token]:
        da[json_type_token].remove(hashval)
        dostore=True
    if hashval in da['descriptions']:
        del da['descriptions'][hashval]
        dostore=True
    if dostore:
        _set_archive_catalog(da)
    catalog_lock().unlock()

def get_file_description(json_type_token,hashval):#ro
    da=_get_archive_catalog()
    if json_type_token in da and hashval in da[json_type_token] and hashval in da['descriptions']:
        cs=get_archived_file(json_type_token,hashval)
        if cs==None:
            return None
        st=os.stat(_path_for_file(json_type_token,hashval))
        epoch=datetime(1970,1,1,0,0,0)
        mtime=epoch+timedelta(seconds=st.st_mtime)
        ctime=epoch+timedelta(seconds=st.st_ctime)
        fsize=st.st_size
        return {'description':da['descriptions'][hashval],'content_size':len(cs),'moddate':mtime,"created":ctime,'size':fsize}
    return None

def get_archived_json(json_type_token,hashval,parseFile=True):#ro
    try:
        tmp=get_archived_file(json_type_token,hashval)
        if tmp==None:
            return None
        if not parseFile:
            return True
        return json.loads(tmp)
    except:
        return None

def _path_for_file(json_type_token,hashval):
    return os.path.join(archivepath,json_type_token+'_'+hashval)

def get_archived_file(json_type_token,hashval):
    try:
        tmp=file(_path_for_file(json_type_token,hashval)).read()
        if not hashval_verify(tmp,hashval):
            return None
        return tmp
    except:
        return None


def make_archived_widget(request,json_type_token,formname,onchange="",formfilename=None,formhost=None,formfileonchange="",formfilefield=None,formfilefielddesc="",customizeurl=None,defaultname="default"):
    ret=''
    if formfilename and formhost:
        onchange="doVisibleIf('%s','%s',%s,'%s');%s" % (formhost,formname,"'custom'",formfilefield if formfilefield else (formfilename+'_span'),onchange) 
    ret+='<option value="default">%s</option>\n' % (defaultname)
    for h in get_archive_list(request,json_type_token):
        ret+='<option value="%s">%s</option>\n' % (h,get_file_description(json_type_token,h)['description'])
    ret+='<option value="custom">custom...</option>\n'
    ret = ('<select NAME="%s" SIZE="1" onchange="%s" >\n' % (formname,onchange)) + ret + '</select>\n'
    ret = ('<input type="hidden" name="%s_token" value="%s"/>\n' % (formname,json_type_token) ) +ret
    if formfilename:
        ret+='<br/><span id=%s style="display: none">\n' % (formfilefield if formfilefield else (formfilename+'_span'))
        ret+='%s<input type="file" name="%s" onchange="%s"/>'% (formfilefielddesc,formfilename,formfileonchange)
        if customizeurl!=None:
            ret+='<br/> or <a href="%s">Download New</a>' % (customizeurl)
        ret+='</span>\n' 
    return ret

@view_config(route_name='archiveconf',renderer='templates/archivelist.pt')
def archiveconf(request):
    tok = request.matchdict['json_type_token']
    #check if this was submitted
    print request.params
    if 'remove' in request.params:
        remove_archived_file(tok,request.params.getone('remove'))
    if 'submitted' in request.params:
        usearray=[]
        for h in get_complete_list(tok):
            if h in request.params and request.params.getone(h):
                usearray.append(h)
        if 'remove' not in request.params:
            replace_archive_list(request,tok,usearray)
            if 'destination' in request.params:
                return HTTPTemporaryRedirect(location=request.params.getone('destination'))
    else:
        usearray=[x for x in get_archive_list(request,tok)]
    return {'datetime':datetime,'timedelta':timedelta,'token':tok,
    'entries':get_complete_list(tok),'selected_entries':usearray,'get_file_description':get_file_description}
