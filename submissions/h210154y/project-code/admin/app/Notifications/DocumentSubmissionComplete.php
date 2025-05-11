<?php

namespace App\Notifications;

use Illuminate\Notifications\Notification;
use Illuminate\Notifications\Messages\MailMessage;
use App\Models\Document;

class DocumentSubmissionComplete extends Notification
{
    protected Document $document;

    public function __construct(Document $document)
    {
        $this->document = $document;
    }

    public function via($notifiable)
    {
        return ['mail', 'database']; // mail to send email, database if you want in-app notifications too
    }

    public function toMail($notifiable)
    {
        $token = $this->document->uploader->createToken('auth_token')->plainTextToken;
        $url = url("/documents/{$this->document->id}?authenticate={$token}");

        return (new MailMessage)
            ->greeting("Hello, {$notifiable->name}")
            ->line("Your recent submission titled \"{$this->document->title}\" was successfully submitted and auto-tagged into \"{$this->document->category}\".")
            ->line('It is now set for human review.')
            ->action('Track Your Document', $url)
            ->line('Thank you for using our platform!');
    }

    public function toArray($notifiable)
    {
        return [
            'document_id' => $this->document->id,
            'title' => $this->document->title,
            'document_type' => $this->document->document_type,
        ];
    }
}