from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, View
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from .models import AccidentProneArea, Journey, Setting
from .forms import SettingForm
from django.http import JsonResponse
import json
from detection.models import AccidentProneArea
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.decorators.http import require_POST
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Alert
from .models import SafetyNotification

# Create your views here.
class SettingListView(LoginRequiredMixin, ListView):
    model = Setting
    context_object_name = "settings"
    template_name = "setting/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['first_setting'] = Setting.objects.filter(user=self.request.user).first()  # Get the first setting for the logged-in user   
        return context

class SettingCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Setting
    form_class = SettingForm
    template_name = "setting/create.html"
    success_message = "Setting created successfully"

    def form_valid(self, form):
        form.instance.user = self.request.user  # Associate the Setting instance with the logged-in user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("setting_list")

class SettingUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Setting
    form_class = SettingForm
    template_name = "setting/update.html"
    success_message = "Setting updated successfully"
    
    def form_valid(self, form):
        form.instance.user = self.request.user  # Associate the Setting instance with the logged-in user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("setting_list")

class SettingDeleteView(LoginRequiredMixin, SuccessMessageMixin, View):
    def get(self, request, **kwargs):
        obj = get_object_or_404(Setting, pk=kwargs.get("pk"))
        obj.delete()
        messages.success(request, f"{obj} deleted successfully")
        return HttpResponseRedirect(reverse("setting_list"))

class SettingDetailView(LoginRequiredMixin, DetailView):
    model = Setting
    context_object_name = "setting"
    template_name = "setting/detail.html"
    
#accident areas history

class AccidentAreaHistoryListView(LoginRequiredMixin, ListView):
    model = AccidentProneArea
    context_object_name = "accident_areas"
    template_name = "accident_area/index.html"

    def get_queryset(self):
        return AccidentProneArea.objects.filter(accident_prone=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accident_areas_json'] = self.accident_map_view()
        return context

    def accident_map_view(self):
        accident_areas = AccidentProneArea.objects.filter(accident_prone=True).values(
            'latitude', 'longitude', 'description', 'accident_prone'
        )
        return json.dumps(list(accident_areas), cls=DjangoJSONEncoder)
    
class DestinationTemplateView(LoginRequiredMixin, TemplateView):
    context_object_name = "destination"
    template_name = "destination/index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accident_areas_json'] = self.accident_map_view()
        return context

    def accident_map_view(self):
        accident_areas = AccidentProneArea.objects.filter(accident_prone=True).values(
            'latitude', 'longitude', 'description', 'accident_prone'
        )
        return json.dumps(list(accident_areas), cls=DjangoJSONEncoder)

class AlertListView(LoginRequiredMixin, ListView):
    model = Alert
    context_object_name = "alerts"
    template_name = "alert/index.html"

    def get_queryset(self):
        return Alert.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role != "Admin":
            context['alerts'] = self.get_queryset().filter(user=self.request.user)
        else:
            context['alerts'] = self.get_queryset()
        return context
    
class JourneyListView(LoginRequiredMixin, ListView):
    model = Journey # Assuming Journey is related to Alert, replace with Journey model if it exists
    context_object_name = "journeys"
    template_name = "journey/index.html"

    def get_queryset(self):
        return Journey.objects.filter(user=self.request.user)  # Replace with Journey.objects.filter(...) if Journey model exists

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role != "Admin":
            context['journeys'] = self.get_queryset().filter(user=self.request.user)
        else:
            context['journeys'] = self.get_queryset()
        return context

class JourneyStartView(LoginRequiredMixin, SuccessMessageMixin, View):
    def get(self, request, **kwargs):
        obj = get_object_or_404(Journey, pk=kwargs.get("pk"))
        if obj.status == "Started":  # Assuming the Journey model has a 'status' field
            obj.status = "Arrived"
            messages.success(request, f"Journey {obj} status changed to Arrived successfully")
        else:
            obj.status = "Started"
            messages.success(request, f"Journey {obj} status changed to Started successfully")
        obj.save()
        return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

class JourneyDetailView(LoginRequiredMixin, DetailView):
    model = Journey
    context_object_name = "journey"
    template_name = "journey/detail.html"

@csrf_exempt  
@require_POST
@login_required
def create_alert(request):  
    try:
        data = json.loads(request.body)
        message = data.get("message")
        user_id = data.get("user_id")
        start = data.get("start")
        destination = data.get("destination")
        
        #create and alert
        alert = Alert.objects.create(start=start, destination=destination, user=request.user, message=message)
        alert.save()
        
        #create journey
        journey = Journey.objects.create(start=start, destination=destination, user=request.user)
        journey.save()

        return JsonResponse({"status": "success"})
    except Exception as e:
        print(f"Error in create_alert: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)



def latest_alert(request):
    alert = Alert.objects.order_by('-timestamp').first()
    if alert:
        return JsonResponse({
            'message': alert.message,
            'start': alert.start,
            'destination': alert.destination,
            'timestamp': alert.timestamp.isoformat()
        })
    return JsonResponse({'message': None})



from django.views.decorators.http import require_GET

@require_GET
@csrf_exempt  # optional if needed
def safety_alert(request):
    try:
        notification = SafetyNotification.objects.filter(is_read=False).latest('timestamp')
        return JsonResponse({
            'message': notification.message,
            'timestamp': notification.timestamp.isoformat()
        })
    except SafetyNotification.DoesNotExist:
        return JsonResponse({'message': None})
