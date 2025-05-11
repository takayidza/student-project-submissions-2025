<?php

namespace App\Http\Controllers;

use App\Models\Department;
use App\Models\Document;
use App\Models\User;
use Inertia\Inertia;
use Inertia\Response;
use Spatie\Permission\Models\Role;

class DashboardController extends Controller
{
    public function index(): Response
    {
        $user = auth()->user();
        if ($user->hasRole('user')) {
            $documents = Document::with('uploader')
                ->where('uploaded_by', $user->id)
                ->get();

            return Inertia::render('dashboard', [
                'usage' => [],
                'documents' => $documents,
                "departments" => [],
            ]);
            ;
        }
        $usage = [
            [
                'name' => 'Total Submission',
                'stat' => Document::count(),
            ],
            [
                'name' => 'Storage',
                'stat' => '3MB',
            ],
            [
                'name' => 'Users',
                'stat' => User::count(),
            ],
            [
                'name' => 'Departments',
                'stat' => Department::count(),
            ],
        ];

        $departments = Department::all();
        return Inertia::render('dashboard', [
            'usage' => $usage,
            'documents' => [],
            "departments" => $departments
        ]);
    }

    public function getUsers(): Response
    {
        $users = User::with(['roles', 'permissions', 'department'])->get();
        $roles = Role::pluck('name')->toArray();
        return Inertia::render('users', ['users' => $users, 'roles' => $roles, 'departments' => Department::all()]);
    }
}