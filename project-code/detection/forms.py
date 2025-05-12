from django import forms
from .models import AccidentProneArea, History, Alert, Setting, Prediction

class AccidentProneAreaForm(forms.ModelForm):
    class Meta:
        model = AccidentProneArea
        exclude = ["created_at"]

    def __init__(self, *args, **kwargs):
        super(AccidentProneAreaForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

class HistoryForm(forms.ModelForm):
    class Meta:
        model = History
        exclude = ["timestamp"]

    def __init__(self, *args, **kwargs):
        super(HistoryForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        exclude = ["timestamp"]

    def __init__(self, *args, **kwargs):
        super(AlertForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

class SettingForm(forms.ModelForm):
    class Meta:
        model = Setting
        exclude = ["user"]

    def __init__(self, *args, **kwargs):
        super(SettingForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    "class": "form-check-input",
                })
            else:
                field.widget.attrs["class"] = "form-control"

class PredictionForm(forms.ModelForm):
    class Meta:
        model = Prediction
        exclude = ["timestamp"]

    def __init__(self, *args, **kwargs):
        super(PredictionForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"