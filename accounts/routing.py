from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/votes/(?P<poll_id>\w+)/$', consumers.VoteConsumer.as_asgi()),
]