from django.urls import path

from .views import (
    learning_health,
    learning_learners,
    learning_teams,
    learning_run,
    learning_iq_status,
    learning_docs,
)

urlpatterns = [
    path("api/learning/health/", learning_health, name="learning_health"),
    path("api/learning/learners/", learning_learners, name="learning_learners"),
    path("api/learning/teams/", learning_teams, name="learning_teams"),
    path("api/learning/run/", learning_run, name="learning_run"),
    path("api/learning/iq/", learning_iq_status, name="learning_iq_status"),
    path("api/learning/docs/", learning_docs, name="learning_docs"),
]
