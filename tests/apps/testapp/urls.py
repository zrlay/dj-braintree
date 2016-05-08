from __future__ import unicode_literals
from django.conf.urls import url, include

from django.http import HttpResponse


def empty_view(request):
    return HttpResponse()

urlpatterns = [
    url(
        r"^$",
        empty_view,
        name="test_url_name"
    ),
    url(r"^djbraintree/", include('djbraintree.urls', namespace="djbraintree")),
    url(
        r"^rest_djbraintree/",
        include('djbraintree.contrib.rest_framework.urls', namespace="rest_djbraintree")
    ),
]
