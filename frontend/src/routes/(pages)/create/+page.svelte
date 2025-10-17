<script lang="ts">
    import { Alert } from "$lib/components/ui/alert";
    import { Button } from "$lib/components/ui/button";
    import { Checkbox } from "$lib/components/ui/checkbox";
    import FileUploader from "$lib/components/ui/file-uploader/file-uploader.svelte";
    import { Label } from "$lib/components/ui/label";
    import { Spinner } from "$lib/components/ui/spinner";

    let promptFiles: File[] = [];
    let imageFile: File[] = [];

    let isSubmitting = false;
    let errorMessage = "";
    let success = false;
    let ocr = false;

    let extractedText = "";
    let imageUrl = "";

    let isUploadingToGCS = false;
    let gcsUploadSuccess = false;
    let gcsUploadError = "";

    async function uploadToGCS(event: Event) {
        event.preventDefault();
        isUploadingToGCS = true;
        gcsUploadError = "";
        gcsUploadSuccess = false;

        if (!imageUrl) {
            gcsUploadError = "No image available to upload.";
            isUploadingToGCS = false;
            return;
        }

        try {
            const formData = new FormData();
            formData.append("image_url", imageUrl);

            const gcsResponse = await fetch(
                import.meta.env.VITE_BACKEND_URL + "/api/fetch-and-upload",
                {
                    method: "POST",
                    body: formData,
                },
            );

            const result = await gcsResponse.json();

            if (gcsResponse.ok) {
                gcsUploadSuccess = true;
            } else {
                gcsUploadError = result?.message || "Upload to GCS failed.";
            }
        } catch (err) {
            gcsUploadError =
                (err as Error).message || "Unknown error during GCS upload.";
        } finally {
            isUploadingToGCS = false;
        }
    }

    async function handleSubmit(event: Event) {
        event.preventDefault();
        errorMessage = "";
        success = false;
        isSubmitting = true;

        if (promptFiles.length === 0) {
            errorMessage = "At least one prompt file is required.";
            isSubmitting = false;
            return;
        }

        try {
            const formData = new FormData();
            promptFiles.forEach((file) => formData.append("prompt", file));
            if (imageFile.length > 0) {
                formData.append("image", imageFile[0]);
            }
            formData.append("ocr", ocr ? "true" : "false");

            const response = await fetch(
                import.meta.env.VITE_BACKEND_URL + "/api/upload",
                {
                    method: "POST",
                    body: formData,
                },
            );

            const data = await response.json().catch(() => null);

            if (response.ok) {
                success = true;
                imageUrl = data?.image_url || "";
                extractedText = data?.extracted_text || "";
            } else {
                errorMessage = data?.message || "Upload failed";
                imageUrl = data?.image_url || "";
                extractedText = data?.extracted_text || "";
            }
        } catch (err) {
            errorMessage = (err as Error).message || "Unknown error occurred";
        } finally {
            isSubmitting = false;
        }
    }
</script>

<form class="gap-8 flex flex-col" on:submit={handleSubmit}>
    <div>
        <h1 class="font-bold mb-1">Custom Prompts</h1>
        <p class="mb-3">
            Prompts as text files. If several are uploaded they will be
            combined.
        </p>

        <Label for="prompt">
            <FileUploader
                bind:files={promptFiles}
                accept="text/plain"
                multiple={true}
            />
        </Label>
    </div>

    <div>
        <h2 class="font-bold mb-1">Base Image (sample image to feed AI)</h2>
        <Label for="image">
            <FileUploader
                bind:files={imageFile}
                accept="image"
                multiple={false}
            />
        </Label>
    </div>

    <div class="mb-6">
        <h2 class="font-bold mb-2">OCR</h2>
        <p class="mb-2">
            Should the generated image be OCR'd to ensure the text content
            aligns with the prompted image.
        </p>
        <label
            for="ocr"
            class="inline-flex items-center cursor-pointer select-none"
        >
            <Checkbox bind:checked={ocr} id="ocr" class="mr-2" />
            <span>Enable OCR</span>
        </label>
    </div>

    <Button variant="outline" type="submit" disabled={isSubmitting}>
        {#if isSubmitting}
            <Spinner class="inline-block mr-2" />
            Uploading...
        {:else}
            Generate Image
        {/if}
    </Button>

    {#if errorMessage}
        <Alert variant="destructive" class="mt-4 space-y-1 flex flex-col">
            <h2 class="font-semibold text-red-600">Upload Failed</h2>
            <p class="text-sm text-muted-foreground">{errorMessage}</p>

            {#if extractedText}
                <p class="text-xs mt-2 text-gray-500 break-words max-w-full">
                    Extracted text from image: <br />
                    <span class="font-mono whitespace-pre-wrap"
                        >{extractedText}</span
                    >
                </p>
            {/if}
        </Alert>
    {:else if success}
        <Alert variant="default" class="mt-4 space-y-1 flex flex-col">
            <h2 class="font-semibold text-green-700">Success</h2>
            <p class="text-sm text-muted-foreground">
                Image generation started successfully!
            </p>

            {#if imageUrl}
                <!-- svelte-ignore a11y_img_redundant_alt -->
                <img
                    src={imageUrl}
                    alt="The Generated Image"
                    class="mt-2 w-64 rounded border"
                    style="max-width: 100%; height: auto;"
                    on:error={() => console.error("Failed to load image")}
                />
            {/if}
        </Alert>
    {/if}

    {#if imageUrl}
        <!-- svelte-ignore a11y_img_redundant_alt -->
        <img
            src={imageUrl}
            alt="The Generated Image"
            class="mt-2 w-64 rounded border"
            style="max-width: 100%; height: auto;"
            on:error={() => console.error("Failed to load image")}
        />

        <Button
            variant="secondary"
            class="mt-4 w-fit"
            disabled={isUploadingToGCS}
            onclick={uploadToGCS}
            type="button"
        >
            {#if isUploadingToGCS}
                <Spinner class="inline-block mr-2" />
                Uploading to GCS...
            {:else}
                Upload to Google Cloud
            {/if}
        </Button>

        {#if gcsUploadSuccess}
            <p class="text-green-600 text-sm mt-2">
                Image successfully uploaded to Google Cloud Storage.
            </p>
        {:else if gcsUploadError}
            <p class="text-red-600 text-sm mt-2">Error: {gcsUploadError}</p>
        {/if}
    {/if}
</form>
