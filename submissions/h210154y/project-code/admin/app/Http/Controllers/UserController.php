<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Support\Facades\Hash;
use Spatie\Permission\Models\Role;
use Illuminate\Http\Request;

class UserController extends Controller
{
    public function store(Request $request)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:users',
            'password' => 'required|min:6',
            'role' => 'required|exists:roles,name',
            'department_id' => 'nullable|string|max:255',
        ]);

        $departmentId = (int) $validated['department_id'];

        $user = User::create([
            'name' => $validated['name'],
            'email' => $validated['email'],
            'password' => Hash::make($validated['password']),
            'department_id' => $departmentId,
        ]);

        $user->assignRole($validated['role']);

        return back()->with('success', 'User created successfully.');
    }

    public function destroy(User $user)
    {

        if (!auth()->user()->can('delete-users')) {
            return redirect()->back()->withErrors(['permission' => 'You do not have permission to create departments.']);
        }
        if (auth()->id() === $user->id) {
            return back()->withErrors(['permission' => 'You cannot delete yourself.']);
        }

        $user->delete();

        return redirect()->back()->with('success', 'User deleted successfully.');
    }

    public function assignRoles(Request $request)
    {
        $validated = $request->validate([
            'name' => 'required|string|unique:roles,name',
            'permissions' => 'array',
            'permissions.*' => 'string|exists:permissions,name',
        ]);

        $role = Role::create(['name' => $validated['name']]);
        $role->syncPermissions($validated['permissions']);

        return redirect()->back()->with('success', 'New role set successfully.');
    }
}