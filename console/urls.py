from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^update/$', views.render_settings, name='console_update'),
    url(r'^$', views.console_node, name='console_node'),
    url(r'^update/saved/$', views.saved, name='saved'),
    url(r'^update/not_saved/$', views.not_saved, name='not_saved'),
    url(r'^payoutreport/@(?P<ark_address>[\w.@+-]+)$', views.payout_report, name='console_payout_report'),
    url(r'^balancereport/@(?P<ark_address>[\w.@+-]+)$', views.balance_report, name='console_balance_report'),
    url(r'^roireport/@(?P<ark_address>[\w.@+-]+)$', views.roi_report, name='console_roi_report'),

    url(r'^arkdelegatereport/$', views.delegate_report, name='console_ark_delegate_report'),
    url(r'^save_general_settings/$', views.save_settings, name='save_general'),
    url(r'^save_account_settings/$', views.save_account_settings, name='save_account_settings'),

]
