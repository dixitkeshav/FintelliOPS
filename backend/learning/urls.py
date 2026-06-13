from django.urls import path

from . import views

urlpatterns = [
    path("run/", views.learning_run, name="learning_run"),
    path("health/", views.learning_health, name="learning_health"),
    path("status/", views.learning_status, name="learning_status"),
    path("learners/", views.learning_learners, name="learning_learners"),
    path("topics/", views.learning_topics, name="learning_topics"),
]
