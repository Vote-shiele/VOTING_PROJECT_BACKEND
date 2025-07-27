from django.urls import re_path
from . import consumers

# WebSocket URL routing patterns
websocket_urlpatterns = [
    # This route matches WebSocket connections at ws/votes/<poll_id>/
    # <poll_id> is a dynamic part captured as a string (using \w+ = alphanumeric)
    # The connection is handled by VoteConsumer (ASGI consumer)
    re_path(r'ws/votes/(?P<poll_id>\w+)/$', consumers.VoteConsumer.as_asgi()),
]
