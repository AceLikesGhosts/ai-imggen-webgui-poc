<script lang="ts">
    import { cn } from "$lib/utils";

    export let accept = "image/,text/plain";
    export let multiple = true;
    export let files: File[] = [];

    let name = "file-upload-" + Math.random();

    let dragActive = false;
    let previews: { file: File; url?: string; text?: string }[] = [];
    let errors: string[] = [];

    $: allowMore = multiple || files.length === 0;

    function handleFiles(selectedFiles: FileList | File[]) {
        let filesArray = Array.from(selectedFiles);
        const newErrors: string[] = [];

        if (!multiple) {
            // NOTE: firefox does not respect the `multiple`
            // input tag property, so we have to ensure this
            // does not happen ourselves. Thank you Mozilla,
            // and your 10 year old bugs.
            filesArray = [filesArray[filesArray.length - 1]];
            files = [];
            previews = [];
        }

        const validFiles: File[] = [];

        filesArray.forEach((file) => {
            const isValid = accept
                .split(",")
                .some((v) => file.type.startsWith(v));

            if (!isValid) {
                newErrors.push(`Unsupported file type: ${file.name}`);
                return;
            }

            validFiles.push(file);

            if (file.type.startsWith("image/")) {
                previews = [
                    ...previews,
                    { file, url: URL.createObjectURL(file) },
                ];
            } else if (file.type === "text/plain") {
                const reader = new FileReader();
                reader.onload = () => {
                    previews = [
                        ...previews,
                        { file, text: reader.result as string },
                    ];
                };
                reader.readAsText(file);
            }
        });

        files = [...files, ...validFiles];
        errors = newErrors;
    }

    function handleDrop(event: DragEvent) {
        event.preventDefault();
        dragActive = false;
        if (event.dataTransfer?.files) {
            handleFiles(event.dataTransfer.files);
        }
    }

    function handleDragOver(event: DragEvent) {
        event.preventDefault();
        dragActive = true;
    }

    function handleDragLeave() {
        dragActive = false;
    }

    function handleInputChange(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files) {
            handleFiles(target.files);
        }
    }
</script>

<div
    role="none"
    class={cn(
        "border-2 border-dashed rounded-lg p-6 text-center transition-colors",
        dragActive ? "border-primary bg-muted" : "border-border",
    )}
    on:drop={handleDrop}
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
>
    <label for={name} class="cursor-pointer space-y-2 block">
        <input
            type="file"
            {accept}
            {multiple}
            class="hidden"
            id={name}
            on:change={handleInputChange}
        />

        {#if allowMore}
            <div class="text-sm text-muted-foreground">
                Drag & drop your files here or click to upload
            </div>
        {/if}

        {#if errors.length > 0}
            <ul class="mt-4 text-sm text-red-600 space-y-1 text-left">
                {#each errors as error}
                    <li>{error}</li>
                {/each}
            </ul>
        {/if}
    </label>

    {#if previews.length > 0}
        <div
            class="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-left"
        >
            {#each previews as { file, url, text }}
                <div class="relative p-2 border rounded bg-muted">
                    <p class="text-xs font-medium mb-1 truncate">{file.name}</p>

                    {#if url}
                        <img
                            src={url}
                            alt={file.name}
                            class="rounded-md object-cover h-[100px] w-[100px] mx-auto"
                        />
                    {:else if text}
                        <div
                            class="max-h-[150px] overflow-auto rounded bg-background border p-2 text-xs whitespace-pre-wrap font-mono"
                        >
                            {text}
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}
</div>
