from django.conf.urls import *
from django.shortcuts import render_to_response
from django.template import RequestContext
import sys
sys.path.append("..")
from marketwebsocket.decorators import accept_websocket

# from models import User
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

def base_view(request):
    return render_to_response('index1.html', {

    }, context_instance=RequestContext(request))


clients = []

@accept_websocket
def chat(request):
    if request.is_websocket:
        try:
            clients.append(request.websocket)
            for message in request.websocket:
                if not message:
                    break
        #         action = message.split('&')[0]
        #         if action == 'createUser':
        #             pass
        #         elif action == 'chatMessage':
        #             pass
                for client in clients:
                    client.send(message)
        #         request.websocket.send(message)
        finally:
            clients.remove(request.websocket)


urlpatterns = patterns('',
    # Example:
    url(r'^$', base_view),
    url(r'^chat$', chat),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
