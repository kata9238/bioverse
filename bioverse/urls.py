from django.conf.urls import url

from . import views
from bioverse.views import Protein

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^protein/', Protein.as_view())
]
