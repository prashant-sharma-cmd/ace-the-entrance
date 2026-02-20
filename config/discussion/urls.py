from django.urls import path
from discussion import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'forum'
urlpatterns = [
    # Page
    path('', views.IndexPageView.as_view(), name='index' ),

    # API
    path("api/threads/", views.ThreadListView.as_view(), name="api-threads"),
    path("api/threads/<int:pk>/", views.ThreadDetailView.as_view(),
         name="api-thread-detail"),
    path("api/threads/<int:pk>/replies/", views.ReplyListView.as_view(),
         name="api-replies"),
    path("api/threads/<int:pk>/like/", views.ThreadLikeView.as_view(),
         name="api-thread-like"),
    path("api/replies/<int:pk>/like/", views.ReplyLikeView.as_view(),
         name="api-reply-like"),
]

# Development Only. In production, serve /media/ via Nginx or an S3 bucket instead.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
