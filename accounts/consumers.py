import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Poll

class VoteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.poll_id = self.scope['url_route']['kwargs']['poll_id']
        self.room_group_name = f'votes_{self.poll_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial data on connect
        await self.send_current_votes()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle incoming messages if needed
        pass

    async def vote_update(self, event):
        # Send updated vote data to client
        await self.send(text_data=json.dumps({
            'type': 'vote_update',
            'total_votes': event['total_votes'],
            'candidate_votes': event['candidate_votes']
        }))

    @database_sync_to_async
    def send_current_votes(self):
        poll = Poll.objects.get(id=self.poll_id)
        return {
            'total_votes': poll.get_total_votes(),
            'candidate_votes': poll.get_candidate_votes()
        }