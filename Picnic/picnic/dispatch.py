import picnicsession
from datetime import datetime,timedelta
import jsgen
import json
import os,sys
from pyramid.httpexceptions import HTTPBadRequest
import traceback
import server_archive
import logging
log = logging.getLogger(__name__)
#get parameters from session, call function to make DPL and make images
def createimages(request,session,isBackground):
    log.debug("createimages: %s %s %s" % (repr(request), repr(session), repr(isBackground)) )
    if isBackground in [True, None]:
        makeImagesFromDPL(session,makeDPLFromSession(session))

#parse parameters, put in session
def newimages(request,session,isBackground):
    if isBackground in [False, None]:
        parseImageParameters(request,session)
    if isBackground in [True, None]:
        parseImageParametersBackground(request,session)
        createimages(request,session,isBackground)

     #call function to make dpl from netcdf and make images from it
def readnetcdf(request,session,isBackground):
    if isBackground in [True, None]:
        makeImagesFromDPL(session,makeDPLFromNetCDF(session,session['filename']))
   
#get parameters from session, call function to make DPL and make a netcdf
def createnetcdf(request,session,isBackground):
    if isBackground in [True, None]:
        makeNetCDFFromDPL(session,makeDPLFromSession(session),session['template'],session['filename'])
        tmp=[]
        if session['figstocapture']!=None:
            for k,v in session['figstocapture'].items():
                tmp.extend(v)
        if len(tmp)>0:
            picnicsession.updateSessionComment(session,'done. capturing images')
            readnetcdf(request,session,isBackground)
        else:
            picnicsession.updateSessionComment(session,'done.')

   
#parse parameters, put in session
def newnetcdf(request,session,isBackground):
    if isBackground in [False, None]:
        parseImageParameters(request,session)
        parseNetCDFParameters(request,session)
    if isBackground in [True,None]:
        parseImageParametersBackground(request,session)
        createnetcdf(request,session,isBackground)

#get parameters from session, call function to make DPL and make a netcdf
def createmultinetcdf(request,session,isBackground):
    if isBackground in [True, None]:
        dpl,dplp=makeDPLFromSession(session,doSearch=False)
        makeMultiNetCDFFromDPL(session,dpl,dplp,session['template'])
        picnicsession.updateSessionComment(session,'done.')

   
#parse parameters, put in session
def newmultinetcdf(request,session,isBackground):
    if isBackground in [False, None]:
        parseImageParameters(request,session)
        parseNetCDFParameters(request,session)
    if isBackground in [True,None]:
        createmultinetcdf(request,session,isBackground)
    
def getDispatchers():
    return {
        'newimages':newimages,
        'createimages':createimages,
        'readnetcdf':readnetcdf,
        'createnetcdf':createnetcdf,
        'newnetcdf':newnetcdf,
        'createmultinetcdf':createmultinetcdf,
        'newmultinetcdf':newmultinetcdf
    }

from HSRLImageArchiveLibrarian import HSRLImageArchiveLibrarian
lib=HSRLImageArchiveLibrarian(indexdefault='site')

