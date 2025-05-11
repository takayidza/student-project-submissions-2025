import AppLayout from '@/layouts/app-layout';
import { UserResponse, type BreadcrumbItem } from '@/types';
import { Head, usePage, router } from "@inertiajs/react";
import { formatDateTime, capitalize } from "@/lib/utils";
import { DataTable } from "@/components/datatable/data-table";
import { type ColumnDef, createColumnHelper } from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import { MoreHorizontal } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import NewRoleFrm from '@/components/new-role';
import NewUserFrm from '@/components/new-user';


const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Users',
        href: '/users',
    },
];

const columnHelper = createColumnHelper<UserResponse>();

const columns: ColumnDef<UserResponse, any>[] = [
    columnHelper.accessor('name', {
        header: 'Name',
        cell: info => info.getValue(),
    }),
    columnHelper.display({
        header: 'Department',
        cell: ({ row }) => row.original.department?.name ?? 'N/A',
    }),
    columnHelper.accessor('email', {
        header: 'Email',
        cell: info => info.getValue(),
    }),
    columnHelper.display({
        header: 'Role',
        cell: ({ row }) => capitalize(row.original.roles[0]?.name) ?? 'No role',
    }),
    columnHelper.display({
        header: 'Added On',
        cell: ({ row }) => formatDateTime(row.original.created_at),
    }),
    columnHelper.display({
        id: 'actions',
        cell: ({ row }) => {
            return (
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="data-[state=open]:bg-muted flex size-4 p-0">
                            <MoreHorizontal />
                            <span className="sr-only">Open menu</span>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-[160px]">
                        <DropdownMenuItem
                            variant="destructive"
                            onClick={() => {
                                router.delete(route('users.destroy', row.original.id));
                            }}
                        >
                            Delete
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            );
        },
    }),
]


export default function Users() {
    const { users, roles, departments } = usePage<{ users: UserResponse[] }>().props;

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Manage Users" />
            <div className="flex h-full flex-1 flex-col gap-4 rounded-xl p-4">
                <div className="flex items-center justify-between">
                    <span></span>
                    <div className="flex items-center justify-between">
                        <span></span>
                        <div className="flex gap-3">
                            <NewRoleFrm />
                            <NewUserFrm roles={roles} departments={departments} />
                        </div>
                    </div>
                </div>

                <div className="my-8">
                    <DataTable data={users} columns={columns} />
                </div>
            </div>
        </AppLayout>
    )
}