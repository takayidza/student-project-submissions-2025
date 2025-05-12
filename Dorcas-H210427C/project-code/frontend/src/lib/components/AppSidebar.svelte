<!-- src/lib/components/AppSidebar.svelte -->
<script>
    import { Home, ShieldAlert, User, Settings, LogOut, ChevronLeft, ChevronRight, Camera, Users } from "lucide-svelte";
    import { enhance } from '$app/forms';
    import { browser } from '$app/environment';
    import { page } from '$app/stores'; // Changed from $app/state to $app/stores
    import { onMount } from "svelte";

    // State management with Svelte 5 runes
    let isOpen = $state(true);
    let currentPath = $state('');
    let username = $state('');
    let userInitials = $state('');
    
    // Menu items configuration
    const menuItems = [
        {
            title: "Dashboard",
            url: "/dashboard",
            icon: Home,
            isAction: false
        },
        {
            title: "Security Logs",
            url: "/dashboard/faces",
            icon: ShieldAlert,
            isAction: false
        },
        {
            title: "Logout",
            url: "/auth/logout",
            icon: LogOut,
            isAction: true
        }
    ];
    
    // Toggle sidebar function
    function toggleSidebar() {
        isOpen = !isOpen;
        
        // Save preference to localStorage
        if (browser) {
            localStorage.setItem('sidebarOpen', isOpen.toString());
        }
    }
    
    // Initialize from localStorage and set current path
    function initSidebar() {
        if (browser) {
            // Set current path
            currentPath = window.location.pathname;
            
            // Load saved state
            const savedState = localStorage.getItem('sidebarOpen');
            if (savedState !== null) {
                isOpen = savedState === 'true';
            }
        }
    }
    
    // Get user info from page data
    function getUserData() {
        if (page.subscribe) {
            const unsubscribe = page.subscribe(pageData => {
                if (pageData && pageData.data && pageData.data.user) {
                    username = pageData.data.user.username || '';
                    
                    // Create initials from username
                    if (username) {
                        userInitials = username
                            .split(' ')
                            .map(part => part.charAt(0).toUpperCase())
                            .join('')
                            .substring(0, 2);
                    }
                }
            });
            return unsubscribe;
        }
        return null;
    }
    
    // Initialize on component mount
    onMount(() => {
        initSidebar();
        const unsubscribe = getUserData();
        
        // Return cleanup function
        return () => {
            if (unsubscribe) unsubscribe();
        };
    });
</script>

<!-- Main sidebar container -->
<aside 
    class="h-screen flex flex-col transition-all duration-300 ease-in-out fixed left-0 top-0 z-40 border-r border-gray-200 bg-gradient-to-b from-indigo-600 to-indigo-800"
    style="width: {isOpen ? '250px' : '70px'}"
>
    <div class="p-4 flex-1 overflow-y-auto flex flex-col">
        <!-- Logo and title -->
        <div class="mb-8 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <div class="p-2 bg-white/10 rounded-lg">
                    <Camera class="h-6 w-6 text-white" />
                </div>
                {#if isOpen}
                    <div>
                        <h2 class="text-xl font-bold tracking-tight text-white">Face Scanner</h2>
                        <p class="text-xs text-indigo-200/70">AI Recognition</p>
                    </div>
                {/if}
            </div>
        </div>
        
        <!-- User profile section -->
        {#if isOpen}
            <div class="mb-8 p-3 bg-white/10 rounded-lg flex items-center gap-3">
                <div class="h-10 w-10 rounded-full bg-indigo-800 flex items-center justify-center">
                    <span class="text-white font-semibold">{userInitials || 'U'}</span>
                </div>
                <div>
                    <p class="text-white font-medium truncate">{username || 'User'}</p>
                    <p class="text-xs text-indigo-200/70">Authenticated User</p>
                </div>
            </div>
        {:else}
            <div class="mb-8 p-2 bg-white/10 rounded-lg flex items-center justify-center">
                <div class="h-8 w-8 rounded-full bg-indigo-800 flex items-center justify-center">
                    <span class="text-white font-semibold text-xs">{userInitials || 'U'}</span>
                </div>
            </div>
        {/if}
        
        <!-- Navigation menu -->
        <nav class="flex-1">
            <ul class="space-y-1.5">
                {#each menuItems as item}
                    <li>
                        {#if item.isAction}
                            <!-- Form action items (like logout) -->
                            <form 
                                action={item.url} 
                                method="POST" 
                                use:enhance
                                class="w-full"
                            >
                                <button
                                    type="submit"
                                    class="flex items-center rounded-lg px-3 py-2.5 text-sm w-full transition-all duration-200
                                           hover:bg-white/10 
                                           {currentPath === item.url ? 'bg-white/20 text-white' : 'text-indigo-100'}"
                                >
                                    <item.icon class="h-5 w-5 flex-shrink-0" />
                                    {#if isOpen}
                                        <span class="ml-3">{item.title}</span>
                                    {/if}
                                </button>
                            </form>
                        {:else}
                            <!-- Standard navigation links -->
                            <a
                                href={item.url}
                                class="flex items-center rounded-lg px-3 py-2.5 text-sm transition-all duration-200
                                       hover:bg-white/10 
                                       {currentPath.startsWith(item.url) ? 'bg-white/20 text-white' : 'text-indigo-100'}"
                            >
                                <item.icon class="h-5 w-5 flex-shrink-0" />
                                {#if isOpen}
                                    <span class="ml-3">{item.title}</span>
                                {/if}
                            </a>
                        {/if}
                    </li>
                {/each}
            </ul>
        </nav>
    </div>
    
    <!-- Sidebar toggle button -->
    <div class="p-4 border-t border-indigo-500/30">
        <button 
            class="flex items-center justify-center w-8 h-8 rounded-full bg-indigo-800/50 text-white hover:bg-indigo-500 transition-colors"
            onclick={toggleSidebar}
            aria-label={isOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
            {#if isOpen}
                <ChevronLeft class="h-4 w-4" />
            {:else}
                <ChevronRight class="h-4 w-4" />
            {/if}
        </button>
    </div>
</aside>

<!-- Spacer to push content to the right of sidebar -->
<div 
    style="width: {isOpen ? '250px' : '70px'}" 
    class="transition-all duration-300 flex-shrink-0"
></div>