<script>
    let showModal = false;
  </script>
  
  {#if showModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center">
    <div class="bg-gray-800 text-white rounded-lg shadow-lg w-1/3 p-6">
      <h3 class="text-lg font-bold">Confirm Action</h3>
      <p class="mt-4">Are you sure you want to proceed?</p>
      <div class="mt-6 flex justify-end space-x-4">
        <button class="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-md" on:click={() => (showModal = false)}>
          Cancel
        </button>
        <button class="px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-md">Confirm</button>
      </div>
    </div>
  </div>
  {/if}
  
  <button 
    class="bg-blue-500 px-4 py-2 rounded-md text-white"
    on:click={() => (showModal = true)}
  >
    Open Modal
  </button>
  