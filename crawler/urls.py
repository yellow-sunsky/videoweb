# videoweb/crawler/urls.py
from django.urls import path
from .views import start_crawling

urlpatterns = [
    path('start_crawling/', start_crawling, name='start_crawling'),
]