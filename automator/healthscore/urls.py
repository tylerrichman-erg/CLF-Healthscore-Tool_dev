from django.urls import path, include, re_path
from django.contrib import admin
from django.views.generic.base import RedirectView
from . import views

favicon_view = RedirectView.as_view(url='/static/healthscore/favicon.ico', permanent=True)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('start', views.index),
    path('download', views.download_healthscore, name='download'),
    path('save', views.save_healthscore, name='save'),
    path('save_title', views.save_healthscore_title, name='save_title'),
    path('delete', views.delete_healthscore, name='delete'),
    path('saved', views.my_scorecards, name='saved'),
    path('settings', views.settings, name='settings'),
    path('tracts', views.tracts, name='tracts'),
    path('select_tracts', views.select_tracts, name='select_tracts'),
    path("accounts/", include("django.contrib.auth.urls")),
    path('about', views.about, name='about'),
    re_path(r'^favicon\.ico$', favicon_view),
]
