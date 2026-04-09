from django.urls import path
from discussion import views

app_name = 'forum'
urlpatterns = [
    # Page
    path('', views.IndexPageView.as_view(), name='index' ),

    # API
    path("api/threads/", views.ThreadListView.as_view(), name="api-threads"),
    path("api/threads/<int:pk>/replies/", views.ReplyListView.as_view(),
         name="api-replies"),
    path("api/threads/<int:pk>/like/", views.ThreadLikeView.as_view(),
         name="api-thread-like"),
    path("api/replies/<int:pk>/like/", views.ReplyLikeView.as_view(),
         name="api-reply-like"),
    path("api/threads/<int:pk>/", views.ThreadDetailEditView.as_view(),
         name="api-thread-edit"),
    path("api/replies/<int:pk>/", views.ReplyDetailEditView.as_view(),
         name="api-reply-edit"),
]
