<script>
    export let size = "medium"; // small, medium, large
    export let color = "white"; // white, blue-500, etc.

    const sizeClasses = {
        small: "w-4 h-4 border-2",
        medium: "w-6 h-6 border-2",
        large: "w-8 h-8 border-3"
    };

    $: spinnerClass = `${sizeClasses[size]} inline-block rounded-full border-t-transparent border-${color} animate-spin`;
</script>

<div class={spinnerClass} role="status" aria-label="loading">
    <span class="sr-only">Loading...</span>
</div>

<style>
    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    .animate-spin {
        animation: spin 1s linear infinite;
    }
</style>