from django.urls import path
from . import consumers
from shock_predictor.consumers import ShockAlertConsumer

websocket_urlpatterns = [
    path("ws/dashboard/", consumers.DashboardConsumer.as_asgi()),
    path("ws/shock/", ShockAlertConsumer.as_asgi()),
]
