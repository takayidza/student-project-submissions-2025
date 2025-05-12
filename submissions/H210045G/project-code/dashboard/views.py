from logging import info
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib import messages

from sentiment.models.social_media import Alert, SentimentAnalysisResult, SocialMediaPost

from django.utils.timezone import now
from django.db.models import Count
from datetime import datetime, timedelta

class DashboardListView(TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = now()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        days = [(start_of_month + timedelta(days=i)).day for i in range((end_of_month - start_of_month).days + 1)]
        sentiment_data = {
            'positive': [0] * len(days),
            'neutral': [0] * len(days),
            'negative': [0] * len(days),
        }

        queryset = SentimentAnalysisResult.objects.filter(analyzed_at__month=today.month)

        for entry in queryset:
            day = entry.analyzed_at.day
            index = day - 1
            sentiment_data[entry.sentiment][index] += 1

        context['chart_labels'] = days
        context['sentiment_data'] = sentiment_data

        # Keep your existing context
        context['total_posts'] = SocialMediaPost.objects.count()
        context['total_alerts'] = Alert.objects.count()
        context['total_positive'] = SocialMediaPost.objects.filter(sentiment_analysis__sentiment='positive').count()
        context['total_negative'] = SocialMediaPost.objects.filter(sentiment_analysis__sentiment='negative').count()
        context['all_posts'] = SocialMediaPost.objects.all()
        context['all_alerts'] = Alert.objects.all()

        return context
