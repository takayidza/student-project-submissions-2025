from django.contrib import admin
from .models import AccidentProneArea, History, Alert, Journey, Setting, Prediction
from .models import SafetyNotification

# Register your models here.
admin.site.register(AccidentProneArea)
admin.site.register(History)
admin.site.register(Alert)
admin.site.register(Setting)
admin.site.register(Prediction)
admin.site.register(Journey)
admin.site.register(SafetyNotification)