from django.contrib import admin
from .models import ShockEvent, ShockPrecursorPattern, ShockAlert

admin.site.register(ShockEvent)
admin.site.register(ShockPrecursorPattern)
admin.site.register(ShockAlert)
