from django.conf.urls import url
from . import views



urlpatterns = [
    url(r'^update/$', views.edit_user, name='console_update'),
    url(r'^$', views.console_node, name='console_node'),
    url(r'^update/saved/$', views.saved, name='saved'),
    url(r'^update/not_saved/$', views.not_saved, name='not_saved'),
    url(r'^arkwalletmain/$', views.console_payout_report_ark_wallet_main, name='console_payout_report_arkwalletmain'),
    url(r'^arkwalletsec/$', views.console_payout_report_ark_wallet_sec, name='console_payout_report_arkwalletsec'),
    url(r'^arkdelegatereport/$', views.delegate_report, name='console_ark_delegate_report'),

]