def parseImageParameters(request,session):

    methods=['site','dataset','instrument']
    for m in methods:
        if m not in request.params:
            continue
        method=m
        session['method']=method
        try:
            session[method]=int(request.params.getone(method));
            session['methodkey']=int(request.params.getone(method));
        except:
            session[method]=request.params.getone(method);
            session['methodkey']=request.params.getone(method);
        break
    starttime=datetime(int(request.params.getone('byr')),
                       int(request.params.getone('bmo')),
                       int(request.params.getone('bdy')),
                       int(request.params.getone('bhr')),
                       int(request.params.getone('bmn')),
                       0)
    endtime=datetime(int(request.params.getone('eyr')),
                     int(request.params.getone('emo')),
                     int(request.params.getone('edy')),
                     int(request.params.getone('ehr')),
                     int(request.params.getone('emn')),
                     0)
    session['altmin']=float(request.params.getone('lheight'))*1000
    session['altmax']=float(request.params.getone('height'))*1000
    session['starttime']=starttime.strftime(picnicsession.json_dateformat)
    session['endtime']=endtime.strftime(picnicsession.json_dateformat)
    #contstruct dpl
    datinfo=lib(**{method:session[method]})
    instruments=datinfo['Instruments']
    name=datinfo['Name']
    datasetname=instruments[0].lower()
    #print figstocapture
    datasets=[]
    for inst in instruments:
        datasets.extend(lib.instrument(inst)['datasets'])

    #dplc=dpl_rti(datasetname,starttime,endtime,timedelta(seconds=timeres),endtime-starttime,altmin,altmax,altres);#alt in m
    #construct image generation parameters
    session['dataset']=datasetname
    session['name']=name

    if 'custom_processing' in request.params and request.params.getone('custom_processing')!='default':
        cust=request.params.getone('custom_processing')
        if cust=='custom':
            try:
                pd=request.params.getone('process_parameters_content')
                pdc=pd.file.read()
                d=json.loads(pdc)#.file.read())
            except:
                traceback.format_exc()
                return HTTPBadRequest()
        else:
            d=server_archive.get_archived_json(request.params.getone('custom_processing_token'),cust)
        #print 'Storing custom process parameters ',request.params.getone('process_parameters_content')
        picnicsession.storejson(session,d,'process_parameters.json')
    #return HTTPTemporaryRedirect(location=request.route_path('progress_withid',session=sessionid))
    if 'custom_display' in request.params and request.params.getone('custom_display')!='default':
        cust=request.params.getone('custom_display')
        if cust=='custom':
            pd=request.params.getone('display_defaults_content')
            print 'Storing custom image parameters to',session['sessionid'],'display_parameters.json'
            try:
                d=json.loads(pd.file.read())
            except:
                traceback.format_exc()
                return HTTPBadRequest()
        else:
            d=server_archive.get_archived_json(request.params.getone('custom_display_token'),cust)
        picnicsession.storejson(session,d,'display_parameters.json')
        session['figstocapture']=None
        getdatasets=datasets
        imagesetlist=jsgen.formsetsForInstruments(datasets,'images')
        session['figrequest']={}
        for i in imagesetlist:
            session['figrequest'][i['formname']]='custom'
    elif 'display_defaults_file' in request.params:
        session['display_defaults_file']=request.params.getone('display_defaults_file')
        if os.path.sep in session['display_defaults_file']:
            session['display_defaults_file']=picnicsession.sessionfile(session,session['display_defaults_file'])
        session['figstocapture']=None
        getdatasets=datasets
        imagesetlist=jsgen.formsetsForInstruments(datasets,'images')
        session['figrequest']={}
        for i in imagesetlist:
            session['figrequest'][i['formname']]='custom'
    else:
        session['display_defaults_file']='all_plots.json'
        imagesetlist=jsgen.formsetsForInstruments(datasets,'images')
        getdatasets=[]
        figstocapture={}
        session['figrequest']={}
        for i in imagesetlist:
            #print i
            try:
                setmode=request.params.getone(i['formname'])
                session['figrequest'][i['formname']]=setmode
                figstocapture[i['setenum']]=i['sets'][setmode]['figs']
                if len(i['sets'][setmode]['figs'])>0:#radio buttons
                    if 'enabled' in i['sets'][setmode]:
                        for dat in i['sets'][setmode]['enabled']:
                            if dat not in getdatasets:
                                getdatasets.append(dat)
                    if 'required' in i['sets'][setmode]:
                        for dat in i['sets'][setmode]['required']:
                            if dat not in getdatasets:
                                getdatasets.append(dat)
                if "options" in i and len(i["options"])>0:#checkboxes only currently, may extend to choicebox
                    for opt in i["options"]:
                        if opt["formname"] in request.params and request.params.getone(opt['formname']):
                                if 'enabled' in opt:
                                    for dat in opt['enabled']:
                                        if dat not in getdatasets:
                                            getdatasets.append(dat)
                                if 'required' in opt:
                                    for dat in opt['required']:
                                        if dat not in getdatasets:
                                            getdatasets.append(dat)
                                figstocapture[i['setenum']].extend(opt['included'])
                        else:
                            for f in opt['included']:
                                figstocapture[i['setenum']].append('-'+f)
            except:
                pass
        session['figstocapture']=figstocapture
    session['datastreams']=getdatasets
        #if None in session['figstocapture']:
    picnicsession.storesession(session)

