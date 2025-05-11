import AppLayout from '@/layouts/app-layout';
import AdminOverview from '@/partial/admin-overview';
import UserOverview from '@/partial/user-overview';
import { Department, SharedData, type BreadcrumbItem } from '@/types';
import { Head, usePage } from '@inertiajs/react';

const breadcrumbs: BreadcrumbItem[] = [
    {
        title: 'Dashboard',
        href: '/dashboard',
    },
];

export default function Dashboard() {
    const {
        auth: { user },
    } = usePage<SharedData>().props;
    const { departments, documents, usage } = usePage<{ departments: Department[], documents: Document[] }>().props;
    return (
        <AppLayout breadcrumbs={breadcrumbs}>
            <Head title="Dashboard" />
            {user.role === 'user' ? <UserOverview documents={documents} /> : <AdminOverview usage={usage} departments={departments} />}
        </AppLayout>
    );
}
