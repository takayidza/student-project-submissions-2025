import AppLayout from "@/layouts/app-layout";
import { BreadcrumbItem } from "@/types";
import { DataTable } from "@/components/datatable/data-table";
import { formatDateTime, statuses } from "@/lib/utils";
import { Link } from '@inertiajs/react';
import { MoreHorizontal } from 'lucide-react';
import { type ColumnDef, createColumnHelper } from "@tanstack/react-table";
import { Head, usePage, router } from "@inertiajs/react";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Button } from "@/components/ui/button";
import { toast } from 'sonner'


const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Documents',
        href: '/documents',
    },

];

const columnHelper = createColumnHelper<Document>();

const columns: ColumnDef<Document, any>[] = [
    columnHelper.display({
        header: 'Name',
        cell: ({ row }) => (
            <Link href={`/documents/${row.original.id}`} className="text-blue-500">
                {row.original.title}
            </Link>
        ),
    }),
    columnHelper.accessor('uploader.name', {
        header: 'Uploaded By',
        cell: info => info.getValue(),
    }),
    columnHelper.accessor('category', {
        header: 'Document Type',
        cell: info => info.getValue(),
    }),
    columnHelper.display({
        header: 'Added On',
        cell: ({ row }) => formatDateTime(row.original.created_at),
    }),
    columnHelper.display({
        header: 'Status',
        cell: ({ row: { original } }) => {
            const status = statuses.find((status) => status.value === original.status);
            if (!status) {
                return null;
            }
            return (
                <div className="flex items-center">
                    {status.icon && <status.icon className="text-muted-foreground mr-2 !size-4" />}
                    <span>{status.label}</span>
                </div>
            );
        },
    }),
    columnHelper.display({
        id: 'actions',
        cell: ({ row }) => {
            return (
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="data-[state=open]:bg-muted flex size-5 p-0">
                            <MoreHorizontal />
                            <span className="sr-only">Open menu</span>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-[160px]">
                        <DropdownMenuItem>Re-Execute Pipeline</DropdownMenuItem>
                        <DropdownMenuItem onClick={() => {
                            router.patch(`/documents/${row.original.id}/status`, {
                                status: 'done'
                            });
                        }}>Mark Completed</DropdownMenuItem>
                        <DropdownMenuItem onClick={() => {
                            router.patch(`/documents/${row.original.id}/status`, {
                                status: 'archived'
                            });
                        }}>Archive Submission</DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                            variant="destructive"
                            onClick={() => {
                                router.delete(`/documents/${row.original.id}`, {
                                    onError: (errors) => {
                                        const errorMessages = Object.keys(errors);
                                        const firstError = errorMessages.length > 0 ? errorMessages[0] : 'Something went wrong';
                                        toast.error(firstError);
                                    },
                                });
                            }}
                        >
                            Delete
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            );
        }
    }),

];

export default function Documents() {
    const { documents } = usePage<{ documents: Document[] }>().props;

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Manage Submissions" />
            <div className="flex h-full flex-1 flex-col gap-4 rounded-xl p-4">
                <div className="flex items-center mt-3 justify-between">
                    <h2 className='font-semibold text-xl'>Manage Submissions</h2>
                    <Button disabled variant='outline'>Create Workflow</Button>
                </div>

                <div className="my-6">
                    <DataTable data={documents} columns={columns} />
                </div>
            </div>
        </AppLayout>
    )
}