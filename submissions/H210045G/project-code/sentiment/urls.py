from django import views
from django.urls import path
from .views import SocialMediaPostListView, SocialMediaCommentListView, comment_post, create_post, export_report_view, like_post

urlpatterns = [
    path('posts/', SocialMediaPostListView.as_view(), name='social_media_post_list'),
    path('comments/', SocialMediaCommentListView.as_view(), name='social_media_comment_list'),
    path('create-post/', create_post, name='create_post'),
    path('like/', like_post, name='like_post'),
    path('comment/', comment_post, name='comment_post'),
    path('export-report/', export_report_view, name='export_report'),
]