def parseImageParametersBackground(request,session):
    picnicsession.updateSessionComment(session,'setup')
    if 'custom_display' in request.params and request.params.getone('custom_display')!='default':
        import hsrl.utils.json_config as jc
        disp=jc.json_config(picnicsession.loadjson(session,'display_parameters.json'))#session['display_defaults'])
    else:
        import hsrl.data_stream.display_utilities as du
        (disp,conf)=du.get_display_defaults(session['display_defaults_file'])

    #else:#fixme should this be enable_all()?
    #    (disp,conf)=du.get_display_defaults('web_plots.json')
    allfigs=session['figstocapture']==None
    if not allfigs:
        for k,v in session['figstocapture'].items():
            if None in v:
                allfigs=True
                break
    if not allfigs: # None indicates all should be captured, so if its not, scan structure
        data_req='images'
        lib_filetype='data'
        for fi in disp.get_attrs(): # for each figure
            if 'enable' in disp.get_labels(fi): # if it can be enabled/disabled
                disp.set_value(fi,'enable',0)
        for inst,figset in session['figstocapture'].items():
            for fi in disp.get_attrs(): # for each figure
                if 'enable' in disp.get_labels(fi): # if it can be enabled/disabled        
                    if fi in figset or ('#'+fi) in figset: #if requested, enable it
                        disp.set_value(fi,'enable',1)
                        if not fi.endswith('_image') and inst=='hsrl':
                            data_req='images housekeeping'
                            lib_filetype=None
                    elif ('-'+fi) in figset or ('-#'+fi) in figset:#if explicitly disabled, disable it
                        disp.set_value(fi,'enable',0)
    else:
        if session['figstocapture']!=None:
          for inst,figset in session['figstocapture'].items():
            for fi in disp.get_attrs(): # for each figure
                if 'enable' in disp.get_labels(fi): # if it can be enabled/disabled        
                    if ('-'+fi) in figset or ('-#'+fi) in figset:#if explicitly disabled, disable it
                        disp.set_value(fi,'enable',0)

        data_req= 'images housekeeping'
        lib_filetype=None

    picnicsession.storejson(session,disp.json_representation(),'display_parameters.json')
    if 'data_request' not in session:
        session['data_request']=data_req
    if 'lib_filetype' not in session:
        session['lib_filetype']=lib_filetype
    picnicsession.storesession(session)


def parseNetCDFParameters(request,session):
    session['timeres']=float(request.params.getone('timeres'))
    session['altres']=float(request.params.getone('altres'))
    session['maxtimeslice_timedelta']=60*60*2
    session['data_request']="images housekeeping"
    session['template']=request.params.getone('cdltemplatename')
    if session['template']=='custom':
        fn=picnicsession.sessionfile(session,'template.cdl',create=True)
        file(fn,'w').write(request.params.getone('cdltemplate_content').file.read())
        session['template']=fn
    stf=datetime.strptime(session['starttime'],picnicsession.json_dateformat).strftime('_%Y%m%dT%H%M')
    etf=datetime.strptime(session['endtime'],picnicsession.json_dateformat).strftime('_%Y%m%dT%H%M')
    session['filesuffix']=('_%gs_%gm' % (session['timeres'],session['altres']))
    session['filemode']=request.params.getone('filemode')
    session['fileprefix']=session['dataset']+ '_' + session['filemode']
    session['filename']=session['dataset'] + stf + etf + session['filesuffix'] + '.nc'
    session['username']=request.params.getone('username')

    datinfo=lib(**{session['method']:session[session['method']]})
    instruments=datinfo['Instruments']
    #print figstocapture
    datasets=[]
    for inst in instruments:
        datasets.extend(lib.instrument(inst)['datasets'])
 
    fieldstocapture=[]
    if not 'allfields' in request.params or not request.params.getone('allfields'):
        fieldsetlist=jsgen.formsetsForInstruments(datasets,'netcdf')
        getdatasets=[]
        for inst in fieldsetlist:#per instrument
            for subset in inst['sets']:
                subsetincluded=False
                for checkbox in subset['options']:
                    formname=checkbox['formname']
                    if formname not in request.params or not request.params.getone(formname):
                        continue
                    subsetincluded=True
                    for fieldname in checkbox['included']:
                        if fieldname not in fieldstocapture:
                            fieldstocapture.append(fieldname)
                    if 'enabled' in checkbox:
                        for dat in checkbox['enabled']:
                            if dat not in getdatasets:
                                getdatasets.append(dat)
                    if 'required' in checkbox:
                        for dat in checkbox['required']:
                            if dat not in getdatasets:
                                getdatasets.append(dat)
                if subsetincluded:
                    if 'included' in subset:
                        for fieldname in subset['included']:
                            if fieldname not in fieldstocapture:
                                fieldstocapture.append(fieldname)
                    if 'enabled' in subset:
                        for dat in subset['enabled']:
                            if dat not in getdatasets:
                                getdatasets.append(dat)
                    if 'required' in subset:
                        for dat in subset['required']:
                            if dat not in getdatasets:
                                getdatasets.append(dat)
    else:
        getdatasets=datasets
    session['datastreams']=getdatasets

    print fieldstocapture
    session['selected_fields']=fieldstocapture

    figstocapture={}

    if 'custom_display' not in request.params or request.params.getone('custom_display')=='default':
        imagesetlist=jsgen.formsetsForInstruments(datasets,'images')
        session['display_defaults_file']='all_plots.json'
      
        for i in imagesetlist:
            #print i
            try:
                defmode=i['default']
                figstocapture[i['setenum']]=[]
                for figname in i['sets'][defmode]['figs']:#get default images of default set
                    if 'image' in figname and figname not in figstocapture[i['setenum']]:
                        figstocapture[i['setenum']].append(figname)
                if 'options' in i:#and default options
                    for opt in i['options']:
                        if opt['default']:#checkbox default is true
                            for figname in i['included']:
                                if 'image' in figname and figname not in figstocapture[i['setenum']]:
                                    figstocapture[i['setenum']].append(figname)
            except:
                pass
    else:
        figstocapture=None
    session['figstocapture']=figstocapture
    session['lib_filetype']=None
    picnicsession.storesession(session)

