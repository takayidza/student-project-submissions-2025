import { DataTable } from "@/components/datatable/data-table";
import { type ColumnDef, createColumnHelper } from "@tanstack/react-table";
import { formatDateTime, statuses } from "@/lib/utils";
import { Link, useForm } from '@inertiajs/react';
import { Button } from "@/components/ui/button";
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogClose, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

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
            console.log(original);
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
    })

];

export default function UserOverview({ documents }: { documents: Document[] }) {
    return (
        <div className="flex h-full flex-1 flex-col gap-4 rounded-xl p-4">
            <div className="flex items-center mt-3 justify-between">
                <h2 className='font-semibold text-xl'>Your Submissions</h2>
                <AddDocForm />
            </div>
            <div className="my-6">
                <DataTable data={documents} columns={columns} />
            </div>
        </div>
    )
}


function AddDocForm() {
    const { data, setData, post, processing } = useForm({
        title: '',
        description: '',
        file: null as File | null,
    });

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        post('/documents/upload', {
            forceFormData: true, // Important for file uploads
        })
    };

    return (
        <Dialog>
            <DialogTrigger asChild>
                <Button>New Submission</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Request Submission</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit}>
                    <div className="grid gap-4 py-4">
                        <div>
                            <Label htmlFor="name" className="mb-3 text-right">
                                Title
                            </Label>
                            <Input
                                id="name"
                                name="name"
                                className="mt-1.5"
                                value={data.title}
                                onChange={(e) => setData('title', e.target.value)}
                                required
                            />
                        </div>
                        <div>
                            <Label htmlFor="email" className="text-right">
                                File
                            </Label>
                            <Input
                                className="mt-1.5"
                                id="email"
                                name="email"
                                type="file"
                                onChange={(e) => setData('file', e.target.files?.[0] ?? null)}
                                accept="application/pdf"
                                required
                            />
                        </div>
                        <div>
                            <Label htmlFor="email">Message</Label>
                            <Textarea className="mt-2" rows={5} value={data.description} onChange={(e) => setData('description', e.target.value)} />
                        </div>
                    </div>
                    <DialogFooter>
                        <DialogClose>
                            <Button size="sm" disabled={processing} type="submit">
                                {processing ? 'Uploading...' : 'Upload'}
                            </Button>
                        </DialogClose>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}