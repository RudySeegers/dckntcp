from django.conf.urls import url
from . import views



urlpatterns = [
    url(r'^update/$', views.edit_user, name='console_update'),
    url(r'^$', views.console_first, name='console_first'),
    url(r'^update/saved/$', views.saved, name='saved'),
    url(r'^update/not_saved/$', views.not_saved, name='not_saved'),
    url(r'^arkwalletmain/$', views.console_ark_main, name='console_arkwalletmain'),
    url(r'^arkwalletreceive/$', views.console_ark_receive, name='console_arkwalletreceive'),

]
