from django.conf.urls import url
from documents import views

urlpatterns = [
    url(r'^ToS/$', views.render_tos, name='docs_tos'),
    url(r'^proposal/$', views.render_prop, name='docs_prop'),
    url(r'^FAQ/$', views.render_faq, name='docs_faq'),
]


