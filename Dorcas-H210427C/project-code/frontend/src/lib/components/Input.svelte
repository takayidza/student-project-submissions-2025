<script>
    let {label, type, id, name, placeholder, required, value} = $props();
</script>

<div class="space-y-2">
    <!-- Label -->
    {#if label}
        <label for={id} class="block text-sm font-medium text-gray-300">
            {label}
        </label>
    {/if}
    <input
        {type}
        {id}
        bind:value
        {name}
        {placeholder}
        class="w-full px-4 py-2 bg-gray-700 border border-gray-600 text-white rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none"
        {required}
    />
</div>
