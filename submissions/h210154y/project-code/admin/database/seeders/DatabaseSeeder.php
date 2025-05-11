<?php

namespace Database\Seeders;

use App\Models\Department;
use App\Models\User;
// use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;
use Illuminate\Support\Facades\Hash;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        // Clear permission cache
        app()[\Spatie\Permission\PermissionRegistrar::class]->forgetCachedPermissions();

        $admin = Role::create(['name' => 'admin']);
        $editor = Role::create(['name' => 'editor']);
        $viewer = Role::create(['name' => 'viewer']);
        $user = Role::create(['name' => 'user']);

        // Define permissions
        $permissions = [
            'create-documents',
            'edit-documents',
            'delete-documents',
            'view-documents',
            'upload-documents',
            'create-users',
            'edit-users',
            'delete-users',
            'view-users',
            'edit-departments',
            'create-departments',
            'delete-departments',
            'view-departments',
            'assign-roles',
            'create-roles',
            'edit-roles',
            'delete-roles',
            'view-roles',
        ];

        // Create permissions if they don't exist
        foreach ($permissions as $permission) {
            Permission::firstOrCreate(['name' => $permission]);
        }

        // Admin gets all permissions
        $admin->givePermissionTo($permissions);

        // Editor permissions
        $editor->givePermissionTo([
            'create-documents',
            'edit-documents',
            'view-documents',
            'view-users',
            'view-departments',
            'edit-departments',
            'create-departments',
            'view-roles',
        ]);

        // Viewer permissions
        $viewer->givePermissionTo([
            'view-documents',
            'view-users',
            'view-departments',
            'view-roles',
        ]);

        // Basic user permissions
        $user->givePermissionTo([
            'view-documents',
            'upload-documents',
        ]);


        Department::create([
            'name' => 'Quality Assurance Junior School',
            'code' => 'QAJS',
        ]);

        Department::create([
            'name' => 'Quality Assurance Secondary and Non Formal Education',
            'code' => 'QASNFE',
        ]);

        Department::create([
            'name' => 'Quality Assurance Infant School',
            'code' => 'QAIS',
        ]);

        $curriculum = Department::create([
            'name' => 'Curriculum Development and Technical Services',
            'code' => 'CDTS',
        ]);

        $superAdmin = User::create([
            'name' => 'Mutsawashe Dupwa',
            'email' => 'h210154y@hit.ac.zw',
            'password' => Hash::make('Mutsawashe'),
            'department_id' => $curriculum->id
        ]);

        $superAdmin->assignRole('admin');
    }
}