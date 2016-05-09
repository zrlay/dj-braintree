# # -*- coding: utf-8 -*-
# """
# .. module:: dj-braintree.contrib.rest_framework.urls
#     :synopsis: dj-braintree url REST routing for Subscription.
#
# .. moduleauthor:: Philippe Luickx (@philippeluickx)
#
# Wire this into the root URLConf this way::
#
#     url(
#         r'^api/v1/stripe/',
#         include('djbraintree.contrib.rest_framework.urls', namespace="rest_djbraintree")
#     ),
#     # url can be changed
#     # Call to 'djbraintree.contrib.rest_framework.urls' and 'namespace' must stay as is
#
# """
#
# from __future__ import unicode_literals
# from django.conf.urls import url
#
# from . import views
#
#
# urlpatterns = [
#
#     # REST api
#     url(
#         r"^subscription/$",
#         views.SubscriptionRestView.as_view(),
#         name="subscription"
#     ),
#
# ]
