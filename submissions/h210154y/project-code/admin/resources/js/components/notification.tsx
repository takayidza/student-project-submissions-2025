
type NotificationProps = {
    sender: string;
    timestamp: string;
    message: string;
    iconColor?: 'blue' | 'orange' | 'green' | 'purple';
    actionText?: string;
    actionUrl?: string;
};

export const Notification = ({
    sender,
    timestamp,
    message,
    iconColor = 'blue',
    actionText,
    actionUrl
}: NotificationProps) => {
    const initial = sender.charAt(0);

    // Map color names to Tailwind classes
    const colorMap = {
        blue: 'bg-blue-100 text-blue-500',
        orange: 'bg-orange-100 text-orange-500',
        green: 'bg-green-100 text-green-500',
        purple: 'bg-purple-100 text-purple-500',
    };

    const iconColorClass = colorMap[iconColor];

    return (
        <div className="mb-4 flex gap-3">
            <div className={`flex h-8 w-8 items-center justify-center rounded-full ${iconColorClass}`}>
                {initial}
            </div>
            <div className="flex-1">
                <div className="flex items-center gap-2">
                    <span className="font-medium">{sender}</span>
                    <span className="text-sm text-gray-500">{timestamp}</span>
                </div>
                <div className="mt-1 rounded-md bg-gray-50 p-3 text-sm">
                    <p>{message}</p>
                    {actionText && actionUrl && (
                        <a href={actionUrl} className="mt-2 block text-blue-500">
                            {actionText}
                        </a>
                    )}
                </div>
            </div>
        </div>
    );
};