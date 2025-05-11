<?php

namespace App\Http\Controllers;

use App\Models\Department;
use Illuminate\Http\Request;

class DepartmentController extends Controller
{
    public function store(Request $request)
    {
        if (!auth()->user()->can('create-departments')) {
            return redirect()->back()->withErrors(['permission' => 'You do not have permission to create departments.']);
        }

        $request->validate([
            'name' => 'required|string|max:255',
            'code' => 'required|string|max:10|unique:departments',
            'description' => 'nullable|string',
        ]);

        Department::create([
            'name' => $request->name,
            'code' => $request->code,
            'description' => $request->description,
        ]);

        return back()->with('success', 'Department created successfully.');
    }
    public function destroy($id)
    {
        $department = Department::findOrFail($id);
        $department->delete();

        return back()->with('success', 'Department deleted successfully.');
    }
}