def fromSession(session,xlate):
    ret={}
    for k in xlate:
        if k in session:
            tmp=session[k]
            dest=xlate[k]
            if dest.endswith('_datetime'):
                tmp=datetime.strptime(tmp,picnicsession.json_dateformat)
            elif dest.endswith('_timedelta'):
                tmp=timedelta(seconds=tmp)
            ret[dest]=tmp
    return ret

class getLastOf:
    def __init__(self,field,parents=None):
        self.field=field
        self.parents=parents

    def __call__(self,fr):
        if self.parents==None:
            if hasattr(fr,self.field):
                #print 'GETLASTOF:',p,'has',self.field
                fa=getattr(fr,self.field)
                if not hasattr(fa,'shape'):
                    return fa
                if hasattr(fa,'shape') and fa.shape[0]>0:
                    #print 'GETLASTOF:',p,self.field,'has shape. value is',fa[-1]
                    return fa[-1]
        else:
            for p in self.parents:
                if hasattr(fr,p):
                    #print 'GETLASTOF: has',p
                    pa=getattr(fr,p)
                    if hasattr(pa,self.field):
                        #print 'GETLASTOF:',p,'has',self.field
                        fa=getattr(pa,self.field)
                        if hasattr(fa,'shape') and fa.shape[0]>0:
                            #print 'GETLASTOF:',p,self.field,'has shape. value is',fa[-1]
                            return fa[-1]
        return None

