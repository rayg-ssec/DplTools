from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.config import Configurator
import matplotlib
matplotlib.use('Agg')

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    my_session_factory = UnencryptedCookieSessionFactoryConfig('picnicsecret')
    config = Configurator(settings=settings, session_factory=my_session_factory)
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

    import picnicsession
    import dispatch
    picnicsession.addDispatchers(dispatch.getDispatchers())

    config.scan()
    return config.make_wsgi_app()
