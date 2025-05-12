from django import forms
from .models import SocialMediaPost, SocialMediaComment, SentimentAnalysisResult, Alert, Report

class SocialMediaPostForm(forms.ModelForm):
    class Meta:
        model = SocialMediaPost
        fields = ["message", "image"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"


class SocialMediaCommentForm(forms.ModelForm):
    class Meta:
        model = SocialMediaComment
        fields = ["text"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"


class SentimentAnalysisResultForm(forms.ModelForm):
    class Meta:
        model = SentimentAnalysisResult
        fields = ["user", "post", "comment", "sentiment", "confidence_score"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"


class AlertForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ["user", "sentiment_result", "level", "message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["user", "report_type", "content"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"
            
# forms.py
from django import forms

class ReportFilterForm(forms.Form):
    REPORT_CHOICES = [
        ('sentiment', 'Sentiment Analysis'),
        ('posts', 'Posts'),
        ('comments', 'Comments'),
        ('alerts', 'Alerts'),
    ]
    report_type = forms.ChoiceField(choices=REPORT_CHOICES)
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
