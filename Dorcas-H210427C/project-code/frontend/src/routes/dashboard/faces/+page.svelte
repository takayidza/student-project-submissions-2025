<!-- src/routes/dashboard/faces/+page.svelte -->
<script>
    import { onMount } from "svelte";
    import { page } from "$app/stores"; // Changed from $app/state to $app/stores
    import { Card } from "$lib/components/ui/card";
    import {
        Loader2,
        UserPlus,
        Clock,
        Calendar,
        AlertTriangle,
        ChevronLeft,
        ChevronRight,
        X,
        Shield,
        User,
        Download,
        RefreshCw
    } from "lucide-svelte";

    // State management with Svelte 5 runes
    let unknownFaces = $state([]);
    let loading = $state(true);
    let error = $state(null);
    let selectedFace = $state(null);
    let showDialog = $state(false);
    let currentPage = $state(1);
    let refreshing = $state(false);
    let lastUpdated = $state(new Date());
    let userId = $state(null);
    
    // Configuration
    const apiUrl = import.meta.env.VITE_PUBLIC_API_URL;
    const itemsPerPage = 9;
    
    // Get user ID from page store
    function getUserId() {
        if (page.subscribe) {
            const unsubscribe = page.subscribe(pageData => {
                if (pageData?.data?.userId) {
                    userId = pageData.data.userId;
                    // Fetch data once we have the user ID
                    if (!refreshing && !unknownFaces.length) {
                        fetchUnknownFaces();
                    }
                }
            });
            return unsubscribe;
        }
        return null;
    }

    // Format date functions
    function formatDate(dateString) {
        if (!dateString) return "Unknown";
        return new Date(dateString).toLocaleDateString();
    }

    function formatTime(dateString) {
        if (!dateString) return "Unknown";
        return new Date(dateString).toLocaleTimeString();
    }

    function formatDateTime(dateString) {
        if (!dateString) return "Unknown";
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    function isToday(dateString) {
        if (!dateString) return false;
        const today = new Date();
        const date = new Date(dateString);
        return (
            date.getDate() === today.getDate() &&
            date.getMonth() === today.getMonth() &&
            date.getFullYear() === today.getFullYear()
        );
    }

    function isYesterday(dateString) {
        if (!dateString) return false;
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const date = new Date(dateString);
        return (
            date.getDate() === yesterday.getDate() &&
            date.getMonth() === yesterday.getMonth() &&
            date.getFullYear() === yesterday.getFullYear()
        );
    }

    function getDayLabel(dateString) {
        if (!dateString) return "Unknown";
        if (isToday(dateString)) return "Today";
        if (isYesterday(dateString)) return "Yesterday";
        return formatDate(dateString);
    }

    // Fetch unknown faces data
    async function fetchUnknownFaces() {
        try {
            loading = true;
            
            if (!userId) {
                error = "User ID not found. Please log in again.";
                return;
            }
            
            const response = await fetch(`${apiUrl}/users/unknown_faces/${userId}`);
            
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
            
            const result = await response.json();
            unknownFaces = result.results || [];
            lastUpdated = new Date();
        } catch (err) {
            console.error("Error fetching unknown faces:", err);
            error = "Failed to load security logs. Please try again later.";
        } finally {
            loading = false;
            refreshing = false;
        }
    }

    // Pagination functions
    function getPaginatedFaces() {
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        return unknownFaces.slice(startIndex, endIndex);
    }

    function getTotalPages() {
        return Math.ceil(unknownFaces.length / itemsPerPage);
    }

    function nextPage() {
        if (currentPage < getTotalPages()) {
            currentPage++;
        }
    }

    function prevPage() {
        if (currentPage > 1) {
            currentPage--;
        }
    }

    function goToPage(pageNum) {
        if (pageNum >= 1 && pageNum <= getTotalPages()) {
            currentPage = pageNum;
        }
    }

    // Dialog functions
    function openDialog(face) {
        selectedFace = face;
        showDialog = true;
    }

    function closeDialog() {
        showDialog = false;
        selectedFace = null;
    }
    
    // Refresh data
    async function refreshData() {
        if (refreshing) return;
        
        refreshing = true;
        await fetchUnknownFaces();
    }

    // Initialize component
    onMount(() => {
        const unsubscribe = getUserId();
        
        // Return cleanup function
        return () => {
            if (unsubscribe) unsubscribe();
        };
    });
</script>

<svelte:head>
    <title>Security Logs | Face Recognition System</title>
</svelte:head>

<div class="min-h-screen p-6 bg-gray-50">
    <!-- Page header -->
    <div class="flex flex-col md:flex-row items-start md:items-center justify-between mb-6 gap-4">
        <div>
            <h1 class="text-2xl font-bold text-gray-800">Security Logs</h1>
            <p class="text-gray-500">Manage and monitor unauthorized face detections</p>
        </div>
        
        <div class="flex items-center gap-2">
            <div class="flex items-center gap-2 bg-indigo-50 px-4 py-2 rounded-lg border border-indigo-100">
                <Clock class="h-5 w-5 text-indigo-500" />
                <span class="text-sm text-indigo-700 font-medium">
                    Updated: {lastUpdated.toLocaleTimeString()}
                </span>
            </div>
            
            <button
                class="p-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                onclick={refreshData}
                disabled={refreshing || loading}
                title="Refresh data"
            >
                <RefreshCw class="h-5 w-5 text-gray-700 {refreshing ? 'animate-spin' : ''}" />
            </button>
            
            <button
                class="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors inline-flex items-center gap-2"
                disabled={unknownFaces.length === 0}
                title="Export data"
            >
                <Download class="h-4 w-4 text-gray-700" />
                <span class="text-sm font-medium text-gray-700">Export</span>
            </button>
        </div>
    </div>

    <!-- Error message -->
    {#if error}
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded">
            <div class="flex items-center">
                <AlertTriangle class="h-5 w-5 text-red-500 mr-2" />
                <p class="text-red-700">{error}</p>
            </div>
        </div>
    {/if}

    <!-- Main content -->
    {#if loading && !refreshing}
        <!-- Loading state -->
        <div class="flex flex-col items-center justify-center py-16 bg-white rounded-lg shadow">
            <div class="relative">
                <div class="w-16 h-16 border-4 border-indigo-200 border-t-indigo-500 rounded-full animate-spin"></div>
                <div class="absolute inset-0 flex items-center justify-center">
                    <User class="h-6 w-6 text-indigo-500" />
                </div>
            </div>
            <p class="text-gray-600 mt-4 font-medium">Loading security logs...</p>
            <p class="text-gray-400 text-sm">This may take a moment</p>
        </div>
    {:else if unknownFaces.length === 0}
        <!-- Empty state -->
        <div class="text-center py-16 bg-white rounded-lg shadow border border-gray-100">
            <div class="mx-auto w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mb-4">
                <Shield class="w-8 h-8 text-indigo-600" />
            </div>
            <h3 class="text-lg font-medium text-gray-800 mb-2">
                No Unauthorized Faces Detected
            </h3>
            <p class="text-gray-500 max-w-md mx-auto mb-6">
                Your secure area is clear. When the system detects unauthorized faces, they will appear here for review.
            </p>
        </div>
    {:else}
        <!-- Face detection grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each getPaginatedFaces() as face, index}
                <Card class="group bg-white rounded-xl overflow-hidden border border-gray-100 shadow-sm hover:shadow-md transition-all duration-200 hover:border-indigo-200">
                    <!-- Face image -->
                    <div class="h-48 overflow-hidden bg-gray-100 cursor-pointer relative" onclick={() => openDialog(face)}>
                        {#if face.image_path}
                            <img
                                src={`${apiUrl}/${face.image_path}`}
                                alt="Detected face"
                                class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                                onerror={(e) => (e.target.src = "/placeholder-face.png")}
                            />
                            
                            <!-- Date badge -->
                            <div class="absolute top-3 left-3 z-10">
                                <div class="bg-black/60 backdrop-blur-sm flex items-start space-x-1.5 rounded-lg overflow-hidden">
                                    <div class="bg-indigo-600 text-white px-2 py-1.5 flex flex-col items-center justify-center">
                                        <span class="text-xs font-medium">{new Date(face.created_at).toLocaleDateString('en-US', {month: 'short'})}</span>
                                        <span class="text-lg font-bold leading-none">{new Date(face.created_at).getDate()}</span>
                                    </div>
                                    <div class="px-2 py-1 text-white flex flex-col justify-center">
                                        <span class="text-xs font-medium">{getDayLabel(face.created_at)}</span>
                                        <span class="text-xs">{formatTime(face.created_at)}</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Status badge -->
                            <div class="absolute top-2 right-2">
                                <div class="bg-black/60 backdrop-blur-sm text-white text-xs px-2.5 py-1 rounded-full font-medium">
                                    Unauthorized
                                </div>
                            </div>
                        {:else}
                            <div class="h-full flex items-center justify-center">
                                <p class="text-gray-400 text-sm">No image available</p>
                            </div>
                        {/if}
                    </div>

                    <!-- Face details -->
                    <div class="p-4">
                        <div class="flex items-center justify-between mb-3">
                            <div class="flex items-center">
                                <span class="bg-indigo-100 text-indigo-800 text-xs px-2.5 py-0.5 rounded-full font-medium mr-2">
                                    ID #{(currentPage - 1) * itemsPerPage + index + 1}
                                </span>
                            </div>
                            <span class="text-xs text-gray-500">
                                {formatTime(face.created_at)}
                            </span>
                        </div>

                        <!-- Date summary -->
                        <div class="mb-3 bg-gray-50 rounded-md p-2 flex items-center">
                            <Calendar class="w-4 h-4 text-indigo-500 mr-2" />
                            <div class="text-xs text-gray-600">
                                <span class="font-semibold">{formatDate(face.created_at)}</span>
                                <span> at </span>
                                <span class="font-semibold">{formatTime(face.created_at)}</span>
                            </div>
                        </div>

                        <!-- Face attributes -->
                        <div class="space-y-2 mb-4">
                            <div class="flex items-center justify-between py-1.5 border-b border-gray-100">
                                <span class="text-gray-500 text-sm">Age</span>
                                <span class="font-medium text-gray-800">{face.age || "Unknown"}</span>
                            </div>
                            <div class="flex items-center justify-between py-1.5 border-b border-gray-100">
                                <span class="text-gray-500 text-sm">Gender</span>
                                <span class="font-medium text-gray-800">{face.gender || "Unknown"}</span>
                            </div>
                            <div class="flex items-center justify-between py-1.5 border-b border-gray-100">
                                <span class="text-gray-500 text-sm">Race</span>
                                <span class="font-medium text-gray-800">{face.race || "Unknown"}</span>
                            </div>
                        </div>

                        <!-- View details button -->
                        <button
                            onclick={() => openDialog(face)}
                            class="w-full py-2 px-4 rounded-lg bg-gradient-to-r from-indigo-500 to-indigo-600 text-white text-sm font-medium shadow-sm hover:shadow transition-all duration-150 hover:from-indigo-600 hover:to-indigo-700 flex items-center justify-center gap-1.5"
                        >
                            <span>View Details</span>
                        </button>
                    </div>
                </Card>
            {/each}
        </div>

        <!-- Pagination controls -->
        {#if getTotalPages() > 1}
            <div class="mt-8 pt-6 border-t border-gray-100 flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                <div class="text-sm text-gray-500">
                    Showing <span class="font-medium text-gray-700">
                        {(currentPage - 1) * itemsPerPage + 1}
                    </span>
                    to
                    <span class="font-medium text-gray-700">
                        {Math.min(currentPage * itemsPerPage, unknownFaces.length)}
                    </span>
                    of
                    <span class="font-medium text-gray-700">
                        {unknownFaces.length}
                    </span> faces
                </div>
                
                <div class="flex space-x-1 justify-center">
                    <!-- Previous page button -->
                    <button
                        class="h-9 w-9 flex items-center justify-center border border-gray-200 text-gray-600 rounded-md disabled:opacity-40 disabled:cursor-not-allowed hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50 transition-colors duration-150"
                        disabled={currentPage === 1}
                        onclick={prevPage}
                    >
                        <ChevronLeft class="w-4.5 h-4.5" />
                    </button>

                    <!-- Page number buttons -->
                    {#each Array(getTotalPages()) as _, i}
                        <!-- Only show limited page numbers on larger pagination sets -->
                        {#if getTotalPages() <= 7 || i + 1 === 1 || i + 1 === getTotalPages() || (i + 1 >= currentPage - 1 && i + 1 <= currentPage + 1)}
                            <button
                                class="h-9 min-w-9 px-3 flex items-center justify-center text-sm rounded-md transition-colors duration-150
                                       {currentPage === i + 1
                                    ? 'bg-indigo-600 text-white border border-indigo-600 font-medium shadow-sm'
                                    : 'border border-gray-200 text-gray-700 hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50'}"
                                onclick={() => goToPage(i + 1)}
                            >
                                {i + 1}
                            </button>
                        {:else if i + 1 === currentPage - 2 || i + 1 === currentPage + 2}
                            <span class="flex items-center justify-center h-9 w-9 text-gray-500">•••</span>
                        {/if}
                    {/each}

                    <!-- Next page button -->
                    <button
                        class="h-9 w-9 flex items-center justify-center border border-gray-200 text-gray-600 rounded-md disabled:opacity-40 disabled:cursor-not-allowed hover:border-indigo-300 hover:text-indigo-600 hover:bg-indigo-50 transition-colors duration-150"
                        disabled={currentPage === getTotalPages()}
                        onclick={nextPage}
                    >
                        <ChevronRight class="w-4.5 h-4.5" />
                    </button>
                </div>
            </div>
        {/if}
    {/if}
</div>

<!-- Detail dialog -->
{#if showDialog && selectedFace}
    <div class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fadeIn">
        <div class="bg-white rounded-2xl shadow-2xl max-w-5xl w-full max-h-[90vh] flex flex-col overflow-hidden animate-scaleIn">
            <!-- Dialog header -->
            <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-gray-50 to-white">
                <div class="flex items-center space-x-3">
                    <div class="bg-indigo-100 p-1.5 rounded-full">
                        <User class="w-5 h-5 text-indigo-600" />
                    </div>
                    <div>
                        <h3 class="text-lg font-semibold text-gray-800">
                            Unauthorized Person Details
                        </h3>
                        <p class="text-sm text-gray-500">
                            Detected on {formatDateTime(selectedFace.created_at)}
                        </p>
                    </div>
                </div>
                <button
                    class="h-8 w-8 flex items-center justify-center rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                    onclick={closeDialog}
                >
                    <X class="w-5 h-5" />
                </button>
            </div>

            <!-- Dialog content -->
            <div class="p-6 overflow-auto flex-1 bg-white">
                <div class="grid md:grid-cols-5 gap-8">
                    <!-- Face image -->
                    <div class="md:col-span-3 bg-gray-900 rounded-xl overflow-hidden flex items-center justify-center relative" style="min-height: 360px">
                        <img
                            src={`${apiUrl}/${selectedFace.image_path}`}
                            alt="Unauthorized person"
                            class="max-h-[70vh] max-w-full object-contain"
                            onerror={(e) => (e.target.src = "/placeholder-face.png")}
                        />

                        <!-- Date badge overlay -->
                        <div class="absolute top-3 left-3">
                            <div class="bg-black/70 backdrop-blur-sm flex items-start space-x-1.5 rounded-lg overflow-hidden">
                                <div class="bg-indigo-600 text-white px-2 py-1 flex flex-col items-center justify-center">
                                    <span class="text-xs font-medium">{new Date(selectedFace.created_at).toLocaleDateString('en-US', {month: 'short'})}</span>
                                    <span class="text-lg font-bold leading-none">{new Date(selectedFace.created_at).getDate()}</span>
                                    <span class="text-xs">{new Date(selectedFace.created_at).getFullYear()}</span>
                                </div>
                                <div class="px-2 py-1 text-white flex flex-col justify-center">
                                    <span class="text-xs font-medium">{getDayLabel(selectedFace.created_at)}</span>
                                    <span class="text-xs">{formatTime(selectedFace.created_at)}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Face details -->
                    <div class="md:col-span-2 space-y-6">
                        <!-- Status badges -->
                        <div class="flex flex-wrap gap-2">
                            <div class="bg-red-100 px-3 py-1 rounded-full text-red-700 text-sm font-medium flex items-center">
                                <AlertTriangle class="w-3.5 h-3.5 mr-1" />
                                <span>Unauthorized</span>
                            </div>
                            <div class="bg-indigo-100 px-3 py-1 rounded-full text-indigo-700 text-sm font-medium flex items-center">
                                <Calendar class="w-3.5 h-3.5 mr-1" />
                                <span>{formatDate(selectedFace.created_at)}</span>
                            </div>
                            <div class="bg-indigo-100 px-3 py-1 rounded-full text-indigo-700 text-sm font-medium flex items-center">
                                <Clock class="w-3.5 h-3.5 mr-1" />
                                <span>{formatTime(selectedFace.created_at)}</span>
                            </div>
                        </div>

                        <!-- Person details -->
                        <div class="bg-gray-50 rounded-xl p-5 border border-gray-100 space-y-4">
                            <div class="flex items-center justify-between">
                                <h4 class="text-sm font-medium text-gray-500 uppercase tracking-wider">
                                    Person Details
                                </h4>
                            </div>

                            <div>
                                <!-- Age -->
                                <div class="flex items-center justify-between py-3 border-b border-gray-200">
                                    <h4 class="text-gray-500 flex items-center">
                                        <span class="bg-indigo-100 p-1 rounded mr-2">
                                            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                                <circle cx="12" cy="8" r="5" />
                                                <path d="M20 21a8 8 0 1 0-16 0" />
                                            </svg>
                                        </span>
                                        Age Estimate
                                    </h4>
                                    <p class="text-lg font-semibold text-gray-800">
                                        {selectedFace.age || "Unknown"}
                                    </p>
                                </div>

                                <!-- Gender -->
                                <div class="flex items-center justify-between py-3 border-b border-gray-200">
                                    <h4 class="text-gray-500 flex items-center">
                                        <span class="bg-indigo-100 p-1 rounded mr-2">
                                            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                                                <circle cx="12" cy="7" r="4" />
                                            </svg>
                                        </span>
                                        Gender
                                    </h4>
                                    <p class="text-lg font-semibold text-gray-800">
                                        {selectedFace.gender || "Unknown"}
                                    </p>
                                </div>

                                <!-- Race/Ethnicity -->
                                <div class="flex items-center justify-between py-3 border-b border-gray-200">
                                    <h4 class="text-gray-500 flex items-center">
                                        <span class="bg-indigo-100 p-1 rounded mr-2">
                                            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                                <circle cx="12" cy="12" r="10" />
                                                <line x1="2" y1="12" x2="22" y2="12" />
                                                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                                            </svg>
                                        </span>
                                        Ethnicity
                                    </h4>
                                    <p class="text-lg font-semibold text-gray-800">
                                        {selectedFace.race || "Unknown"}
                                    </p>
                                </div>

                                <!-- Detection time -->
                                <div class="flex items-center justify-between py-3">
                                    <h4 class="text-gray-500 flex items-center">
                                        <span class="bg-indigo-100 p-1 rounded mr-2">
                                            <Clock class="w-4 h-4 text-indigo-600" />
                                        </span>
                                        Detection Time
                                    </h4>
                                    <p class="text-lg font-semibold text-gray-800">
                                        {formatTime(selectedFace.created_at)}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <!-- Action buttons -->
                        <div class="space-y-3">
                            <h4 class="text-sm font-medium text-gray-500">
                                Security Actions
                            </h4>
                            <div class="flex flex-col space-y-2">
                                <button class="w-full py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors duration-150 flex items-center justify-center">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                                        <polyline points="22 4 12 14.01 9 11.01" />
                                    </svg>
                                    Register as Authorized
                                </button>
                                <button class="w-full py-2.5 border border-red-200 hover:bg-red-50 text-red-600 font-medium rounded-lg transition-colors duration-150 flex items-center justify-center">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                        <path d="M18 6L6 18" />
                                        <path d="M6 6l12 12" />
                                    </svg>
                                    Mark as Threat
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Dialog footer -->
            <div class="px-6 py-4 border-t border-gray-100 flex justify-between bg-gray-50">
                <div class="text-sm text-gray-500 flex items-center">
                    <Clock class="w-4 h-4 mr-1 text-gray-400" />
                    Detected {formatDateTime(selectedFace.created_at)}
                </div>
                <button
                    class="px-5 py-2 bg-white hover:bg-gray-50 text-gray-700 font-medium rounded-lg border border-gray-200 shadow-sm transition-colors duration-150 flex items-center"
                    onclick={closeDialog}
                >
                    <X class="w-4 h-4 mr-1.5" />
                    Close Window
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    @keyframes spin {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    @keyframes scaleIn {
        from {
            transform: scale(0.95);
            opacity: 0;
        }
        to {
            transform: scale(1);
            opacity: 1;
        }
    }

    .animate-spin {
        animation: spin 1s linear infinite;
    }

    .animate-fadeIn {
        animation: fadeIn 0.2s ease-out forwards;
    }

    .animate-scaleIn {
        animation: scaleIn 0.25s ease-out forwards;
    }
</style>