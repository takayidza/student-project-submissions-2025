<?php

namespace App\Jobs;

use App\Models\Document;
use App\Notifications\DocumentClassified;
use App\Notifications\DocumentStatusChanged;
use App\Notifications\DocumentSubmissionComplete;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class ProcessPDFCategory implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, SerializesModels, Queueable;
    protected int $documentId;
    protected string $fileId;
    /**
     * @param  int     $documentId  The id ID of the document record
     * @param  string  $fileId   The file id to be used for classification 
     */
    public function __construct(int $documentId, string $fileId)
    {
        $this->documentId = $documentId;
        $this->fileId = $fileId;
    }


    public function handle(): void
    {
        try {
            $baseURL = env('AI_API_URL');
            $document = Document::findOrFail($this->documentId);
            Log::info("Auto-tagging document: {$document->title}");
            Log::info("Using file_id: {$this->fileId}");

            $mlcResp = Http::withToken(env('AI_SERVICE_TOKEN'))->withHeaders([
                'Accept' => 'application/json',
                'Content-Type' => 'application/json',
            ])->post("{$baseURL}/mlc", [
                        'file_ids' => [$this->fileId],
                    ]);


            if (!$mlcResp->successful()) {
                Log::error('failed to create classification request: ' . $mlcResp->body());
            }

            $fileEntry = $mlcResp->json('file_ids.0');
            $requestId = data_get($fileEntry, 'request_id');
            Log::info('mlc request_id: ' . $requestId);

            $timeout = now()->addMinutes(3);
            $interval = 5; // seconds

            do {
                sleep($interval);

                $pollResp = Http::withToken(env('AI_SERVICE_TOKEN'))->withHeaders(['Accept' => 'application/json'])
                    ->get($baseURL . "/mlc/{$requestId}");

                Log::info('MLC poll status: ' . $pollResp->status());
                Log::info('MLC poll body: ' . $pollResp->body());

                if (!$pollResp->successful()) {
                    Log::error('Polling error: ' . $pollResp->body());
                }
                $status = $pollResp->json('status');
            } while ($status === 'processing' && now()->lt($timeout));

            if ($status !== 'complete') {
                Log::error("Classification did not complete (status: {$status})");
            }

            $levels = $pollResp->json('classifications', []);
            Log::info('levels', $levels);
            $docType = $levels[1] ?? $levels[0] ?? 'classification-failed';
            $document->file_id = $this->fileId;
            $document->classifications = $levels;
            $document->status = 'categorised';
            $document->category = $docType;
            $document->save();

            $document->uploader->notify(new DocumentStatusChanged($document));
            $document->uploader->notify(new DocumentClassified($document));
            $document->uploader->notify(new DocumentSubmissionComplete($document));
        } catch (\Exception $e) {
            Log::error($e->getMessage());
        }
    }
}