import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Poll

class VoteConsumer(AsyncWebsocketConsumer):
    # Called when a WebSocket client tries to connect
    async def connect(self):
        # Extract poll_id from the WebSocket URL route
        self.poll_id = self.scope['url_route']['kwargs']['poll_id']

        # Define a unique room name for this poll's voting session
        self.room_group_name = f'votes_{self.poll_id}'

        # Register this connection with the group (room)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the WebSocket connection
        await self.accept()

        # Send initial vote data immediately on connect (real-time init state)
        await self.send_current_votes()

    # Called when WebSocket disconnects
    async def disconnect(self, close_code):
        # Remove this connection from the poll group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Called when client sends a message (you can define custom actions here)
    async def receive(self, text_data):
        # Currently unused — extend this if clients need to send data (e.g., ping, auth)
        pass

    # Custom handler to receive broadcasted vote updates
    async def vote_update(self, event):
        # This method is triggered by `group_send` elsewhere (e.g., after someone votes)
        # It pushes the updated vote data to the WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'vote_update',
            'total_votes': event['total_votes'],
            'candidate_votes': event['candidate_votes']
        }))

    # Send the current vote snapshot (called right after connect)
    @database_sync_to_async
    def send_current_votes(self):
        """
        This runs in a thread-safe sync context because ORM access must not block async loop.
        It fetches total and per-candidate vote counts for the poll.
        """
        poll = Poll.objects.get(id=self.poll_id)
        return {
            'total_votes': poll.get_total_votes(),
            'candidate_votes': poll.get_candidate_votes()
        }
