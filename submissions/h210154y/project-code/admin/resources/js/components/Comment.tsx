import { useForm } from "@inertiajs/react";
import { Paperclip } from "lucide-react";
import { FormEvent } from "react";

export default function Comment({ document_id }: { document_id: number }) {

    const { data, setData, post } = useForm({
        action: 'admin review',
        message: '',
        document_id: document_id,
        color: 'green'
    });


    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        post('/comments', {
            forceFormData: true,
        });
    };

    return (
        <div className="mt-6 flex gap-x-3">
            <img
                src="/avatar.png"
                alt="Profile"
                className="size-7 flex-none rounded-full bg-gray-50"
            />
            <form onSubmit={handleSubmit} className="relative flex-auto">
                <div className="overflow-hidden rounded-md pb-12 shadow-xs border border-border">
                    <label htmlFor="comment" className="sr-only">
                        Add your comment
                    </label>
                    <textarea
                        rows={2}
                        name="comment"
                        id="comment"
                        className="block w-full px-3 resize-none border-0 bg-transparent py-1.5 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-0 sm:text-sm sm:leading-6"
                        placeholder="Write a review or comment..."
                        value={data.message}
                        onChange={(e) => setData('message', e.target.value)}
                        required
                    />
                </div>
                <div className="absolute inset-x-0 bottom-0 flex items-center justify-between py-2 px-3">
                    <button
                        type="button"
                        className="flex h-9 w-9 items-center justify-center rounded-full text-gray-400 hover:text-gray-500 focus:outline-none"
                    >
                        <Paperclip className="h-5 w-5" aria-hidden="true" />
                        <span className="sr-only">Attach a file</span>
                    </button>
                    <button
                        type="submit"
                        className="rounded-md bg-white px-3 py-1.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:outline-none"
                    >
                        Comment
                    </button>
                </div>
            </form>
        </div>
    );
}
