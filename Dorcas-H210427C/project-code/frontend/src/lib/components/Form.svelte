<script>
    import { enhance } from "$app/forms";
    import { form } from "$app/stores";

    let { 
        method = "post", 
        action = "?", 
        class: className = "",
        children = () => {}
    } = $props();
</script>

<!-- svelte-ignore component_name_lowercase -->
<form use:enhance {action} {method} class={className}>
    {#if $form?.error}
        <div class="bg-red-500 text-white p-2 rounded-md text-sm">
            {$form.error}
        </div>
    {/if}
    
    {@render children()}
</form>