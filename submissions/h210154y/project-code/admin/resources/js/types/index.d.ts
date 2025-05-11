import { LucideIcon } from 'lucide-react';
import type { Config } from 'ziggy-js';

export interface Auth {
    user: User;
}

export interface BreadcrumbItem {
    title: string;
    href: string;
}

export interface NavGroup {
    title: string;
    items: NavItem[];
}

export interface NavItem {
    title: string;
    href: string;
    icon?: LucideIcon | null;
    isActive?: boolean;
}

interface Notification {
    id: number;
    data: {
        message: string
    };
    read_at?: string;
    created_at: string
}


export interface SharedData {
    name: string;
    quote: { message: string; author: string };
    auth: Auth;
    ziggy: Config & { location: string };
    notifications: number;
    messages: Notification[],
    sidebarOpen: boolean;
    [key: string]: unknown;
}

export interface User {
    id: number;
    name: string;
    email: string;
    avatar?: string;
    email_verified_at: string | null;
    created_at: string;
    updated_at: string;
    [key: string]: unknown;
}

interface Department {
    name: string;
    id: number;
    code: string;
    description?: string;
    created_at: string;
    updated_at: string;
}

interface Role {
    id: number;
    name: string;
    guard_name: string;
}

interface Permission {
    id: number;
    name: string;
    guard_name: string;
}

export interface UserResponse extends User {
    roles: Role[];
    permissions: Permission[];
    department: Department | null;
}

export interface Document {
    id: number;
    title: string;
    description: string | null;
    file_path: string;
    file_name: string;
    file_type: string;
    file_size: number;
    category: string;
    status: string;
    uploaded_by: number;
    department_id: number | null;
    created_at: string;
    updated_at: string;
    document_url?: string; // optional, added in response
    comments?: Comment[]
}


// export interface Comment {
//     id: number;
//     user_id: number;
//     action: string;
//     created_at: string;
//     document_id: number;
//     message: string;
//     updated_at: string;
//     user: User
// }