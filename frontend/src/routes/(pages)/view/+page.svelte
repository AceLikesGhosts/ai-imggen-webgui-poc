<script lang="ts">
    import { Button } from "$lib/components/ui/button";
    import { onMount } from "svelte";

    let images: { name: string; url: string }[] = [];
    let isLoading = false;
    let error = "";

    async function fetchImages() {
        isLoading = true;
        try {
            const response = await fetch(
                import.meta.env.VITE_BACKEND_URL + "/api/images",
            );
            const data = await response.json();
            images = data.images || [];
        } catch (err) {
            error = "Failed to load images.";
        } finally {
            isLoading = false;
        }
    }

    onMount(fetchImages);
</script>

<Button onclick={fetchImages} variant="outline">Reload</Button>

{#if isLoading}
    <p>Loading images...</p>
{:else if error}
    <p class="text-red-500">{error}</p>
{:else}
    <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
        {#each images as image}
            <img
                src={image.url}
                alt={image.name}
                class="w-full h-auto rounded shadow"
            />
        {/each}
    </div>
{/if}
