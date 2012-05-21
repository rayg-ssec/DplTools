from pyramid.config import Configurator

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('image_request','/statichash/{statickey}')
    config.add_route('month', '/{accesstype}/{access}/{thumbtype}/{year}/{month}/')
    config.add_route('thumb', '/{accesstype}/{access}/{thumbtype}/',view='picnic.views.redirect_month')
    config.add_route('inst', '/{accesstype}/{access}/',view='picnic.views.redirect_day')
    config.add_route('home', '/')#,view='picnic.views.redirect_month')#fixme this should provide a website selector
    config.add_route('date','/{accesstype}/{access}/{year}/{month}/{day}/{ampm}/')
    config.scan()
    return config.make_wsgi_app()
