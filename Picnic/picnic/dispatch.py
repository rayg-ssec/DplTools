import picnicsession
from datetime import datetime,timedelta
import jsgen
import os

#get parameters from session, call function to make DPL and make images
def createimages(request,session,isBackground):
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
        if len(session['figstocapture'])>0:
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
    
def getDispatchers():
    return {
        'newimages':newimages,
        'createimages':createimages,
        'readnetcdf':readnetcdf,
        'createnetcdf':createnetcdf,
        'newnetcdf':newnetcdf
    }

from HSRLImageArchiveLibrarian import HSRLImageArchiveLibrarian
lib=HSRLImageArchiveLibrarian(indexdefault='site')

def parseImageParameters(request,session):

    method='site'
    session['method']=method
    session[method]=int(request.params.getone(method));
    session['methodkey']=int(request.params.getone(method));
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

    if 'custom_processing' in request.params and request.params.getone('custom_processing'):
        print 'Storing custom process parameters ',request.params.getone('process_parameters_content')
        try:
            d=json.loads(request.params.getone('process_parameters_content').file.read())
            picnicsession.storejson(session,d,'process_parameters.json')
        except:
            return HTTPBadRequest()
    #return HTTPTemporaryRedirect(location=request.route_path('progress_withid',session=sessionid))
    if 'custom_display' in request.params and request.params.getone('custom_display'):
        print 'Storing custom image parameters ',request.params.getone('display_defaults_content')
        try:
            d=json.loads(request.params.getone('display_defaults_content').file.read())
            picnicsession.storejson(session,d,'display_parameters.json')
        except:
            return HTTPBadRequest()
        session['figstocapture']=[None]
    elif 'display_defaults_file' in request.params:
        session['display_defaults_file']=request.params.getone('display_defaults_file')
        if os.path.sep in session['display_defaults_file']:
            session['display_defaults_file']=picnicsession.sessionfile(session,session['display_defaults_file'])
        session['figstocapture']=[None]
    else:
        session['display_defaults_file']='all_plots.json'
        imagesetlist=jsgen.formsetsForInstruments(datasets,'images')
        
        figstocapture=[]
        for i in imagesetlist:
            #print i
            try:
                setmode=request.params.getone(i['formname'])
                figstocapture.extend(i['sets'][setmode]['figs'])
            except:
                pass
        session['figstocapture']=figstocapture
        #if None in session['figstocapture']:
    picnicsession.storesession(session)

def parseImageParametersBackground(request,session):
    picnicsession.updateSessionComment(session,'setup')
    if 'custom_display' in request.params and request.params.getone('custom_display'):
        import hsrl.utils.json_config as jc
        disp=jc.json_config(picnicsession.loadjson(session,'display_parameters.json'))#session['display_defaults'])
    else:
        import hsrl.data_stream.display_utilities as du
        (disp,conf)=du.get_display_defaults(session['display_defaults_file'])

    #else:#fixme should this be enable_all()?
    #    (disp,conf)=du.get_display_defaults('web_plots.json')
    if None not in session['figstocapture']: # None indicates all should be captured, so if its not, scan structure
        data_req='images'
        for fi in disp.get_attrs(): # for each figure
            if 'enable' in disp.get_labels(fi): # if it can be enabled/disabled
                if fi in session['figstocapture']: #if requested, enable it
                    disp.set_value(fi,'enable',1)
                    if fi.startswith('show'):
                        data_req='images housekeeping'
                else:
                    disp.set_value(fi,'enable',0) #otherwise disable it
    else:
        data_req= 'images housekeeping'

    picnicsession.storejson(session,disp.json_representation(),'display_parameters.json')
    if 'data_request' not in session:
        session['data_request']=data_req
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
    session['filename']=session['dataset'] + stf + etf + ('_%gs_%gm.nc' % (session['timeres'],session['altres']))

    figstocapture=[]

    if 'custom_display' not in request.params or request.params.getone('custom_display'):
        datinfo=lib(**{session['method']:session[session['method']]})
        instruments=datinfo['Instruments']
        #print figstocapture
        datasets=[]
        for inst in instruments:
            datasets.extend(lib.instrument(inst)['datasets'])
 
        imagesetlist=jsgen.formsetsForInstruments(datasets,'images')
        session['display_defaults_file']='all_plots.json'
      
        for i in imagesetlist:
            #print i
            try:
                defmode=i['default']
                for figname in i['sets'][defmode]['figs']:
                    if 'image' in figname:
                        figstocapture.append(figname)
            except:
                pass
    session['figstocapture']=figstocapture
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