def makeDPLFromSession(session,doSearch=True):
    copyToInit={
        'dataset':'instrument',
        'maxtimeslice':'maxtimeslice_timedelta',
        'data_request':'data_request',
        'lib_filetype':'filetype',
    }
    copyToSearch={
        'starttime':'start_time_datetime',
        'endtime':'end_time_datetime',
        'altmin':'min_alt_m',
        'altmax':'max_alt_m',
        'timeres':'timeres_timedelta',
        'altres':'altres_m',
    }
    hasProgress=False
    from hsrl.dpl_experimental.dpl_hsrl import dpl_hsrl
    process_control=None
    if os.access(picnicsession.sessionfile(session,'process_parameters.json'),os.R_OK):
        process_control=picnicsession.loadjson(session,'process_parameters.json')
        import hsrl.utils.json_config as jc
        process_control=jc.json_config(process_control,default_key='process_defaults')
    dplobj=dpl_hsrl(process_control=process_control,**fromSession(session,copyToInit))
    if not doSearch:
        return dplobj,fromSession(session,copyToSearch)
    searchparms=fromSession(session,copyToSearch)
    #try:
    #    import hsrl.utils.threaded_generator
    #    dplc=hsrl.utils.threaded_generator.threaded_generator(dplobj,**searchparms)
    #except:
    hsrlnar=dplobj(**searchparms)
    dplc=hsrlnar
    if 'merge' in session['datastreams']:#add merge to rs_mmcr, refit
        import hsrl.dpl_tools.time_frame as time_slicing
        import hsrl.dpl_tools.resample_altitude as altitude_resampling
        import hsrl.dpl_tools.substruct as frame_substruct
        from hsrl.dpl_netcdf.NetCDFZookeeper import GenericTemplateRemapNetCDFZookeeper 
        import hsrl.dpl_netcdf.MMCRMergeLibrarian as mmcr
        import hsrl.utils.hsrl_array_utils as hau

        if session['dataset']=='ahsrl':
            mmcrzoo=GenericTemplateRemapNetCDFZookeeper('eurmmcrmerge')
            mmcrlib=mmcr.MMCRMergeLibrarian(session['dataset'],['eurmmcrmerge.C1.c1.','nsaarscl1clothC1.c1.'],zoo=mmcrzoo)
        elif session['dataset']=='mf2hsrl':
            pass #set up zoo and lib for mf2
        mmcrnar=mmcr.MMCRMergeCorrector(mmcrlib(start=searchparms['start_time_datetime'],end=searchparms['start_time_datetime']))
        mmcrnar=mmcr.MMCRMergeBackscatterToReflectivity(altitude_resampling.ResampleXd(time_slicing.TimeGinsu(mmcrnar,'times'),'heights',dplc.altitudeAxis))

        hsrlnarsplitter=frame_substruct.SubstructBrancher(hsrlnar)
        hsrlinvnar=time_slicing.TimeGinsu(hsrlnarsplitter.narrateSubstruct('rs_inv'),'times')#,isEnd=True)

        from dplkit.simple.blender import TimeInterpolatedMerge

        merge=TimeInterpolatedMerge(hsrlinvnar,[mmcrnar],allow_nans=True,channels=['heights','Reflectivity','MeanDopplerVelocity','Backscatter','SpectralWidth'])
        merge=frame_substruct.Retyper(merge,hau.Time_Z_Group,{'timevarname':'times','altname':'heights'})
 
        dplc=frame_substruct.SubstructMerger('rs_inv',{
            'rs_mean':hsrlnarsplitter.narrateSubstruct('rs_mean'),
            'rs_raw':hsrlnarsplitter.narrateSubstruct('rs_raw'),
            'rs_inv':hsrlnarsplitter.narrateSubstruct('rs_inv'),
            'rs_mmcr':merge,
            'rs_init':hsrlnarsplitter.narrateSubstruct('rs_init'),
            'rs_static':hsrlnarsplitter.narrateSubstruct('rs_static'),
            'profiles':hsrlnarsplitter.narrateSubstruct('profiles',sparse=True),
            'rs_Cxx':hsrlnarsplitter.narrateSubstruct('rs_Cxx',sparse=True)
            }
        ,hau.Time_Z_Group)
       #merge=picnicsession.PicnicProgressNarrator(dplc,getLastOf('start'), searchparms['start_time_datetime'],searchparms['end_time_datetime'],session)
        #hasProgress=True

    if not os.access(picnicsession.sessionfile(session,'process_parameters.json'),os.R_OK):
        picnicsession.storejson(session,hsrlnar.get_process_control().json_representation(),'process_parameters.json')
    picnicsession.updateSessionComment(session,'processing with DPL')
    if hasProgress:
        return dplc
    return picnicsession.PicnicProgressNarrator(dplc,getLastOf('times',['rs_inv','rs_mean','rs_raw']),
        searchparms['start_time_datetime'],searchparms['end_time_datetime'],session)
    #return dplc    

