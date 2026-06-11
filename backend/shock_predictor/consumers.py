import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ShockAlertConsumer(AsyncWebsocketConsumer):
    """WebSocket: ws://host/ws/shock/ — live shock score updates."""

    async def connect(self):
        await self.channel_layer.group_add("shock_alerts", self.channel_name)
        await self.accept()
        from shock_predictor.scoring import get_current_score
        current = get_current_score()
        await self.send(text_data=json.dumps(current))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("shock_alerts", self.channel_name)

    async def shock_update(self, event):
        await self.send(text_data=json.dumps(event.get('data', {})))
