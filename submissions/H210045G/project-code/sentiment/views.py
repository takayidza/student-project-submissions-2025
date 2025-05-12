from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView
from .models import SocialMediaPost, SocialMediaComment
from django.shortcuts import render, redirect
from .forms import SocialMediaCommentForm, SocialMediaPostForm
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import datetime
import openpyxl
from django.http import HttpResponse
from .forms import ReportFilterForm
from .models import SocialMediaPost, SocialMediaComment, SentimentAnalysisResult, Alert, PostLike

# Create your views here.
class SocialMediaPostListView(ListView):
    model = SocialMediaPost
    template_name = "social_media_post/list.html"
    context_object_name = "posts"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['post_form'] = SocialMediaPostForm()
        context['comment_form'] = SocialMediaCommentForm()
        context['system_posts'] = SocialMediaPost.objects.filter(source="SYSTEM")
        return context

class SocialMediaCommentListView(ListView):
    model = SocialMediaComment
    template_name = "social_media_comment/list.html"
    context_object_name = "comments"
    
def create_post(request):
    if request.method == 'POST':
        form = SocialMediaPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user 
            post.source = "SYSTEM"
            post.save()
            return redirect(request.META.get("HTTP_REFERER", "/"))  # Return to same page
    else:
        form = SocialMediaPostForm()
    return render(request, 'your_template.html', {'form': form})

@require_POST
@login_required
def like_post(request):
    post_id = request.POST.get('post_id')
    post = get_object_or_404(SocialMediaPost, id=post_id)

    # Check if the user already liked the post, if yes, delete the like, else create a new like
    like, created = PostLike.objects.get_or_create(user=request.user, post=post)

    if not created:
        like.delete()  # Remove the like if it already exists
        liked = False
    else:
        liked = True  # Add the like

    # Get the updated like count for the post
    like_count = PostLike.objects.filter(post=post).count()

    # Return the updated like status and like count
    return JsonResponse({'liked': liked, 'like_count': like_count})


@require_POST
@login_required
@login_required
def comment_post(request):
    post_id = request.POST.get('post_id')
    post = get_object_or_404(SocialMediaPost, id=post_id)
    
    form = SocialMediaCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.user = request.user
        # No need to assign a custom comment_id, let Django handle it
        comment.save()

        # Allow multiple comments by redirecting back to the same page
        return redirect(request.META.get("HTTP_REFERER", "/"))  

    return JsonResponse({'success': False, 'errors': form.errors})


def export_report_view(request):
    form = ReportFilterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        report_type = form.cleaned_data['report_type']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

        wb = openpyxl.Workbook()
        ws = wb.active

        if report_type == 'sentiment':
            ws.title = "Sentiment Analysis"
            queryset = SentimentAnalysisResult.objects.filter(analyzed_at__range=[start_date, end_date])
            ws.append(['User', 'Post', 'Comment', 'Sentiment', 'Confidence Score', 'Analyzed At'])
            for item in queryset:
                ws.append([
                    str(item.user),
                    str(item.post),
                    str(item.comment),
                    item.sentiment,
                    item.confidence_score,
                    item.analyzed_at.strftime('%Y-%m-%d %H:%M:%S'),
                ])

        elif report_type == 'posts':
            ws.title = "Posts"
            queryset = SocialMediaPost.objects.filter(created_time__range=[start_date, end_date])
            ws.append(['User', 'Text', 'Created Time'])
            for item in queryset:
                ws.append([
                    str(item.user),
                    item.message,
                    item.created_time.strftime('%Y-%m-%d %H:%M:%S') if item.created_time else '',
                ])

        elif report_type == 'comments':
            ws.title = "Comments"
            queryset = SocialMediaComment.objects.filter(created_time__range=[start_date, end_date])
            ws.append(['User', 'Post', 'Text', 'Sentiment', 'Created Time'])
            for item in queryset:
                ws.append([
                    str(item.user),
                    str(item.post),
                    item.text,
                    item.sentiment,
                    item.created_time.strftime('%Y-%m-%d %H:%M:%S') if item.created_time else '',
                ])

        elif report_type == 'alerts':
            ws.title = "Alerts"
            queryset = Alert.objects.filter(triggered_at__range=[start_date, end_date])
            ws.append(['User', 'Level', 'Message', 'Triggered At'])
            for item in queryset:
                ws.append([
                    str(item.user),
                    item.level,
                    item.message,
                    item.triggered_at.strftime('%Y-%m-%d %H:%M:%S'),
                ])

        # Create HTTP response
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f"{report_type}_report_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename={filename}'
        wb.save(response)
        return response

    return render(request, 'report/export_form.html', {'form': form})
