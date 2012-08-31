from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.config import Configurator

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    import matplotlib
    matplotlib.use('Agg')
    my_session_factory = UnencryptedCookieSessionFactoryConfig('picnicsecret')
    config = Configurator(settings=settings, session_factory=my_session_factory)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('image_request','/statichash/{statickey}')
    config.add_route('month', '/{accesstype}/{access}/{thumbtype}/{year}/{month}/')
    config.add_route('imagegen', '/{accesstype}/{access}/custom_rti/')
    config.add_route('netcdfgen', '/{accesstype}/{access}/custom_netcdf/')
    config.add_route('multiview', '/{accesstype}/{access}/all/{year}/{month}/{day}/')
    config.add_route('thumb', '/{accesstype}/{access}/{thumbtype}/',view='picnic.views.redirect_month')
    config.add_route('inst', '/{accesstype}/{access}/',view='picnic.views.redirect_day')
    config.add_route('home', '/')
    config.add_route('date','/{accesstype}/{access}/{year}/{month}/{day}/{ampm}/')
    config.add_route('select_month','/selectmonth')
    config.add_route('select_day','/selectday')
    config.scan()
    return config.make_wsgi_app()
