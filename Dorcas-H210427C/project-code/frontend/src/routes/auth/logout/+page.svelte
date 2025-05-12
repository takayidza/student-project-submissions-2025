<script>
    import { onMount } from 'svelte';
    import { enhance } from '$app/forms';

    onMount(() => {
        // Automatically submit the form when the page loads
        document.getElementById('logoutForm').submit();
    });
</script>

<div class="flex min-h-screen items-center justify-center bg-gray-50">
    <div class="text-center">
        <div class="spinner mb-4"></div>
        <form 
            id="logoutForm" 
            method="POST" 
            use:enhance
        >
            <button type="submit" class="text-gray-600 text-lg">Logging out...</button>
        </form>
    </div>
</div>

<style>
    .spinner {
        width: 40px;
        height: 40px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #3b82f6;
        border-radius: 50%;
        margin: 0 auto;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>