<script>
    import { page } from "$app/state";
    import { goto } from "$app/navigation";
    import Container from "$lib/components/Container.svelte";
    import { onMount, onDestroy } from "svelte";
    import Spinner from "$lib/components/Spinner.svelte"; // Assuming you have a spinner component

    const apiUrl = import.meta.env.VITE_PUBLIC_API_URL;
    const tokenParams = page.url.searchParams.get("tokenid");

    let bg = "bg-gray-100";
    let video;
    let canvas;

    let streaming = false;
    let detectionActive = $state(false);
    let status = $state("Waiting to start");
    let frameInterval;
    let isProcessing = $state(false);
    let errorMessage = $state("");
    let loadingStates = $state({}); // Track loading state for each face

    let newlyDetectedFaces = $state([]);
    let savedImages = $state([]);
    const MAX_IMAGES = 3;

    onMount(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false,
            });
            if (video) {
                video.srcObject = stream;
                video.play();
            }
            await fetchSavedImages();
        } catch (err) {
            console.error("Error accessing camera:", err);
            status = "Error accessing camera";
            errorMessage = "Unable to access camera. Please check your camera permissions.";
        }
    });

    onDestroy(() => {
        if (frameInterval) clearInterval(frameInterval);
        if (video?.srcObject) {
            video.srcObject.getTracks().forEach((track) => track.stop());
        }
    });

    async function fetchSavedImages() {
        try {
            isProcessing = true;
            const res = await fetch(
                `${apiUrl}/faces/get_saved_images?user_id=${tokenParams}`,
            );
            const data = await res.json();
            if (data.success) {
                savedImages = data.images || [];
                newlyDetectedFaces = newlyDetectedFaces.filter((filename) =>
                    savedImages.includes(filename),
                );

                if (savedImages.length >= MAX_IMAGES) {
                    status = "Maximum images saved. Redirecting to login...";
                    goto("/auth/login");
                }
            }
        } catch (err) {
            console.error("Error fetching saved images:", err);
            errorMessage = "Failed to fetch saved images. Please try refreshing the page.";
        } finally {
            isProcessing = false;
        }
    }

    async function captureFrame() {
        if (!streaming || !canvas || savedImages.length >= MAX_IMAGES) return;

        try {
            isProcessing = true;
            errorMessage = "";
            
            const context = canvas.getContext("2d");
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            const blob = await new Promise((resolve) =>
                canvas.toBlob(resolve, "image/jpeg"),
            );
            const formData = new FormData();
            formData.append("image", blob, "capture.jpg");

            const response = await fetch(
                `${apiUrl}/faces/process_frame/${tokenParams}`,
                { method: "POST", body: formData },
            );
            const data = await response.json();

            if (data.success && data.faces?.length) {
                data.faces.forEach((face) => {
                    if (!newlyDetectedFaces.includes(face)) {
                        newlyDetectedFaces = [...newlyDetectedFaces, face];
                    }
                });
                status = `Detected ${data.faces.length} face(s)`;
            } else {
                status = data.message || "No faces detected";
                if (data.message?.includes("Maximum")) {
                    detectionActive = false;
                    if (frameInterval) clearInterval(frameInterval);
                }
            }
        } catch (err) {
            console.error("Error processing frame:", err);
            status = "Error communicating with server";
            errorMessage = "Failed to process image. Please try again.";
        } finally {
            isProcessing = false;
        }
    }

    async function keepFace(filename) {
        if (savedImages.length >= MAX_IMAGES) {
            status = `Maximum ${MAX_IMAGES} faces allowed`;
            return;
        }

        try {
            loadingStates[filename] = true;
            loadingStates = loadingStates; // Trigger reactivity

            // First save to DB
            await saveFaceToDB(filename);
            
            // Then update local state
            savedImages = [filename, ...savedImages];
            newlyDetectedFaces = newlyDetectedFaces.filter((f) => f !== filename);
            status = `Face saved (${savedImages.length}/${MAX_IMAGES})`;

            // If maximum number of images reached, activate user and redirect
            if (savedImages.length >= MAX_IMAGES) {
                const response = await fetch(
                    `${apiUrl}/users/activate?user_id=${tokenParams}`,
                    { method: "POST" },
                );
                const data = await response.json();
                if (data.success) {
                    status = "User activated";
                    alert(
                        `Maximum ${MAX_IMAGES} faces have been saved. You will be redirected to the login page.`,
                    );
                    goto("/auth/login");
                } else {
                    throw new Error(data.message || "Error activating user");
                }
            }
        } catch (err) {
            console.error("Error saving face:", err);
            errorMessage = "Failed to save face. Please try again.";
            status = "Error saving face";
        } finally {
            loadingStates[filename] = false;
            loadingStates = loadingStates; // Trigger reactivity
        }
    }

    async function saveFaceToDB(filename) {
        const response = await fetch(
            `${apiUrl}/faces/save_face?filename=${filename}&user_id=${tokenParams}`,
            { method: "POST" },
        );
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || "Error saving face to database");
        }
        return data;
    }

    async function deleteFace(filename) {
        try {
            loadingStates[filename] = true;
            loadingStates = loadingStates;
            
            const response = await fetch(
                `${apiUrl}/faces/delete_face?filename=${filename}&user_id=${tokenParams}`,
                { method: "DELETE" },
            );
            const data = await response.json();
            if (data.success) {
                status = "Face deleted successfully";
                newlyDetectedFaces = newlyDetectedFaces.filter(
                    (f) => f !== filename,
                );
                savedImages = savedImages.filter((f) => f !== filename);
                if (savedImages.length < MAX_IMAGES && !detectionActive) {
                    toggleDetection();
                }
            } else {
                throw new Error(data.message || "Error deleting face");
            }
        } catch (err) {
            console.error("Error deleting face:", err);
            errorMessage = "Failed to delete face. Please try again.";
            status = "Error deleting face";
        } finally {
            loadingStates[filename] = false;
            loadingStates = loadingStates;
        }
    }

    function toggleDetection() {
        if (savedImages.length >= MAX_IMAGES) return;

        detectionActive = !detectionActive;
        if (detectionActive) {
            status = "Detection active";
            errorMessage = "";
            frameInterval = setInterval(captureFrame, 5000);
        } else {
            status = "Detection stopped";
            if (frameInterval) clearInterval(frameInterval);
        }
    }

    function handleCanPlay() {
        streaming = true;
        status = "Camera ready";
    }
