import { DataTable } from '@/components/datatable/data-table';
import { Button } from '@/components/ui/button';
import { Dialog, DialogClose, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { formatDateTime } from '@/lib/utils';
import { Department } from "@/types";
import { router, useForm } from '@inertiajs/react';
import { ColumnDef, createColumnHelper } from '@tanstack/react-table';
import { MoreHorizontal, PlusIcon } from 'lucide-react';
import { FormEvent } from 'react';

const columnHelper = createColumnHelper<Department>();

export const columns: ColumnDef<Department, any>[] = [
    columnHelper.accessor('name', {
        header: 'Name',
        cell: info => info.getValue(),
    }),
    columnHelper.accessor('code', {
        header: 'Code',
        cell: info => info.getValue(),
    }),
    columnHelper.accessor('created_at', {
        header: 'Edited At',
        cell: ({ row }) => formatDateTime(row.original.created_at),
    }),
    columnHelper.display({
        id: 'actions',
        cell: ({ row }) => {
            return (
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="data-[state=open]:bg-muted flex h-8 w-8 p-0">
                            <MoreHorizontal />
                            <span className="sr-only">Open menu</span>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-[160px]">
                        <DropdownMenuItem
                            variant="destructive"
                            onClick={() => {
                                router.delete(route('departments.destroy', row.original.id));
                            }}
                        >
                            Delete
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            );
        }
    })
];

export default function AdminOverview({ departments, usage }: { departments: Department[], usage: any }) {
    return (
        <div className="flex h-full flex-1 flex-col gap-4 rounded-xl p-4">
            <div>
                <dl className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-4">
                    {/* @ts-expect-error */}
                    {usage.map((item) => (
                        <div key={item.name} className="overflow-hidden rounded-lg bg-white px-4 py-5 border border-border shadow-xs sm:p-6">
                            <dt className="truncate text-sm font-medium text-gray-500">{item.name}</dt>
                            <dd className="mt-1 text-3xl font-semibold tracking-tight text-gray-900">{item.stat}</dd>
                        </div>
                    ))}
                </dl>
            </div>
            <div className="mt-6">
                <div className="flex items-center mb-4 justify-between">
                    <h2 className='font-semibold text-xl'>Departments</h2>
                    <NewDepartmentFrm />
                </div>
                <DataTable data={departments} columns={columns} />
            </div>
        </div>
    )
}

function NewDepartmentFrm() {
    const { data, setData, post, processing } = useForm({
        name: '',
        description: '',
        code: '',
    });

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        post(route('departments.store'));
    };

    return (
        <Dialog>
            <DialogTrigger asChild>
                <Button variant='outline' >
                    <PlusIcon />
                    Add Department
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Create Department</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit}>
                    <div className='space-y-4'>
                        <div>
                            <Label htmlFor="name" className="tmb-2 ext-right">
                                Code
                            </Label>
                            <Input
                                id="name"
                                name="name"
                                className="mt-2"
                                value={data.code}
                                onChange={(e) => setData('code', e.target.value)}
                                required
                            />
                        </div>

                        <div>
                            <Label htmlFor="email" className="text-right">
                                Name
                            </Label>
                            <Input id="name" name="name" className="mt-2" onChange={(e) => setData('name', e.target.value)} required />
                        </div>
                        <div>
                            <Label htmlFor="email" className="text-right">
                                Description
                            </Label>
                            <Textarea className="mt-2" rows={5} value={data.description} onChange={(e) => setData('description', e.target.value)} />
                        </div>
                    </div>
                    <DialogFooter>
                        <DialogClose>
                            <Button className='mt-3.5' disabled={processing} type="submit">
                                {processing ? 'Creating...' : 'Submit'}
                            </Button>
                        </DialogClose>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

