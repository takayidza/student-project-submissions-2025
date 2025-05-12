<script>
    export let type = "primary";
  </script>
  
  <button
    class={`px-4 py-2 rounded-md ${
      type === "primary"
        ? "bg-blue-500 hover:bg-blue-600 text-white"
        : "bg-gray-500 hover:bg-gray-600 text-white"
    }`}
  >
    <slot></slot>
  </button>
  