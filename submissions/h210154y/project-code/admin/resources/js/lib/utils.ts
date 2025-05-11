import { type ClassValue, clsx } from 'clsx';
import { Archive, Boxes, CheckCircle, CircleOff, FolderKanban, SendHorizonal } from 'lucide-react';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}


export function formatDateTime(dateString: string): string {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
        return '';
    }
    const day = date.getDate();
    const month = date.toLocaleString('en-US', { month: 'short' }); // 'May'
    const hours = date.getHours().toString().padStart(2, '0'); // '10'
    const minutes = date.getMinutes().toString().padStart(2, '0'); // '48'

    return `${day} ${month} ${hours}:${minutes}`;
}


export function formatShortDate(dateStr: string): string {
    const date = new Date(dateStr);

    const day = date.getDate();
    const month = date.toLocaleString('en-US', { month: 'short' });
    const year = date.getFullYear();

    return `${day} ${month}, ${year}`;
}

export function capitalize(word: string) {
    if (!word) return '';
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
}

export const statuses = [
    {
        value: 'categorised',
        label: 'Under Review',
        icon: Boxes,
    },
    {
        value: 'in-review',
        label: 'Forwarded',
        icon: FolderKanban,
    },
    {
        value: 'submitted',
        label: 'Submitted',
        icon: SendHorizonal,
    },
    {
        value: 'done',
        label: 'Completed',
        icon: CheckCircle,
    },
    {
        value: 'cancelled',
        label: 'Canceled',
        icon: CircleOff,
    },
    {
        value: 'archived',
        label: 'Archived',
        icon: Archive,
    },
];

export function timeAgo(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diff = (now.getTime() - date.getTime()) / 1000; // in seconds

    const units: [Intl.RelativeTimeFormatUnit, number][] = [
        ['year', 60 * 60 * 24 * 365],
        ['month', 60 * 60 * 24 * 30],
        ['week', 60 * 60 * 24 * 7],
        ['day', 60 * 60 * 24],
        ['hour', 60 * 60],
        ['minute', 60],
        ['second', 1],
    ];

    for (const [unit, secondsInUnit] of units) {
        const value = Math.floor(diff / secondsInUnit);
        if (value >= 1) {
            return new Intl.RelativeTimeFormat('en', { numeric: 'auto' }).format(-value, unit);
        }
    }

    return 'just now';
}