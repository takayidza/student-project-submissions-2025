from django.db import models
from django.contrib.auth import get_user_model

CustomUser = get_user_model()  # Reference to the CustomUser model

class SocialMediaPost(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="posts", null=True, blank=True)  
    platform = models.CharField(
        max_length=20, choices=[('facebook', 'Facebook'), ('instagram', 'Instagram')]
    )
    post_id = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField()
    translated_message = models.TextField(null=True, blank=True)  
    sentiment = models.CharField(max_length=20, null=True, blank=True)  
    created_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    image = models.ImageField(upload_to='attachments/', null=True, blank=True)
    source = models.CharField(max_length=255)  

    def __str__(self):
        return f"{self.platform.capitalize()} Post by {self.user} at {self.created_time}"
    
    def total_likes(self):
        """Returns the total number of likes for this post."""
        return PostLike.objects.filter(post=self).count()
    
    def comments(self):
        """Returns the comments related to this post."""
        return SocialMediaComment.objects.filter(post=self)
    
    def total_comments(self):
        """Returns the total number of comments for this post."""
        return self.comments.count()


class SocialMediaComment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="comments", null=True, blank=True)  
    post = models.ForeignKey(SocialMediaPost, on_delete=models.CASCADE, related_name="comments")
    comment_id = models.CharField(max_length=255, null=True, blank=True)
    text = models.TextField()
    translated_text = models.TextField(null=True, blank=True)  
    sentiment = models.CharField(max_length=20, null=True, blank=True)  
    created_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    username = models.CharField(max_length=255)

    def __str__(self):
        return f"Comment by {self.username} on {self.created_time}"
    
    def sentiment(self):
        sentiment_analysis = SentimentAnalysisResult.objects.filter(comment=self).first()
        return sentiment_analysis


class SentimentAnalysisResult(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sentiment_results", null=True, blank=True)  
    post = models.ForeignKey(SocialMediaPost, on_delete=models.CASCADE, related_name="sentiment_analysis", null=True, blank=True)
    comment = models.ForeignKey(SocialMediaComment, on_delete=models.CASCADE, related_name="sentiment_analysis", null=True, blank=True)
    sentiment = models.CharField(max_length=20, choices=[
        ('positive', 'Positive'), ('neutral', 'Neutral'), ('negative', 'Negative')
    ])
    confidence_score = models.FloatField()  
    analyzed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sentiment Analysis for {self.post or self.comment} - {self.sentiment}"

    def get_related_content(self):
        """Returns the related post or comment for easy retrieval."""
        return f"Post Message: {self.post.message if self.post else 'No related content'}, Comment Text: {self.comment.text if self.comment else 'No related content'}, Translated Message: {self.comment.translated_text if self.comment else 'No translated message'}"


class Alert(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="alerts", null=True, blank=True)  
    sentiment_result = models.ForeignKey(SentimentAnalysisResult, on_delete=models.CASCADE)
    level = models.CharField(max_length=10, choices=[
        ('critical', 'Critical'), ('warning', 'Warning'), ('info', 'Info')
    ])
    message = models.TextField()
    triggered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert [{self.level.upper()}]: {self.message}"


class Report(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reports", null=True, blank=True)  
    report_type = models.CharField(max_length=50)  
    generated_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField()  

    def __str__(self):
        return f"Report ({self.report_type}) - {self.generated_at}"

class PostLike(models.Model):
    post = models.ForeignKey(SocialMediaPost, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')  # Prevents duplicate likes