def makeMultiNetCDFFromDPL(session,DPL,DPLParms,templatefilename):
    picnicsession.updateSessionComment(session,'loading artist')
    #import hsrl.data_stream.open_config as oc
    import hsrl.dpl_experimental.dpl_artists as artists
    ftpbase=os.getenv('FTPPATH','/var/ftp/data')
    ftpurlbase=os.getenv('FTPURL','ftp://lidar.ssec.wisc.edu/data')
    if len(session['username'])==0:
        print 'bad username'
        raise RuntimeError,'Bad username'
    baseftpdir=picnicsession.safejoin(ftpbase,session['username'])
    sessiondir=picnicsession.safejoin(baseftpdir,session['sessionid'])
    try:
        os.mkdir(baseftpdir)
    except:
        pass
    try:
        os.mkdir(sessiondir)
    except:
        pass
    tarname=session['fileprefix'] + DPLParms['start_time_datetime'].strftime('_%Y%m%dT%H%M') + DPLParms['end_time_datetime'].strftime('_%Y%m%dT%H%M') + session['filesuffix'] + '_' + session['sessionid'] + '.tar.bz2'
    tarcompoutputfilename=picnicsession.safejoin(baseftpdir,tarname)
    session['ftpfolder']=ftpurlbase+'/'+session['username']+'/'+session['sessionid']
    session['ftpfile']=ftpurlbase+'/'+session['username']+'/'+tarname
    namer=artists.default_multi_netcdf_namer(sessiondir,session['fileprefix'],session['filesuffix']+'.nc')
    times=artists.multi_netcdf_filewindow('start_time_datetime','end_time_datetime',
        DPLParms['start_time_datetime'],DPLParms['end_time_datetime'],session['filemode'])

    artist=artists.dpl_multi_netcdf_artist(DPL,DPLParms,template=templatefilename,filewindowgenerator=times,filename_maker=namer,selected_bindings=session['selected_fields'])
  
    picnicsession.updateSessionComment(session,'processing')
 
    findTimes=['rs_raw','rs_mean','rs_inv']
    for frame in artist:
        timewindow='blank'
        for f in findTimes:
            if hasattr(frame,f) and hasattr(getattr(frame,f),'times') and len(getattr(frame,f).times)>0:
                t=getattr(frame,f).times
                timewindow=t[0].strftime('%Y.%m.%d %H:%M') + ' - ' + t[-1].strftime('%Y.%m.%d %H:%M')

        picnicsession.updateSessionComment(session,'appended data %s' % (timewindow))
  
    del artist

    pid=os.fork()
    if pid==0:
        os.execvp('tar',('tar','-jcvf',tarcompoutputfilename,'--directory='+baseftpdir,session['sessionid']))
    if pid<0:
        raise RuntimeError,"compression failed due to fork"
    (pid,status)=os.waitpid(pid,0)
    if os.WEXITSTATUS(status)!=0:
        raise RuntimeError,"Compression failed on error %i" % os.WEXITSTATUS(status)

def doNcDumpToFile(filename,outfile):
    def ncdump(f,outp):
        parms=['/usr/bin/ncdump','-h',f]
        f=file(outp,'w')

        os.dup2(f.fileno(),sys.stdout.fileno())
        os.dup2(f.fileno(),sys.stderr.fileno())

        os.execv(parms[0],parms)
        sys.exit(-1)

    import multiprocessing
    p=multiprocessing.Process(target=ncdump, args=(filename,outfile))
    p.start()
    p.join()

def doFrameDumpToFile(provides,frame,outfile):
    def subframe(fr,k):
        if isinstance(fr,dict):
            return fr[k]
        if hasattr(fr,k):
            return getattr(fr,k)
        return None

    def desc(fr):
        ret='' #repr(type(fr)) + ' - '
        try:
            ret=ret+repr(fr.shape)
        except AttributeError:
            try:
                ret=ret+repr([len(fr)])
            except (AttributeError,TypeError):
                ret=ret+'scalar'
        return ret

    def trimjson(d,frame):
        for k in d.keys():
            v=d[k]
            if isinstance(v,dict):
                if 'type' in v:
                    d[k]=repr(d[k]['type']) + ' - ' + desc(subframe(frame,k))
                else:
                    trimjson(v,subframe(frame,k))

    import json
    import copy
    d=copy.deepcopy(provides)
    trimjson(d,frame)
    json.dump(d,file(outfile,'w'),indent=4,separators=(',', ': '))

def makeNetCDFFromDPL(session,DPLgen,templatefilename,netcdffilename):
    picnicsession.updateSessionComment(session,'loading artist')
    #import hsrl.data_stream.open_config as oc
    import hsrl.dpl_experimental.dpl_artists as artists

    #folder=picnicsession.sessionfolder(sessionid);
    picnicsession.updateSessionComment(session,'opening blank netcdf file')
    
    ncfilename=picnicsession.sessionfile(session,netcdffilename,create=True)

    artist=artists.dpl_netcdf_artist(DPLgen,templatefilename,ncfilename,selected_bindings=session['selected_fields'])
  
    picnicsession.updateSessionComment(session,'processing')
 
    findTimes=['rs_raw','rs_mean','rs_inv']
    
    dumped=False

    for frame in artist:
        timewindow='blank'
        if not dumped and frame!=None:
            doFrameDumpToFile(artist.provides,frame,picnicsession.sessionfile(session,'frame.json'))
            dumped=True
        for f in findTimes:
            if hasattr(frame,f) and hasattr(getattr(frame,f),'times') and len(getattr(frame,f).times)>0:
                t=getattr(frame,f).times
                timewindow=t[0].strftime('%Y.%m.%d %H:%M') + ' - ' + t[-1].strftime('%Y.%m.%d %H:%M')

        picnicsession.updateSessionComment(session,'appended data %s' % (timewindow))
  
    doNcDumpToFile(ncfilename,picnicsession.sessionfile(session,'output.cdl'))

    del artist

