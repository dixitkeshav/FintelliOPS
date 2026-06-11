from django.urls import path
from . import views

urlpatterns = [
    path('score/', views.current_score),
    path('universe/', views.shock_universe),
    path('live-scan/', views.live_move_scan),
    path('history/', views.shock_history),
    path('alerts/', views.alert_log),
    path('patterns/', views.precursor_patterns),
]
