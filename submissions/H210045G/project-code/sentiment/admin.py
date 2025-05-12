from django.contrib import admin
from .models import (
    SocialMediaPost,
    SocialMediaComment,
    SentimentAnalysisResult,
    Alert,
    Report,
    PostLike
)

# Register your models here.
@admin.register(SocialMediaPost)
class SocialMediaPostAdmin(admin.ModelAdmin):
    list_display = ('platform', 'post_id', 'source', 'created_time')
    search_fields = ('platform', 'post_id', 'source')

@admin.register(SocialMediaComment)
class SocialMediaCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'comment_id', 'username', 'created_time')
    search_fields = ('comment_id', 'username', 'post__post_id')

@admin.register(SentimentAnalysisResult)
class SentimentAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('sentiment', 'confidence_score', 'analyzed_at')
    search_fields = ('sentiment',)

@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('level', 'message', 'triggered_at')
    search_fields = ('level', 'message')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'generated_at')
    search_fields = ('report_type',)

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'liked_at')
    search_fields = ('post__post_id', 'user__username')