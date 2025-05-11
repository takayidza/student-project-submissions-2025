<?php

namespace App\Notifications;

use Illuminate\Bus\Queueable;
use Illuminate\Notifications\Notification;
use Illuminate\Notifications\Messages\DatabaseMessage;

class DocumentStatusChanged extends Notification
{
    use Queueable;

    protected $document;

    public function __construct($document)
    {
        $this->document = $document;
    }

    public function via($notifiable)
    {
        return ['database'];
    }

    public function toDatabase($notifiable)
    {
        $token = $this->document->uploader->createToken('auth_token')->plainTextToken;
        $url = url("/documents/{$this->document->id}?authenticate={$token}");

        return new DatabaseMessage([
            'document_id' => $this->document->id,
            'title' => $this->document->title,
            'status_advanced' => $this->document->status,
            'url' => route('dashboard', $this->document),
            'message' => "Your submission “{$this->document->title}” status advanced to “{$this->document->status}”. Use the following link to track your document progress {$url}",
        ]);
    }
}