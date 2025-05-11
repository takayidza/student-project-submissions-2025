<?php

namespace App\Notifications;

use Illuminate\Bus\Queueable;
use Illuminate\Notifications\Notification;
use Illuminate\Notifications\Messages\DatabaseMessage;

class DocumentClassified extends Notification
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
        return new DatabaseMessage([
            'document_id' => $this->document->id,
            'title' => $this->document->title,
            'classified_as' => $this->document->category,
            'url' => route('dashboard', $this->document),
            'message' => "Your “{$this->document->title}” was auto-tagged into “{$this->document->category}” category.",
        ]);
    }
}