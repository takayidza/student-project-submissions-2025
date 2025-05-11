<?php

namespace App\Http\Controllers;

use App\Jobs\ProcessPDFCategory;
use App\Models\Comment;
use App\Models\Document;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;
use Inertia\Inertia;

class DocumentController extends Controller
{
    public function index()
    {
        if (!auth()->user()->can('view-documents')) {
            return redirect()->back()->withErrors(['permission' => 'You do not have permission to create departments.']);
        }
        $documents = Document::with('uploader')->latest()->get();
        return Inertia::render('documents', [
            'documents' => $documents
        ]);
    }
    public function upload(Request $request): RedirectResponse
    {
        $request->validate([
            'title' => 'required|string|max:255',
            'description' => 'nullable|string',
            'file' => 'required|file|max:2048', // Max 2MB
            'category' => 'nullable|string',
            'department_id' => 'nullable|exists:departments,id',
        ]);

        $file = $request->file('file');

        $uploadResp = Http::withToken(env('AI_SERVICE_TOKEN'))->withHeaders([
            'Accept' => 'application/json',
            'Content-Type' => 'application/octet-stream',
        ])
            ->send('POST', env('AI_API_URL') . '/files', [
                'body' => file_get_contents($file->getRealPath()),
            ]);

        if (!$uploadResp->successful()) {
            Log::error('Fail to upload file to AI service' . $uploadResp->body());
            return redirect()->back()->withErrors('error', 'File upload failed, please try again');
        }

        $fileId = $uploadResp->json('file_id');

        $fileName = time() . '_' . $file->getClientOriginalName();
        $filePath = $file->storeAs('uploads', $fileName, 'public');

        $document = Document::create([
            'title' => $request->title,
            'description' => $request->description,
            'file_path' => $filePath,
            'file_name' => $fileName,
            'file_type' => $file->getClientMimeType(),
            'file_size' => $file->getSize(),
            'category' => $request->category ?? 'Unclassified',
            'uploaded_by' => auth()->id(),
            'department_id' => $request->department_id,
        ]);

        $document->document_url = asset('storage/' . $document->file_path);

        ProcessPDFCategory::dispatch($document->id, $fileId);

        return to_route('dashboard');
    }

    public function update(Request $request, $id): RedirectResponse
    {
        $request->validate([
            'status' => 'required|string|max:255',
        ]);

        $document = Document::findOrFail($id);
        $document->status = $request->status;
        $document->save();

        Comment::create([
            'document_id' => $document->id,
            'user_id' => auth()->id(),
            'action' => 'Status Updated',
            'message' => 'Document status updated to "' . $request->status . '" by ' . auth()->user()->name,
            'color' => 'green'
        ]);

        return redirect()->route('documents')->with('success', 'Document status updated.');
    }


    public function show($id)
    {
        $document = Document::with(['uploader', 'comments.user'])->findOrFail($id);
        $document->document_url = asset('storage/' . $document->file_path);

        return Inertia::render('track-document', [
            'document' => $document,
        ]);
    }
    public function destroy($id): RedirectResponse
    {
        if (auth()->user()->hasPermissionTo('delete-documents')) {
            return redirect()->back()->withErrors('permission', 'You do not have permission to delete documents.');
        }

        $document = Document::findOrFail($id);

        // Remove the associated file from storage
        Storage::disk('public')->delete($document->file_path);

        // Delete the document from the database
        $document->delete();


        return redirect()->back()->with('success', 'Document deleted successfully.');
    }


}