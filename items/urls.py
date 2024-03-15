from django.urls import path

from . import views

urlpatterns =  [
    path("", views.index, name="index"),
    path("items", views.items, name="items"),
    path("export", views.export, name="export"),
    path("gaps", views.gaps, name="gaps"),
    path("item/<int:id>", views.item, name="item"),
    path("item/<str:name>", views.itemByName, name="itemByName"),
    path("exportSet", views.exportSet, name="exportSet")
]