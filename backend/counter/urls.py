from django.urls import path
from . import views


urlpatterns = [
    path("start/", views.StartCounterView.as_view(), name="start_counter"),
    path("stop/", views.StopCounterView.as_view(), name="stop_counter"),
    path("video_feed/", views.video_feed, name="video_feed"),
    path("count/", views.GetCountView.as_view(), name="get_count"),
    path("update_line/", views.UpdateLineSettingsView.as_view(), name="update_line"),
    path("start_counting/", views.StartCountingView.as_view(), name="start_counting"),
]
