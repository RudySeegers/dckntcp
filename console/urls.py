from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^update/$', views.edit_user, name='console_update'),
    url(r'^$', views.console_node, name='console_node'),
    url(r'^update/saved/$', views.saved, name='saved'),
    url(r'^update/not_saved/$', views.not_saved, name='not_saved'),
    url(r'^payoutreport/@(?P<ark_address>[\w.@+-]+)$', views.payout_report, name='console_payout_report'),
    url(r'^balancereport/@(?P<ark_address>[\w.@+-]+)$', views.balance_report, name='console_balance_report'),

    url(r'^arkdelegatereport/$', views.delegate_report, name='console_ark_delegate_report'),

]
