<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\Comment;

class CommentController extends Controller
{
    public function store(Request $request)
    {
        $validated = $request->validate([
            'document_id' => 'required|exists:documents,id',
            'action' => 'required|string|max:255',
            'message' => 'required|string|max:1000',
            'color' => 'required|string|max:10'
        ]);

        Comment::create([
            'document_id' => $validated['document_id'],
            'user_id' => auth()->id(),
            'action' => $validated['action'],
            'message' => $validated['message'],
            'color' => $validated['color'],
        ]);

        return back();
    }
}