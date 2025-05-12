<!-- src/routes/dashboard/+page.svelte -->
<script>
    import { onMount } from "svelte";
    import { page } from "$app/stores"; // Changed from $app/state to $app/stores
    import { Card, CardHeader, CardTitle, CardContent } from "$lib/components/ui/card";
    import { Progress } from "$lib/components/ui/progress";
    import { Shield, Users, Clock, Calendar, AlertTriangle, RefreshCw } from "lucide-svelte";
    import Chart from "chart.js/auto";
    
    // State management with Svelte 5 runes
    let successRate = $state(85);
    let totalScans = $state(0);
    let dailyScans = $state(0);
    let loadingData = $state(true);
    let errorMessage = $state(null);
    let unknownFaces = $state([]);
    let refreshing = $state(false);
    let lastUpdated = $state(new Date());
    let userId = $state(null);
    
    // Chart instances for cleanup
    let charts = $state({
        performanceChart: null,
        detectionsChart: null
    });
    
    // Get API URL
    const apiUrl = import.meta.env.VITE_PUBLIC_API_URL;
    
    // Get user ID from page data
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
    
    // Fetch unknown faces data from API
    async function fetchUnknownFaces() {
        try {
            loadingData = true;
            
            if (!userId) {
                errorMessage = "User ID not found. Please log in again.";
                return;
            }
            
            const response = await fetch(`${apiUrl}/users/unknown_faces/${userId}`);
            
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }
            
            const result = await response.json();
            unknownFaces = result.results || [];
            lastUpdated = new Date();
            
            // Calculate dashboard metrics
            calculateMetrics();
        } catch (err) {
            console.error("Error fetching data:", err);
            errorMessage = "Failed to load security data. Please try again.";
        } finally {
            loadingData = false;
            refreshing = false;
        }
    }
    
    // Calculate metrics from unknown faces data
    function calculateMetrics() {
        // Default success rate
        successRate = 85;
        
        // If no data, use defaults
        if (!unknownFaces || unknownFaces.length === 0) {
            totalScans = 0;
            dailyScans = 0;
            return;
        }
        
        // Count total faces
        totalScans = unknownFaces.length;
        
        // Process faces data
        const detectionsByDay = {};
        let today = new Date().toISOString().split('T')[0];
        
        // Group by date
        unknownFaces.forEach(face => {
            const date = new Date(face.created_at);
            const dayKey = date.toISOString().split('T')[0];
            
            detectionsByDay[dayKey] = (detectionsByDay[dayKey] || 0) + 1;
        });
        
        // Set daily scans count (today's count or 0)
        dailyScans = detectionsByDay[today] || 0;
        
        // Initialize charts with calculated data
        initializeCharts(detectionsByDay);
    }
    
    // Refresh data
    async function refreshData() {
        if (refreshing) return;
        
        refreshing = true;
        await fetchUnknownFaces();
    }
    
    // Initialize charts with data
    function initializeCharts(detectionsByDay) {
        // Clean up any existing charts
        if (charts.performanceChart) {
            charts.performanceChart.destroy();
            charts.performanceChart = null;
        }
        
        if (charts.detectionsChart) {
            charts.detectionsChart.destroy();
            charts.detectionsChart = null;
        }
        
        // Create performance chart
        const ctx1 = document.getElementById("securityPerformanceChart")?.getContext("2d");
        if (ctx1) {
            charts.performanceChart = new Chart(ctx1, {
                type: "doughnut",
                data: {
                    labels: ["Successful", "Unsuccessful"],
                    datasets: [
                        {
                            data: [
                                Math.round(totalScans * (successRate / 100)),
                                Math.round(totalScans * ((100 - successRate) / 100))
                            ],
                            backgroundColor: ["#10B981", "#EF4444"],
                            borderWidth: 0,
                            borderRadius: 5,
                        },
                    ],
                },
                options: {
                    plugins: {
                        legend: {
                            position: "bottom",
                        },
                    },
                    cutout: '70%',
                    maintainAspectRatio: false
                },
            });
        }
        
        // Create daily detections chart
        const ctx2 = document.getElementById("dailyDetectionsChart")?.getContext("2d");
        if (ctx2) {
            // Convert detections by day to array format
            const daysArray = Object.keys(detectionsByDay).sort();
            const last7Days = daysArray.slice(-7);
            
            const labels = last7Days.map(day => {
                const date = new Date(day);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            });
            
            const values = last7Days.map(day => detectionsByDay[day] || 0);
            
            charts.detectionsChart = new Chart(ctx2, {
                type: "line",
                data: {
                    labels,
                    datasets: [
                        {
                            label: "Daily Detections",
                            data: values,
                            borderColor: "#8B5CF6",
                            backgroundColor: "rgba(139, 92, 246, 0.1)",
                            fill: true,
                            tension: 0.4,
                            borderWidth: 2,
                        },
                    ],
                },
                options: {
                    plugins: {
                        legend: {
                            position: "bottom",
                        },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    },
                    maintainAspectRatio: false
                },
            });
        }
    }
    
    // Initialize on component mount
    onMount(() => {
        const unsubscribe = getUserId();
        
        // Return cleanup function
        return () => {
            if (unsubscribe) unsubscribe();
            
            if (charts.performanceChart) {
                charts.performanceChart.destroy();
            }
            
            if (charts.detectionsChart) {
                charts.detectionsChart.destroy();
            }
        };
    });
