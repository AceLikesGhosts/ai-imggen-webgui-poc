<script>
	import { page } from "$app/stores";
	import * as ButtonGroup from "$lib/components/ui/button-group/index.js";
	import Button from "$lib/components/ui/button/button.svelte";
</script>

<div class="min-h-screen px-4 pt-[33vh]">

	<nav class="mb-12 flex justify-center relative">
		<div class="relative mx-auto -translate-x-1/2">
			<ButtonGroup.Root>
				<Button
					class={$page.url.pathname === "/create" ? "font-bold" : ""}
					variant="link"
					href="/create"
				>
					Create New Image
				</Button>
				<Button
					class={$page.url.pathname === "/view" ? "font-bold" : ""}
					variant="link"
					href="/view"
				>
					View Images
				</Button>
			</ButtonGroup.Root>
		</div>
	</nav>

	<div class="max-w-2xl mx-auto space-y-4 py-6">
		<slot />
	</div>
</div>
