from logging import info
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib import messages
from django.db.models import Count
import json
from detection.models import AccidentProneArea, Alert, Journey
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse

class DashboardListView(TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['accident_areas_json'] = self.accident_map_view()
        
        if self.request.user.role != "Admin":
            context['alerts'] = Alert.objects.filter(user=user)
            context['journeys'] = Journey.objects.filter(user=user)  # Assuming Journey is related to Alert, replace with Journey model if it exists    
            pending_journeys = Journey.objects.filter(user=user, status='Pending')
            started_journeys = Journey.objects.filter(user=user, status='Started')
            completed_journeys = Journey.objects.filter(user=user, status='Arrived')
            
            context['pending_journeys_count'] = pending_journeys.count()
            context['completed_journeys_count'] = completed_journeys.count()
            context['started_journeys_count'] = started_journeys.count()
            context['pending_journeys_list'] = pending_journeys
            context['completed_journeys_list'] = completed_journeys
            context['started_journeys_list'] = started_journeys
        else:
            context['alerts'] = Alert.objects.all()
            context['journeys'] = Journey.objects.all()
            
            pending_journeys = Journey.objects.filter(status='Pending')
            started_journeys = Journey.objects.filter(status='Started')
            completed_journeys = Journey.objects.filter(status='Arrived')
            
            context['pending_journeys_count'] = pending_journeys.count()
            context['completed_journeys_count'] = completed_journeys.count()
            context['started_journeys_count'] = started_journeys.count()
            context['pending_journeys_list'] = pending_journeys
            context['completed_journeys_list'] = completed_journeys
            context['started_journeys_list'] = started_journeys
            
        return context

    def accident_map_view(self):
        accident_areas = AccidentProneArea.objects.values(
            'latitude', 'longitude', 'description', 'accident_prone'
        )
        return json.dumps(list(accident_areas), cls=DjangoJSONEncoder)
