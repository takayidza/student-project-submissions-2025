<script>
    import { browser } from '$app/environment';
    import { TooltipProvider } from "$lib/components/ui/tooltip";
    import { cn } from "$lib/components/shadcn/utils.js";
    import {
        SIDEBAR_COOKIE_MAX_AGE,
        SIDEBAR_COOKIE_NAME,
        SIDEBAR_WIDTH,
        SIDEBAR_WIDTH_ICON,
    } from "./constants.js";
    import { setSidebar } from "./context.svelte.js";
    
    let {
        ref = $bindable(null),
        open = $bindable(true),
        onOpenChange = () => {},
        class: className,
        style,
        children,
        ...restProps
    } = $props();
    
    const sidebar = setSidebar({
        open: () => open,
        setOpen: (value) => {
            open = value;
            onOpenChange(value);
            if (browser) {
                // Only set cookie on client side
                document.cookie = `${SIDEBAR_COOKIE_NAME}=${open}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`;
            }
        },
    });
</script>

<svelte:window onkeydown={sidebar.handleShortcutKeydown} />

{#if browser}
    <TooltipProvider delayDuration={0}>
        <div
            style="--sidebar-width: {SIDEBAR_WIDTH}; --sidebar-width-icon: {SIDEBAR_WIDTH_ICON}; {style}"
            class={cn(
                "group/sidebar-wrapper has-[[data-variant=inset]]:bg-sidebar flex min-h-svh w-full",
                className
            )}
            bind:this={ref}
            {...restProps}
        >
            {@render children?.()}
        </div>
    </TooltipProvider>
{:else}
    <div
        style="--sidebar-width: {SIDEBAR_WIDTH}; --sidebar-width-icon: {SIDEBAR_WIDTH_ICON}; {style}"
        class={cn(
            "group/sidebar-wrapper has-[[data-variant=inset]]:bg-sidebar flex min-h-svh w-full",
            className
        )}
        bind:this={ref}
        {...restProps}
    >
        {@render children?.()}
    </div>
{/if}