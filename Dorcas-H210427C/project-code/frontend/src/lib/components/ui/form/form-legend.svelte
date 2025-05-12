<script>
	import * as FormPrimitive from "formsnap";
	import { cn } from "$lib/components/shadcn/utils.js";

	let { ref = $bindable(null), class: className, ...restProps } = $props();
</script>

<FormPrimitive.Legend
	bind:ref
	{...restProps}
	class={cn("data-[fs-error]:text-destructive text-sm font-medium leading-none", className)}
/>