def makeImagesFromDPL(session,DPLgen):
    picnicsession.updateSessionComment(session,'loading graphics artist')
    #import hsrl.data_stream.open_config as oc
    import hsrl.dpl_experimental.dpl_artists as artists
    import hsrl.utils.json_config as jc
    #import hsrl.calibration.cal_read_utilities as cru
    #import hsrl.graphics.graphics_toolkit as gt
    instrument=session['dataset']
    #sessionid=session['sessionid']
    disp=jc.json_config(picnicsession.loadjson(session,'display_parameters.json'))#session['display_defaults'])
    params=jc.json_config(picnicsession.loadjson(session,'process_parameters.json'),'process_defaults')
    #print session

    #folder=picnicsession.sessionfolder(sessionid)#safejoin('.','sessions',sessionid);
    artistlist={}
    if True:
        picnicsession.updateSessionComment(session,'creating artist')    
        artist=artists.dpl_images_artist(framestream=DPLgen,instrument=session['dataset'],
            max_alt=session['altmax'],
            processing_defaults=params,
            display_defaults=disp)
        artistlist['hsrl']=artist
        if 'merge' in session['datastreams']:
            artist=artists.dpl_radar_images_artist(framestream=artist,display_defaults=disp)
            artistlist['merge']=artist
        picnicsession.updateSessionComment(session,'processing')
        artist()
        picnicsession.updateSessionComment(session,'rendering figures')
        fignum=0

        capturingfigsgroups=session['figstocapture'].copy()
        if capturingfigsgroups==None:
            capturingfigsgroups={}
            for k in artistlist.keys():
                capturingfigsgroups[k]=[None]
        #print capturingfigs
        for inst,capturingfigs in capturingfigsgroups.items():
          if not inst in artistlist:
            continue
          alreadycaptured=[]
          figs=artistlist[inst].figs
          for x in capturingfigs:#plt._pylab_helpers.Gcf.get_all_fig_managers():
            if x in alreadycaptured or (x!=None and (x.startswith('#') or x.startswith('-'))):
                continue
            alreadycaptured.append(x)
            if x == None:
                tmp=[ f for f in figs ];
                tmp.sort()
                capturingfigs.extend(tmp)
                continue
            figname=picnicsession.sessionfile(session,'figure%04i_%s_%s.png' % (fignum,inst,x))
            fignum = fignum + 1
        #      print 'updating  %d' % x.num
            picnicsession.updateSessionComment(session,'capturing '+inst+' figure ' + x)
            if x not in figs:
                f=file(figname,'w')
                f.close()
                continue
        
            fig = figs.figure(x)#plt.figure(x.num)
        
      # QApplication.processEvents()
            
            fig.canvas.draw()
            #fig.canvas.
            fig.savefig(figname,format='png',bbox_inches='tight')
    picnicsession.updateSessionComment(session,'done')


def makeDPLFromNetCDF(session,netcdffilename):
    import hsrl.dpl_experimental.dpl_read_templatenetcdf as dpl_rtnc
    ncfilename=picnicsession.sessionfile(session,netcdffilename)
  
    #doNcDumpToFile(ncfilename,picnicsession.sessionfile(session,'output.cdl'))
    return dpl_rtnc.dpl_read_templatenetcdf(ncfilename)

def main():
    import sys
    import os
    import picnicsession
    picnicsession.addDispatchers(getDispatchers())
    loc=sys.argv[1]
    sess=''
    while len(sess)==0:
        sess=os.path.basename(loc)
        loc=os.path.dirname(loc)
    sessions=loc
    print sess
    print sessions
    os.environ['SESSIONFOLDER']=sessions
    os.putenv('SESSIONFOLDER',sessions)
    session=picnicsession.loadsession(sess)
    picnicsession.taskdispatch('createimages',None,session)


if __name__ == '__main__':
    main()
