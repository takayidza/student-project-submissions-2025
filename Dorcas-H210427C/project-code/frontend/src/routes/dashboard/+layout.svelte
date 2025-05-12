<!-- src/routes/dashboard/+layout.svelte -->
<script>
    import AppSidebar from "$lib/components/AppSidebar.svelte";
    
    let { children } = $props();
</script>

<div class="flex w-full h-screen overflow-hidden bg-gray-50">
    <!-- Include sidebar navigation -->
    <AppSidebar />
    
    <!-- Main content area -->
    <main class="flex-1 overflow-auto">
        <div class="h-full">
            {@render children?.()}
        </div>
    </main>
</div>