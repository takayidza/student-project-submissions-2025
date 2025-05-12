<script>
    const {
        maxWidth = "xl",
        padding = "px-4 py-6",
        bg = "",
        style = "",
        children,
    } = $props();
</script>

<div
    class={`flex flex-col items-center justify-center w-full min-h-screen ${padding} max-w-${maxWidth} ${bg}`}
    {style}
>
    {@render children()}
</div>

<style>
    :global(body) {
        margin: 0;
        padding: 0;
    }
</style>
