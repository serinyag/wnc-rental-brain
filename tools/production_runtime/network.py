"""Fixed provider hosts and no redirects for production credential transport."""
import urllib.request
from urllib.parse import urlsplit
class NoProviderRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('provider_redirect_forbidden')

def open_provider(request,*,timeout,context):
    url=urlsplit(request.full_url)
    if (url.scheme!='https' or url.hostname not in ('graph.microsoft.com','login.microsoftonline.com','app.asana.com')
        or url.username or url.port not in (None,443) or url.fragment):raise ValueError('provider_host_forbidden')
    return urllib.request.build_opener(NoProviderRedirect(),urllib.request.HTTPSHandler(context=context)).open(request,timeout=timeout)