</script>

<svelte:head>
    <title>Security Dashboard | Face Recognition System</title>
</svelte:head>

<div class="p-6 space-y-6 min-h-screen">
    <!-- Dashboard header -->
    <div class="flex flex-col md:flex-row items-start justify-between gap-4 mb-6">
        <div>
            <h1 class="text-2xl font-bold text-gray-800">Security Dashboard</h1>
            <p class="text-gray-500">Monitor your face recognition system performance</p>
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
                disabled={refreshing || loadingData}
                title="Refresh data"
            >
                <RefreshCw class="h-5 w-5 text-gray-700 {refreshing ? 'animate-spin' : ''}" />
            </button>
        </div>
    </div>

    <!-- Error message -->
    {#if errorMessage}
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded">
            <div class="flex items-center">
                <AlertTriangle class="h-5 w-5 text-red-500 mr-2" />
                <p class="text-red-700">{errorMessage}</p>
            </div>
        </div>
    {/if}
    
    <!-- Loading state -->
    {#if loadingData && !refreshing}
        <div class="flex justify-center items-center h-64">
            <div class="relative">
                <div class="w-16 h-16 border-4 border-indigo-200 border-t-indigo-500 rounded-full animate-spin"></div>
                <div class="absolute inset-0 flex items-center justify-center">
                    <Shield class="h-6 w-6 text-indigo-500" />
                </div>
            </div>
        </div>
    {:else}
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Success Rate Card -->
            <Card class="overflow-hidden hover:shadow-lg transition-shadow duration-300 bg-white rounded-xl border-indigo-100">
                <div class="absolute top-0 right-0 p-2">
                    <div class="bg-green-50 p-2 rounded-md">
                        <Shield class="h-5 w-5 text-green-500" />
                    </div>
                </div>
                <CardHeader>
                    <CardTitle class="text-base text-gray-500 font-medium">Success Rate</CardTitle>
                </CardHeader>
                <CardContent>
                    <Progress
                        value={successRate}
                        class="mb-3 h-2 bg-gray-100"
                    />
                    <div class="flex items-end justify-between">
                        <p class="text-3xl font-bold text-gray-800">{successRate}%</p>
                        <p class="text-sm text-green-600">+2% from last week</p>
                    </div>
                </CardContent>
            </Card>

            <!-- Total Detections Card -->
            <Card class="overflow-hidden hover:shadow-lg transition-shadow duration-300 bg-white rounded-xl border-indigo-100">
                <div class="absolute top-0 right-0 p-2">
                    <div class="bg-indigo-50 p-2 rounded-md">
                        <Users class="h-5 w-5 text-indigo-500" />
                    </div>
                </div>
                <CardHeader>
                    <CardTitle class="text-base text-gray-500 font-medium">Total Detections</CardTitle>
                </CardHeader>
                <CardContent>
                    <p class="text-3xl font-bold text-gray-800">
                        {totalScans.toLocaleString()}
                    </p>
                    <p class="text-sm text-gray-500 mt-2">All time detections</p>
                </CardContent>
            </Card>

            <!-- Daily Detections Card -->
            <Card class="overflow-hidden hover:shadow-lg transition-shadow duration-300 bg-white rounded-xl border-indigo-100">
                <div class="absolute top-0 right-0 p-2">
                    <div class="bg-purple-50 p-2 rounded-md">
                        <Calendar class="h-5 w-5 text-purple-500" />
                    </div>
                </div>
                <CardHeader>
                    <CardTitle class="text-base text-gray-500 font-medium">Daily Detections</CardTitle>
                </CardHeader>
                <CardContent>
                    <p class="text-3xl font-bold text-gray-800">
                        {dailyScans.toLocaleString()}
                    </p>
                    <p class="text-sm text-gray-500 mt-2">Last 24 hours</p>
                </CardContent>
            </Card>
        </div>

        <!-- Charts -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Performance Chart -->
            <Card class="p-6 hover:shadow-lg transition-shadow duration-300 bg-white rounded-xl">
                <CardHeader class="px-0 pt-0">
                    <CardTitle class="text-gray-600 font-medium">
                        Recognition Success vs Failure
                    </CardTitle>
                </CardHeader>
                <CardContent class="px-0 pb-0">
                    <div class="h-[300px] relative">
                        <canvas id="securityPerformanceChart"></canvas>
                        <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <span class="text-4xl font-bold text-gray-800">{successRate}%</span>
                            <span class="text-gray-500 text-sm">Success Rate</span>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <!-- Daily Detections Chart -->
            <Card class="p-6 hover:shadow-lg transition-shadow duration-300 bg-white rounded-xl">
                <CardHeader class="px-0 pt-0"> 
                    <CardTitle class="text-gray-600 font-medium">
                        Daily Detection Trends
                    </CardTitle>
                </CardHeader>
                <CardContent class="px-0 pb-0">
                    <div class="h-[300px]">
                        <canvas id="dailyDetectionsChart"></canvas>
                    </div>
                </CardContent>
            </Card>
        </div>
        
        <!-- Recent Detections -->
        <div class="mt-6">
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-xl font-bold text-gray-800">Recent Unauthorized Detections</h2>
                
                <a 
                    href="/dashboard/faces" 
                    class="text-indigo-600 hover:text-indigo-500 text-sm font-medium"
                >
                    View all detections →
                </a>
            </div>
            
            {#if unknownFaces.length === 0}
                <!-- Empty state -->
                <Card class="p-8 text-center">
                    <div class="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                        <Shield class="w-8 h-8 text-green-600" />
                    </div>
                    <h3 class="text-lg font-medium text-gray-800 mb-2">
                        No Unauthorized Faces Detected
                    </h3>
                    <p class="text-gray-500 max-w-md mx-auto">
                        Your secure area is clear. When the system detects unauthorized faces, they will appear here for review.
                    </p>
                </Card>
            {:else}
                <!-- Face detection cards -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {#each unknownFaces.slice(0, 6) as face}
                        <Card class="overflow-hidden border border-gray-100 hover:border-indigo-200 hover:shadow-md transition-all duration-200">
                            <div class="relative h-48 bg-gray-100">
                                {#if face.image_path}
                                    <img
                                        src={`${apiUrl}/${face.image_path}`}
                                        alt="Detected face"
                                        class="w-full h-full object-cover"
                                        onerror={(e) => (e.target.src = "/placeholder-face.png")}
                                    />
                                    
                                    <!-- Date badge -->
                                    <div class="absolute top-3 left-3">
                                        <div class="bg-black/60 backdrop-blur-sm flex items-center space-x-1.5 rounded-lg px-2 py-1 text-xs text-white">
                                            <Calendar class="w-3.5 h-3.5 mr-1" />
                                            <span>{new Date(face.created_at).toLocaleDateString()}</span>
                                        </div>
                                    </div>
                                    
                                    <!-- Status badge -->
                                    <div class="absolute top-3 right-3">
                                        <div class="bg-red-100 text-red-700 text-xs px-2 py-1 rounded-full font-medium">
                                            Unauthorized
                                        </div>
                                    </div>
                                {:else}
                                    <div class="h-full flex items-center justify-center">
                                        <p class="text-gray-400">No image available</p>
                                    </div>
                                {/if}
                            </div>
                            
                            <CardContent class="p-4">
                                <div class="space-y-3">
                                    <div class="flex justify-between items-center">
                                        <span class="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded-full">
                                            ID #{face.id}
                                        </span>
                                        <span class="text-xs text-gray-500">
                                            {new Date(face.created_at).toLocaleTimeString()}
                                        </span>
                                    </div>
                                    
                                    <!-- Face attributes -->
                                    <div class="grid grid-cols-3 gap-2 mt-3">
                                        <div class="bg-gray-50 p-2 rounded text-center">
                                            <p class="text-xs text-gray-500">Age</p>
                                            <p class="font-medium">{face.age || 'N/A'}</p>
                                        </div>
                                        <div class="bg-gray-50 p-2 rounded text-center">
                                            <p class="text-xs text-gray-500">Gender</p>
                                            <p class="font-medium">{face.gender || 'N/A'}</p>
                                        </div>
                                        <div class="bg-gray-50 p-2 rounded text-center">
                                            <p class="text-xs text-gray-500">Race</p>
                                            <p class="font-medium">{face.race || 'N/A'}</p>
                                        </div>
                                    </div>
                                    
                                    <a 
                                        href="/dashboard/faces" 
                                        class="mt-3 block w-full text-center py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors"
                                    >
                                        View Details
                                    </a>
                                </div>
                            </CardContent>
                        </Card>
                    {/each}
                </div>
                
                <!-- View all link (mobile only) -->
                {#if unknownFaces.length > 6}
                    <div class="mt-6 text-center md:hidden">
                        <a 
                            href="/dashboard/faces" 
                            class="inline-flex items-center px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                        >
                            View All Detections
                        </a>
                    </div>
                {/if}
            {/if}
        </div>
    {/if}
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