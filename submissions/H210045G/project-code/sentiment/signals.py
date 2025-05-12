from django.db.models.signals import post_save
from django.dispatch import receiver
from textblob import TextBlob

from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_save
from django.dispatch import receiver
from googletrans import Translator

from sentiment.models.social_media import SocialMediaPost
from .models import SocialMediaComment # import any other models that need translation
from accounts.models import CustomUser
from .models import SentimentAnalysisResult, Alert
from django.utils.timezone import now
from sentiment.helpers.global_email_sender import send_email_from_global_config
from .models import SocialMediaComment, SentimentAnalysisResult

@receiver(post_save, sender=SocialMediaComment)
def analyze_sentiment_on_comment(sender, instance, created, **kwargs):
    if created:  # Ensure sentiment analysis is done only when a new comment is created
        # Perform sentiment analysis using TextBlob
        blob = TextBlob(instance.text)
        polarity = blob.sentiment.polarity
        
        # Determine sentiment based on polarity score
        if polarity > 0:
            sentiment = 'positive'
        elif polarity == 0:
            sentiment = 'neutral'
        else:
            sentiment = 'negative'
        
        # Create SentimentAnalysisResult
        SentimentAnalysisResult.objects.create(
            user=instance.user,
            post=instance.post,
            comment=instance,
            sentiment=sentiment,
            confidence_score=abs(polarity),  # Using absolute value of polarity for confidence score
            analyzed_at=instance.created_time
        )


@receiver(post_save, sender=SentimentAnalysisResult)
def create_alert_and_send_email(sender, instance, created, **kwargs):
    if created:  # Ensure the alert is created only when the sentiment analysis result is saved
        # Check if the sentiment is 'negative' or 'critical' sentiment
        if instance.sentiment == 'negative':
            # Create an alert
            alert_message = f"A negative sentiment was detected for the comment on post: {instance.get_related_content()}"
            alert = Alert.objects.create(
                user=instance.user,
                sentiment_result=instance,
                level='critical',
                message=alert_message,
            )
            
            # Find the system superuser
            superuser = CustomUser.objects.filter(is_superuser=True).first()
            
            if superuser:
                superuser_email = superuser.email

                # If we have a superuser, send an email
                if superuser_email:
                    email_subject = "Critical Sentiment Alert Detected"
                    email_content = f"A negative sentiment was detected in a comment. Details:\n\n{alert_message}\n\nPlease check the system."
                    
                    # Send email to superuser
                    send_email_from_global_config(
                        email_subject=email_subject,
                        user=superuser.username,
                        email_content=email_content,
                        recipient_email=superuser_email
                    )


#post comment translation
@receiver(pre_save, sender=SocialMediaComment)
def translate_comment_text(sender, instance, **kwargs):
    if instance.user and instance.user.language and instance.text:
        if not instance.translated_text or instance.translated_text == instance.text:
            try:
                translator = Translator()
                translation = translator.translate(instance.text, dest=instance.user.language)
                instance.translated_text = translation.text
            except Exception as e:
                print("Translation failed:", e)

@receiver(post_save, sender=CustomUser)
def retranslate_user_comments_on_language_change(sender, instance, **kwargs):
    if instance.language:
        comments = instance.comments.all()
        translator = Translator()
        for comment in comments:
            if comment.text:
                try:
                    translation = translator.translate(comment.text, dest=instance.language)
                    comment.translated_text = translation.text
                    comment.save(update_fields=["translated_text"])
                except Exception as e:
                    print("Translation failed on re-translate:", e)



# Post message translation before saving the SocialMediaPost
@receiver(pre_save, sender=SocialMediaPost)
def translate_post_message(sender, instance, **kwargs):
    if instance.user and instance.user.language and instance.message:
        # Only translate if translated_message is empty or needs an update
        if not instance.translated_message or instance.translated_message == instance.message:
            try:
                translator = Translator()
                translation = translator.translate(instance.message, dest=instance.user.language)
                instance.translated_message = translation.text  # Corrected property
            except Exception as e:
                print(f"Translation failed: {e}")

# Retranslate posts when the user's language changes
@receiver(post_save, sender=CustomUser)
def retranslate_user_posts_on_language_change(sender, instance, **kwargs):
    if instance.language:
        posts = instance.posts.all()
        translator = Translator()
        for post in posts:
            if post.message:
                try:
                    # Translate each post message into the new language
                    translation = translator.translate(post.message, dest=instance.language)
                    post.translated_message = translation.text  # Corrected property
                    post.save(update_fields=["translated_message"])  # Save only the translated message
                except Exception as e:
                    print(f"Translation failed on re-translate: {e}")
