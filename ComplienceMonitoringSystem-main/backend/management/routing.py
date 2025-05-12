from django.urls import re_path

from . import consumers, server_consumer

websocket_urlpatterns = [
    re_path(r"ws/chat/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/monitoring/$", consumers.MonitoringConsumer.as_asgi()),
    re_path(r'ws/device-tracker/$', consumers.DeviceDataConsumer.as_asgi()),
    re_path(r'ws/client-monitoring/$', server_consumer.MonitoringConsumer.as_asgi()),
]