def makeDPLFromSession(session):
    copyToInit={
        'dataset':'instrument',
        'maxtimeslice':'maxtimeslice_timedelta',
        'data_request':'data_request'
    }
    copyToSearch={
        'starttime':'start_time_datetime',
        'endtime':'end_time_datetime',
        'altmin':'min_alt_m',
        'altmax':'max_alt_m',
        'timeres':'timeres_timedelta',
        'altres':'altres_m',
    }
    from hsrl.dpl_experimental.dpl_hsrl import dpl_hsrl
    process_control=None
    if os.access(picnicsession.sessionfile(session,'process_parameters.json'),os.R_OK):
        process_control=picnicsession.loadjson(session,'process_parameters.json')
        import hsrl.utils.json_config as jc
        process_control=jc.json_config(process_control,default_key='process_defaults')
    dplobj=dpl_hsrl(process_control=process_control,**fromSession(session,copyToInit))
    try:
        import hsrl.utils.threaded_generator
        dplc=hsrl.utils.threaded_generator.threaded_generator(dplobj,**fromSession(session,copyToSearch))
    except:
        dplc=dplobj(**fromSession(session,copyToSearch))
    if not os.access(picnicsession.sessionfile(session,'process_parameters.json'),os.R_OK):
        picnicsession.storejson(session,dplobj.get_process_control(None).json_representation(),'process_parameters.json')
    picnicsession.updateSessionComment(session,'processing with DPL')
    return dplc    

def makeNetCDFFromDPL(session,DPLgen,templatefilename,netcdffilename):
    picnicsession.updateSessionComment(session,'loading artist')
    #import hsrl.data_stream.open_config as oc
    import hsrl.dpl_experimental.dpl_artists as artists

    #folder=picnicsession.sessionfolder(sessionid);
    picnicsession.updateSessionComment(session,'opening blank netcdf file')
    
    ncfilename=picnicsession.sessionfile(session,netcdffilename,create=True)

    artist=artists.dpl_netcdf_artist(DPLgen,templatefilename,ncfilename)
  
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
    
    if True:
        picnicsession.updateSessionComment(session,'creating artist')    
        artist=artists.dpl_images_artist(framestream=DPLgen,instrument=session['dataset'],
            max_alt=session['altmax'],
            processing_defaults=params,
            display_defaults=disp)
        picnicsession.updateSessionComment(session,'processing')
        figs=artist()
        picnicsession.updateSessionComment(session,'rendering figures')
        fignum=0

        alreadycaptured=[]
        capturingfigs=session['figstocapture']
        print capturingfigs
        for x in capturingfigs:#plt._pylab_helpers.Gcf.get_all_fig_managers():
            if x in alreadycaptured:
                continue
            alreadycaptured.append(x)
            if x == None:
                tmp=[ f for f in figs ];
                tmp.sort()
                capturingfigs.extend(tmp)
                continue
            figname=picnicsession.sessionfile(session,'figure%04i_%s.png' % (fignum,x))
            fignum = fignum + 1
        #      print 'updating  %d' % x.num
            picnicsession.updateSessionComment(session,'capturing figure ' + x)
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
    return dpl_rtnc.dpl_read_templatenetcdf(ncfilename)
