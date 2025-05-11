import Comment from '@/components/comment';
import { Notification } from '@/components/notification';
import PDFViewer from '@/components/pdf-viewer';
import AppLayout from '@/layouts/app-layout';
import { SharedData, type BreadcrumbItem } from '@/types';
import { Head, usePage } from '@inertiajs/react';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { timeAgo } from '@/lib/utils';

const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Document Tracking',
        href: '/documents',
    },
];

export default function ViewDocument() {
    const { document } = usePage<{ document: Document }>().props;
    //@ts-expect-error
    const { comments } = document;
    const {
        auth: { user },
    } = usePage<SharedData>().props;

    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Track Document" />
            <div className="flex h-full flex-1 flex-col gap-4 rounded-xl p-4">
                <div>
                    <h1 className="mb-4 text-xl text-foreground font-bold">{document.title}</h1>
                </div>
                <div className="border-sidebar-border/70 dark:border-sidebar-border relative flex-1 overflow-hidden rounded-md border md:min-h-min">
                    <div className="grid grid-cols-2">
                        <div className="border-accent border-r">
                            {/* @ts-ignore */}
                            <PDFViewer file={document.document_url} />
                        </div>
                        <div className="p-6">
                            <div className='border-b mb-1.5'>
                                <h3 className='font-semibold text-foreground mb-2'>Comments & History</h3>
                            </div>
                            <div className="mt-4">
                                {comments.length > 0 && comments.map((comment: Comment) => {
                                    return <Notification
                                        // @ts-expect-error
                                        sender={comment.user.name}
                                        //@ts-expect-error
                                        timestamp={timeAgo(comment.updated_at)}
                                        //@ts-expect-error
                                        message={comment.message}
                                        //@ts-expect-error
                                        iconColor={comment.color}
                                        actionUrl="#"
                                    />
                                })}
                            </div>
                            {/* @ts-expect-error */}
                            {user.role === 'admin' && <Comment document_id={document.id} />}
                        </div>
                    </div>
                </div>
            </div>
        </AppLayout>
    );
}