</script>

<svelte:head>
    <title>Face Registration</title>
</svelte:head>

<Container {bg}>
    <div class="flex flex-col items-center gap-4">
        <h1 class="text-2xl font-bold mb-4">Face Registration</h1>
        
        {#if errorMessage}
            <div class="w-full max-w-2xl bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
                <span class="block sm:inline">{errorMessage}</span>
            </div>
        {/if}

        <video
            bind:this={video}
            class="w-full max-w-2xl border border-gray-300 rounded-lg shadow-lg"
            oncanplay={handleCanPlay}
        >
            <track kind="captions" />
            Video stream not available.
        </video>

        <div class="flex flex-col items-center gap-2">
            <button
                onclick={toggleDetection}
                class="px-6 py-2 {detectionActive
                    ? 'bg-red-500 hover:bg-red-600'
                    : 'bg-blue-500 hover:bg-blue-600'} text-white rounded-lg shadow transition-colors duration-200 relative"
                disabled={savedImages.length >= MAX_IMAGES || isProcessing}
            >
                {#if isProcessing}
                    <Spinner size="small" />
                {:else}
                    {detectionActive ? "Stop Detection" : "Start Detection"}
                {/if}
            </button>

            {#if savedImages.length >= MAX_IMAGES}
                <span class="text-sm text-red-600">
                    Maximum {MAX_IMAGES} faces reached
                </span>
            {/if}
        </div>

        <div class="text-lg font-medium flex items-center gap-2">
            <span>Status: {status}</span>
            <span class="text-blue-600">({savedImages.length}/{MAX_IMAGES} saved)</span>
        </div>

        <canvas bind:this={canvas} class="hidden"></canvas>

        {#if newlyDetectedFaces.length > 0}
            <div class="mt-6 w-full max-w-4xl">
                <h2 class="text-xl font-bold mb-4">Newly Detected Faces</h2>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {#each newlyDetectedFaces as filename}
                        <div class="border rounded-lg shadow-md p-3 flex flex-col items-center bg-white">
                            <div class="relative w-full">
                                <img
                                    src={`${apiUrl}/faces/detected_faces/${filename}`}
                                    alt="Detected face"
                                    class="object-cover w-full rounded"
                                />
                                {#if loadingStates[filename]}
                                    <div class="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded">
                                        <Spinner size="medium" />
                                    </div>
                                {/if}
                            </div>
                            <div class="flex gap-2 mt-3 w-full">
                                <button
                                    class="flex-1 bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                    onclick={() => keepFace(filename)}
                                    disabled={savedImages.length >= MAX_IMAGES || loadingStates[filename]}
                                >
                                    {loadingStates[filename] ? 'Saving...' : 'Keep'}
                                </button>
                                <button
                                    class="flex-1 bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                    onclick={() => deleteFace(filename)}
                                    disabled={loadingStates[filename]}
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    {/each}
                </div>
            </div>
        {/if}

        {#if savedImages.length > 0}
            <div class="mt-6 w-full max-w-4xl">
                <h2 class="text-xl font-bold mb-4">
                    Saved Faces ({savedImages.length}/{MAX_IMAGES})
                </h2>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {#each savedImages as filename}
                        <div class="border rounded-lg shadow-md p-3 flex flex-col items-center bg-white">
                            <div class="relative w-full">
                                <img
                                    src={`${apiUrl}/faces/detected_faces/${filename}`}
                                    alt="Saved face"
                                    class="object-cover w-full rounded"
                                />
                                {#if loadingStates[filename]}
                                    <div class="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded">
                                        <Spinner size="medium" />
                                    </div>
                                {/if}
                            </div>
                            <button
                                class="mt-3 w-full bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                onclick={() => deleteFace(filename)}
                                disabled={loadingStates[filename]}
                            >
                                {loadingStates[filename] ? 'Deleting...' : 'Delete'}
                            </button>
                        </div>
                    {/each}
                </div>
            </div>
        {/if}
    </div>
</Container>

<style>
    video {
        transform: scaleX(-1);
    }
    img {
        transform: scaleX(-1);
    }
</style>