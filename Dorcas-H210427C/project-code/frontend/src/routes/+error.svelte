<script>
    import { page } from "$app/state";
    import {
        Card,
        CardContent,
        CardDescription,
        CardFooter,
        CardHeader,
        CardTitle,
    } from "$lib/components/ui/card";
    import { Button } from "$lib/components/ui/button";
    import { AlertTriangle, ArrowLeft } from "lucide-svelte";
    import { cn } from "$lib/components/shadcn/utils";

    console.log('Error object:', page.error.message);
</script>

<div class="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col items-center justify-center p-4 space-y-6">
    <Card
        class="w-full max-w-lg bg-slate-900/60 border border-slate-800/60 backdrop-blur-xl rounded-2xl shadow-xl shadow-slate-950/50 transition-all hover:shadow-2xl hover:shadow-slate-950/60"
        variant="ghost"
    >
        <CardHeader class="space-y-4 p-8">
            <div class="flex items-center gap-4">
                <div class="p-3 bg-red-500/10 rounded-full backdrop-blur-sm">
                    <AlertTriangle class="w-14 h-14 text-red-400/90 animate-pulse" />
                </div>
                <div>
                    <CardTitle
                        class="text-7xl font-black text-transparent bg-clip-text bg-gradient-to-r from-red-300 to-pink-400 drop-shadow-[0_2px_4px_rgba(255,100,100,0.3)]"
                    >
                        {page.status}
                    </CardTitle>
                    <CardDescription class="mt-2 text-slate-400/90 text-lg">
                       {page.error.message}
                    </CardDescription>
                </div>
            </div>
        </CardHeader>

        <CardContent class="px-8 pb-6">
            <div class="space-y-4">
                <div class="p-4 bg-slate-900/40 rounded-xl border border-slate-800/50">
                    <p class="text-slate-200/90 font-medium leading-relaxed tracking-wide">
                        "{page.error.message}"
                    </p>
                </div>
                {#if import.meta.env.MODE === "development" && page.error.stack}
                    <pre
                        class="p-4 mt-4 text-sm text-slate-400/80 bg-slate-900/40 rounded-xl border border-slate-800/50 overflow-x-auto font-mono"
                    >
                        {page.error.stack}
                    </pre>
                {/if}
            </div>
        </CardContent>

        <CardFooter class="px-8 pb-8">
            <div class="w-full flex justify-between items-center">
                <a
                    href="/"
                    class="text-slate-400/80 hover:text-slate-300 transition-colors font-medium flex items-center gap-2"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                        <polyline points="9 22 9 12 15 12 15 22"/>
                    </svg>
                    Return Home
                </a>
                <Button
                    onclick={() => window.history.back()}
                    class="gap-2 bg-gradient-to-r from-red-400/90 to-pink-500/90 hover:from-red-300 hover:to-pink-400 transition-all shadow-lg shadow-red-500/10 hover:shadow-red-500/20"
                >
                    <ArrowLeft class="w-5 h-5 transform -translate-x-0.5 group-hover:-translate-x-1 transition-transform" />
                    Go Back
                </Button>
            </div>
        </CardFooter>
    </Card>

    <p class="text-sm text-center text-slate-500/80 max-w-md leading-relaxed">
        Still stuck? Reach out to our support team at
        <a
            href="mailto:support@example.com"
            class="text-slate-400/90 hover:text-pink-400/90 transition-colors font-medium underline decoration-2 underline-offset-4 decoration-slate-600 hover:decoration-pink-400/50"
        >
            support@example.com
        </a>
    </p>
</div>
