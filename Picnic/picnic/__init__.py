from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.config import Configurator
import os
import matplotlib
matplotlib.use('Agg')

def verifyEnvValue(envname,ininame,settings,defval=None):
    if os.getenv(envname,None)!=None:
        return
    if ininame!=None and ininame in settings:
        print 'setting from settings: %s=%s from %s' % (envname,settings[ininame],ininame)
        os.putenv(envname,settings[ininame])
        os.environ[envname]=settings[ininame]
    elif defval!=None:
        print "Configuration Warning: setting environment variable %s to %s (set using %s or ini file value %s" % (envname,defval,envname,ininame)
        os.putenv(envname,defval)
    assert os.getenv(envname,None)!=None,'Configuration Error: Define '+ininame+" in your Pyramid INI file, or set the environment variable "+envname

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    my_session_factory = UnencryptedCookieSessionFactoryConfig('picnicsecret')
    config = Configurator(settings=settings, session_factory=my_session_factory)
    verifyEnvValue("HSRL_DATA_ARCHIVE_CONFIG","hsrl.data_archive_config",settings,defval="/etc/dataarchive.plist")
    verifyEnvValue("HSRL_CONFIG","hsrl.config",settings)
    verifyEnvValue("FTPPATH",'picnic.ftp.basepath',settings)
    verifyEnvValue("FTPURL",'picnic.ftp.baseurl',settings)
    verifyEnvValue("SESSIONFOLDER",'picnic.sessionbasepath',settings,defval='./sessions')
    verifyEnvValue("SERVERSIDE_ARCHIVEPATH",'picnic.serverside_archivepath',settings,defval='./serverarchive')
    verifyEnvValue("PICNIC_USERCHECK",'picnic.usercheck_enable',settings,defval='false')
    config.add_static_view('static', 'static', cache_max_age=3600)
    #data availability
    config.add_route('dataAvailability', '/dataAvailability')
    
    #image gen
    config.add_route('imagereq', '/rti_request/')#will set up process, and forward to progress#
    config.add_route('imageresult', '/rti_result/{session}')#
    config.add_route('reimagereq', '/rti_result/{session}/reimage')#
    config.add_route('imagegen', '/by_{accesstype}/{access}/custom_rti/')
    config.add_route('imagejavascript', '/by_{accesstype}/{access}/custom_rti/req.js')

    #netcdf gen redirect
    config.add_route('netcdfreq', '/netcdf_request/')#will set up process, and forward to progress#
    config.add_route('netcdfresult', '/netcdf_result/{session}')#
    config.add_route('netcdfreimage','/netcdf_result/{session}/reimage')
    config.add_route('netcdfgen', '/by_{accesstype}/{access}/custom_netcdf/')
    config.add_route('netcdfjavascript', '/by_{accesstype}/{access}/custom_netcdf/req.js')
    config.add_route('multinetcdfresult', '/multinetcdf_result/{session}')#
 
    #logbook redirect
    config.add_route('logbook', '/by_{accesstype}/{access}/logbook/')

    #month
    config.add_route('thumb', '/by_{accesstype}/{access}/{thumbtype}/')#goes to month
    config.add_route('month', '/by_{accesstype}/{access}/{thumbtype}/{year}/{month}/')
    config.add_route('multiview', '/by_{accesstype}/{access}/all/{year}/{month}/{day}/')
    #images
    config.add_route('today', '/by_{accesstype}/{access}/')#goes to today
    config.add_route('date','/by_{accesstype}/{access}/{year}/{month}/{day}/{ampm}/')
    #portal
    config.add_route('home', '/')
    config.add_route('site', '/by_site/')
    config.add_route('dataset', '/by_dataset/')

    #utilities
    config.add_route('session_resource','/session/{session}/{filename}')
    config.add_route('image_resource','/by_{accesstype}/{access}/{year}/{month}/{day}/{filename}')
    config.add_route('resource_request','/statichash/{statickey}')#static file
    config.add_route('progress', '/progress/')#
    config.add_route('progress_withid', '/progress/{session}')#
    config.add_route('userCheck', '/userCheck')#
    config.add_route('select_month','/selectmonth')
    config.add_route('select_day','/selectday')

    #debug/status pages
    config.add_route('status','/status')
    config.add_route('debug','/debug')
    config.add_route('debugsession','/debug/{session}')

    #json modification
    config.add_route('imagecustom','/imagecustom')
    config.add_route('generatejson','/jsongen')

    #server-side json archive cookie mods
    config.add_route('archiveconf','/archived/{json_type_token}')

    import picnicsession
    import dispatch
    picnicsession.addDispatchers(dispatch.getDispatchers())

    config.scan()
    return config.make_wsgi_app()
