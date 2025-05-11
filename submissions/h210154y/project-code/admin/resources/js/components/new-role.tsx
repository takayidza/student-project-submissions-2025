import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useForm } from '@inertiajs/react';
import { useState } from 'react';

const permissionsList = {
    Documents: [
        { name: 'view-documents', label: 'View Documents' },
        { name: 'create-documents', label: 'Create Documents' },
        { name: 'edit-documents', label: 'Edit Documents' },
        { name: 'delete-documents', label: 'Delete Documents' },
    ],
    Users: [
        { name: 'view-users', label: 'View Users' },
        { name: 'create-users', label: 'Create Users' },
        { name: 'edit-users', label: 'Edit Users' },
        { name: 'delete-users', label: 'Delete Users' },
        { name: 'assign-roles', label: 'Assign Roles' },
    ],
    Roles: [
        { name: 'create-role', label: 'Create Role' },
        { name: 'view-role', label: 'View Role' },
        { name: 'edit-role', label: 'Edit Role' },
        {
            name: 'delete-role', label: 'Delete Role'
        }
    ]
};

export default function NewRoleFrm() {
    const [open, setOpen] = useState(false);

    const { data, setData, post, processing, reset, errors } = useForm({
        name: '',
        permissions: [] as string[],
    });

    const togglePermission = (permission: string) => {
        if (data.permissions.includes(permission)) {
            setData('permissions', data.permissions.filter(p => p !== permission));
        } else {
            setData('permissions', [...data.permissions, permission]);
        }
    };

    const submit = (e: React.FormEvent) => {
        e.preventDefault();
        post(route('roles.store'), {
            onSuccess: () => {
                reset();
                setOpen(false);
            },
        });
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant='secondary'>New Role</Button>
            </DialogTrigger>

            <DialogContent className="max-w-2xl">
                <DialogHeader>
                    <DialogTitle>Add Role</DialogTitle>
                </DialogHeader>

                <form onSubmit={submit} className="space-y-6">
                    <div>
                        <Label htmlFor="name">Role Name</Label>
                        <Input
                            id="name"
                            value={data.name}
                            onChange={(e) => setData('name', e.target.value)}
                            className="mt-2"
                        />
                        {errors.name && <p className="text-sm text-red-600">{errors.name}</p>}
                    </div>

                    <div className="space-y-4">
                        {Object.entries(permissionsList).map(([group, permissions]) => (
                            <div key={group}>
                                <h3 className="font-semibold text-lg">{group}</h3>
                                <div className="grid grid-cols-2 gap-2 mt-2">
                                    {permissions.map((permission) => (
                                        <div key={permission.name} className="flex items-center space-x-2">
                                            <Checkbox
                                                id={permission.name}
                                                checked={data.permissions.includes(permission.name)}
                                                onCheckedChange={() => togglePermission(permission.name)}
                                            />
                                            <Label className='text-muted-foreground' htmlFor={permission.name}>{permission.label}</Label>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>

                    <DialogFooter>
                        <Button variant='outline' onClick={() => {
                            reset()
                            setOpen(false)
                        }}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={processing}>
                            Save
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
