<!-- src/routes/+page.svelte -->
<script>
  import { onMount, onDestroy } from "svelte";
  import Container from "$lib/components/Container.svelte";
  import { goto } from "$app/navigation";
  import { enhance } from "$app/forms";
  import { CheckCircle2, XCircle, Loader2, Camera, AlertTriangle } from "lucide-svelte";
  import { page } from "$app/stores"; // Import the page store

  // Use the page store to get URL parameters
  let tokenParams = $derived($page.url.searchParams.get("tokenid"));
  const apiUrl = import.meta.env.VITE_PUBLIC_API_URL;

  // State management with Svelte 5 runes
  let video = $state(null);
  let canvas = $state(null);
  let status = $state("Initializing camera...");
  let attempts = $state(0);
  let locked = $state(false);
  let frameInterval = $state(null);
  let lastVerificationImage = $state(null);
  let verificationConfidence = $state(null);
  let isVerifying = $state(false);
  let verificationState = $state("idle");
  let blockTimeSeconds = $state(30);
  let countdownValue = $state(0);
  let countdownInterval = $state(null);
  let abortController = $state(new AbortController());
  let verificationSuccess = $state(false);
  let redirectTriggered = $state(false);
  let userData = $state(null);

  // Constants for configuration
  const MAX_ATTEMPTS = 3;
  const VERIFICATION_INTERVAL = 5000;
  const REDIRECT_COUNTDOWN = 3;

  // Get user data from page store
  function getUserData() {
    if ($page.data && $page.data.user) {
      userData = $page.data.user;
    }
  }

  // Clean up resources when needed
  function clearResources() {
    if (frameInterval) {
      clearInterval(frameInterval);
      frameInterval = null;
    }
    if (countdownInterval) {
      clearInterval(countdownInterval);
      countdownInterval = null;
    }
  }

  // Stop the camera stream
  function stopCamera() {
    if (video?.srcObject) {
      const tracks = video.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      video.srcObject = null;
    }
  }

  // Handle successful verification
  async function handleVerificationSuccess() {
    // Prevent multiple success handlers from running
    if (verificationSuccess) return;
    
    // Update state and stop verification process
    verificationSuccess = true;
    verificationState = "success";
    status = "Verification successful! Redirecting to dashboard...";
    clearResources();
    
    // Start countdown for redirect
    let count = REDIRECT_COUNTDOWN;
    const countdown = setInterval(() => {
      status = `Identity confirmed! Redirecting to dashboard in ${count} seconds...`;
      count--;
      
      if (count < 0) {
        clearInterval(countdown);
        if (!redirectTriggered) {
          redirectTriggered = true;
          submitVerification();
        }
      }
    }, 1000);
  }

  // Submit verification to server
  async function submitVerification() {
    try {
      // Create form data
      const formData = new FormData();
      
      // Call the server action to set the face_verified cookie
      const response = await fetch("?/setVerified", {
        method: "POST",
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        console.log("Verification result:", result);
        
        // Navigate to dashboard
        goto("/dashboard", { replaceState: true });
      } else {
        console.error("Failed to submit verification");
        status = "Verification system error. Please try again.";
        verificationState = "error";
        verificationSuccess = false;
      }
    } catch (error) {
      console.error("Error during verification submission:", error);
      status = "Verification system error. Please try again.";
      verificationState = "error";
      verificationSuccess = false;
    }
  }

  // Handle max attempts reached and account lock
  function handleMaxAttemptsReached() {
    locked = true;
    isVerifying = false;
    verificationState = "error";

    // Hard stop all verification activities
    abortController.abort();
    abortController = new AbortController();
    clearResources();
    stopCamera();

    // Show lockout message and start countdown
    status = `Too many failed attempts. Account locked for ${blockTimeSeconds} seconds.`;
    startCountdown(blockTimeSeconds);
    
    // Increase lockout time for next failure
    blockTimeSeconds *= 2;
  }

  // Start countdown timer for lockout
  function startCountdown(seconds) {
    countdownValue = seconds;
    countdownInterval = setInterval(() => {
      countdownValue--;
      
      if (countdownValue <= 0) {
        clearInterval(countdownInterval);
        status = "Verification unlocked. Starting new verification session.";
        locked = false;
        attempts = 0;
        
        // Restart verification after delay
        setTimeout(() => {
          verificationState = "idle";
          initializeCamera();
        }, 2000);
      } else {
        status = `Account temporarily locked. Please wait ${countdownValue} seconds before trying again.`;
      }
    }, 1000);
  }

  // Perform face verification against backend
  async function verifyFace() {
    // Skip verification if locked, already verifying, or already successful
    if (locked || isVerifying || verificationSuccess) return false;
    
    // Update state for verification in progress
    isVerifying = true;
    verificationState = "loading";

    // Show attempt number in status
    const attemptNumber = attempts + 1;
    status = `Verifying your identity (Attempt ${attemptNumber}/${MAX_ATTEMPTS})...`;

    try {
      // Capture image from video
      const context = canvas.getContext("2d");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0);
      
      // Convert canvas to blob
      const blob = await new Promise(resolve => 
        canvas.toBlob(resolve, "image/jpeg", 0.9)
      );

      // Send to backend for verification
      const response = await fetch(
        `${apiUrl}/faces/verify?user_id=${tokenParams}`,
        {
          method: "POST",
          body: createFormData(blob),
          signal: abortController.signal,
        }
      );

      // Check for error responses
      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`);
      }

      // Process result
      const result = await response.json();
      
      // Update verification image if available
      lastVerificationImage = result.verification_image
        ? `${apiUrl}/faces/verified_faces/${result.verification_image}`
        : null;

      // Update confidence level if available
      if (result.confidence !== undefined) {
        verificationConfidence = result.confidence * 100;
      }

      // Handle verification result
      return handleVerificationResult(result);
    } catch (err) {
      // Handle errors (but ignore aborted requests)
      if (err.name !== "AbortError") {
        console.error("Verification error:", err);
        verificationState = "error";
        status = "Verification system error. Please try again later.";
      }
      return false;
    } finally {
      // Always reset verification in progress state
      isVerifying = false;
    }
  }

  // Create form data for verification request
  function createFormData(blob) {
    const form = new FormData();
    form.append("image", blob);
    form.append("attempts", attempts.toString());
    form.append("blocked", (attempts >= MAX_ATTEMPTS - 1).toString());
    return form;
  }

  // Process verification result from server
  function handleVerificationResult(result) {
    if (result.success) {
      // Success case
      handleVerificationSuccess();
      return true;
    }

    // Failure case
    attempts++;
    const remainingAttempts = MAX_ATTEMPTS - attempts;

    if (attempts >= MAX_ATTEMPTS) {
      // Lock account if max attempts reached
      handleMaxAttemptsReached();
    } else {
      // Show failure message with remaining attempts
      verificationState = "error";
      status = (remainingAttempts === 1)
        ? `Verification failed. You have 1 attempt remaining.`
        : `Verification failed. You have ${remainingAttempts} attempts remaining.`;
    }

    return false;
  }

  // Initialize camera for verification
  async function initializeCamera() {
    try {
      status = "Initializing camera...";
      
      // Request camera access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: "user",
          width: { ideal: 640 },
          height: { ideal: 480 }
        }
      });
      
      // Set up video element with stream
      if (video) {
        video.srcObject = stream;
        video.play();
        
        // Update status based on attempts
        status = (attempts > 0)
          ? `Ready for verification. Attempts remaining: ${MAX_ATTEMPTS - attempts}/${MAX_ATTEMPTS}.`
          : "Please look directly at the camera for face verification.";
          
        // Start verification process
        startVerificationLoop();
      }
    } catch (err) {
      console.error("Camera access error:", err);
      status = "Camera access denied. Please enable camera permissions and reload the page.";
      verificationState = "error";
    }
  }

  // Start periodic verification checks
  function startVerificationLoop() {
    // Clear any existing interval
    if (frameInterval) clearInterval(frameInterval);

    // Skip verification loop if already verified
    if (!verificationSuccess) {
      frameInterval = setInterval(async () => {
        if (locked || isVerifying || verificationSuccess) return;
        await verifyFace();
      }, VERIFICATION_INTERVAL);
    }
  }

  // Check if already verified using cookies (only on client side)
  function checkAlreadyVerified() {
    if (typeof document !== 'undefined') {
      const cookies = document.cookie.split(';');
      const faceVerified = cookies.find(cookie => cookie.trim().startsWith('face_verified='));
      return faceVerified && faceVerified.split('=')[1] === 'true';
    }
    return false;
  }

  // Initialize component on mount
  onMount(() => {
    // Update user data
    getUserData();
    
    // Check if already verified
    if (checkAlreadyVerified()) {
      // Already verified, redirect to dashboard
      goto('/dashboard');
      return;
    }
    
    // Start verification process
    if (!verificationSuccess && !redirectTriggered && tokenParams) {
      initializeCamera();
    }
    
    // Cleanup function will be called on component destroy
    return () => {
      abortController.abort();
      clearResources();
      stopCamera();
    };
  });

  // Cleanup on component destroy
  onDestroy(() => {
    abortController.abort();
    clearResources();
    stopCamera();
  });
</script>

<svelte:head>
  <title>Face Verification | Secure Authentication</title>
</svelte:head>

<Container bg="bg-gradient-to-b from-indigo-50 to-blue-50">
  <div class="flex flex-col items-center gap-4 min-h-screen py-8 relative">
    <!-- Status bar at top -->
    <div class="absolute top-0 left-0 right-0 bg-gradient-to-r from-blue-600 to-indigo-600 text-white p-4 text-center">
      <div class="flex items-center justify-center gap-2">
        <Camera size={20} />
        <p>{status}</p>
      </div>
    </div>

    {#if verificationState !== "idle"}
      <!-- Modal overlay for verification status -->
      <div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fadeIn">
        <div class="bg-white p-8 rounded-xl shadow-2xl text-center max-w-md animate-scaleIn">
          {#if verificationState === "loading"}
            <!-- Loading state -->
            <Loader2 class="w-16 h-16 text-blue-500 animate-spin mx-auto" />
            <p class="mt-4 text-xl font-semibold text-gray-800">{status}</p>
            <p class="mt-2 text-gray-600">
              Please keep your face centered and well-lit
            </p>
          {:else if verificationState === "success"}
            <!-- Success state -->
            <CheckCircle2 class="w-16 h-16 text-green-500 mx-auto" />
            <p class="mt-4 text-xl font-semibold text-gray-800">{status}</p>
            <p class="mt-2 text-gray-600">
              Thank you for verifying your identity
            </p>
          {:else}
            <!-- Error state -->
            <XCircle class="w-16 h-16 text-red-500 mx-auto" />
            <p class="mt-4 text-xl font-semibold text-gray-800">{status}</p>

            {#if locked}
              <!-- Account locked countdown -->
              <div class="mt-6">
                <div class="h-2.5 bg-gray-200 rounded-full">
                  <div
                    class="h-2.5 bg-red-500 rounded-full transition-all duration-1000"
                    style={`width: ${(countdownValue / blockTimeSeconds) * 100}%`}
                  ></div>
                </div>
                <p class="text-sm mt-2 text-gray-600">
                  {countdownValue} seconds remaining
                </p>
              </div>
            {:else if attempts > 0 && attempts < MAX_ATTEMPTS}
              <!-- Attempt indicators -->
              <div class="mt-4">
                <div class="flex justify-center gap-2 mt-2">
                  {#each Array(MAX_ATTEMPTS) as _, i}
                    <div
                      class={`w-4 h-4 rounded-full ${i < attempts ? "bg-red-500" : "bg-gray-200"}`}
                    ></div>
                  {/each}
                </div>
                <p class="text-sm mt-2 text-gray-600">
                  {MAX_ATTEMPTS - attempts} attempts remaining
                </p>
              </div>
            {/if}
          {/if}
        </div>
      </div>
    {/if}

    <!-- Video display -->
    <div class="mt-16 relative">
      <video 
        bind:this={video} 
        class="w-full max-w-2xl rounded-xl shadow-lg border-4 border-white bg-black" 
        muted
        playsinline
        autoplay
      ></video>
      
      <!-- Camera frame guide -->
      <div class="absolute inset-0 border-4 border-dashed border-blue-400/30 rounded-xl pointer-events-none"></div>
      <div class="absolute left-1/2 top-1/2 w-48 h-48 -ml-24 -mt-28 border-4 border-blue-500/50 rounded-full pointer-events-none"></div>
    </div>
    
    <!-- Hidden canvas for processing -->
    <canvas bind:this={canvas} class="hidden"></canvas>

    <!-- Verification result image -->
    {#if lastVerificationImage}
      <div class="mt-4 text-center">
        <img
          src={lastVerificationImage}
          alt="Verification capture"
          class="w-48 h-48 object-cover rounded-lg border-4 border-white shadow-md"
        />
        {#if verificationConfidence !== null}
          <div class="mt-2 flex flex-col items-center">
            <p class="text-sm font-medium text-gray-700">
              Confidence: {verificationConfidence.toFixed(1)}%
            </p>
            <div class="w-48 h-2 bg-gray-200 rounded-full mt-1">
              <div
                class="h-2 rounded-full transition-all duration-500"
                style={`width: ${verificationConfidence}%; background-color: ${
                  verificationConfidence > 80
                    ? "#10B981"
                    : verificationConfidence > 50
                      ? "#F59E0B"
                      : "#EF4444"
                }`}
              ></div>
            </div>
          </div>
        {/if}
      </div>
    {/if}

    <!-- Idle state instructions -->
    {#if verificationState === "idle" && !isVerifying}
      <div class="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg max-w-md text-center">
        <p class="text-gray-700">
          Position your face clearly in the frame. Verification will begin automatically.
        </p>
        <div class="mt-2 flex justify-center items-center gap-1">
          <div class={`w-2 h-2 rounded-full ${attempts > 0 ? "bg-yellow-500" : "bg-green-500"}`}></div>
          <p class="text-sm text-gray-600">
            {attempts === 0
              ? "Ready to verify"
              : `${MAX_ATTEMPTS - attempts}/${MAX_ATTEMPTS} attempts remaining`}
          </p>
        </div>
      </div>
    {/if}
  </div>
</Container>

<style>
  video {
    transform: scaleX(-1);
    object-fit: cover;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes scaleIn {
    from { transform: scale(0.95); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
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