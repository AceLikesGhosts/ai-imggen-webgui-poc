from fastapi import FastAPI, HTTPException, Form
import urllib.parse
from datetime import datetime
import secrets
from fastapi import UploadFile
import requests
import tempfile
import io
from PIL import Image
import pytesseract
import os
import openai
from dotenv import load_dotenv
from typing import List, Optional
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi import FastAPI
import uvicorn
from google.cloud import storage
from google.auth.credentials import AnonymousCredentials

app = FastAPI()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


load_dotenv(".env.local")
openai.api_key = os.getenv("OPENAI_API_KEY")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_CREDENTIALS_JSON = os.getenv("GCS_CREDENTIALS_JSON")

if GCS_CREDENTIALS_JSON:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCS_CREDENTIALS_JSON

app = FastAPI()


load_dotenv(".env.local")

app = FastAPI()

openai_api_key = os.getenv("OPENAI_API_KEY")
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_CREDENTIALS_JSON = os.getenv("GCS_CREDENTIALS_JSON")
GCS_EMULATOR_HOST = os.getenv("GCS_EMULATOR_HOST")

GCS_CREDENTIALS_JSON = os.getenv("GCS_CREDENTIALS_JSON")

if GCS_CREDENTIALS_JSON and os.path.isfile(GCS_CREDENTIALS_JSON):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCS_CREDENTIALS_JSON
    print(f"Using credentials file: {GCS_CREDENTIALS_JSON}")
else:
    os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
    print("Unset GOOGLE_APPLICATION_CREDENTIALS env var since no valid file provided")

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


def get_storage_client():
    emulator_host = os.getenv("GCS_EMULATOR_HOST")
    client_options = {"api_endpoint": emulator_host} if emulator_host else None

    if emulator_host:
        return storage.Client(
            credentials=AnonymousCredentials(),
            client_options=client_options,
            project="test-project"
        )
    else:
        return storage.Client(client_options=client_options)


def upload_to_gcs(file_bytes: bytes, destination_blob_name: str, content_type: str = "image/png") -> str:
    try:
        client = get_storage_client()
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(file_bytes, content_type=content_type)

        if GCS_EMULATOR_HOST:
            return f"{GCS_EMULATOR_HOST}/storage/v1/b/{GCS_BUCKET_NAME}/o/{urllib.parse.quote(destination_blob_name)}?alt=media"
        else:
            blob.make_public()
            return blob.public_url
    except Exception as e:
        raise Exception(f"GCS Upload failed: {str(e)}")


@app.get("/api/images")
def list_uploaded_images():
    try:
        client = get_storage_client()
        bucket = client.bucket(GCS_BUCKET_NAME)

        blobs = bucket.list_blobs(prefix="generated")

        image_urls = []

        for blob in blobs:
            if not blob.name.endswith("/"):
                if GCS_EMULATOR_HOST:
                    url = f"{GCS_EMULATOR_HOST}/storage/v1/b/{GCS_BUCKET_NAME}/o/{urllib.parse.quote(blob.name)}?alt=media"
                else:
                    url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{blob.name}"

                image_urls.append({
                    "name": blob.name,
                    "url": url,
                })

        def extract_timestamp_key(blob_item):
            try:
                base = os.path.basename(blob_item["name"])
                ts_part = base.split("_")[0]
                return ts_part
            except Exception:
                return ""

        image_urls.sort(key=extract_timestamp_key, reverse=True)

        return JSONResponse(status_code=200, content={"images": image_urls})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/fetch-and-upload")
async def fetch_and_upload_to_gcs(
    image_url: str = Form(...),
):
    try:
        parsed = urllib.parse.urlparse(image_url)
        if not parsed.scheme.startswith("http"):
            raise HTTPException(status_code=400, detail="Invalid image URL.")

        response = requests.get(image_url)
        if response.status_code != 200:
            raise HTTPException(
                status_code=500, detail="Failed to fetch image.")

        file_bytes = response.content

        timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        random_hex = secrets.token_hex(2)
        destination_blob_name = f"generated/{timestamp}-{random_hex}_proxied-image.png"

        gcs_url = upload_to_gcs(
            file_bytes, destination_blob_name, content_type="image/png")

        return JSONResponse(status_code=200, content={"gcs_url": gcs_url})

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Fetch and upload failed: {str(e)}")


@app.post("/api/upload")
async def upload_file(
        prompt: List[UploadFile] = File(...),
        image: Optional[UploadFile] = File(None),
        ocr: Optional[str] = Form("false"),
):
    ocr = ocr.lower() == "true"

    try:
        combined_prompt = ""
        for file in prompt:
            content = await file.read()
            combined_prompt += content.decode("utf-8") + "\n"
        combined_prompt = combined_prompt.strip()

        if not combined_prompt:
            raise HTTPException(status_code=400, detail="Prompt is empty")

        if image:
            image_bytes = await image.read()
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_image:
                temp_image.write(image_bytes)
                temp_image.flush()

            # Step 1: Use GPT to generate a style description from the prompt
            system_msg = "You are an assistant that summarizes the artistic style of an image based on its prompt."
            user_msg = (
                f"Given the following prompt for an image, describe the artistic style or theme "
                f"in a few keywords or short phrases. Only reply with the keywords.\n\nPrompt:\n{combined_prompt}"
            )
            llm_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0,
                max_tokens=50
            )
            style_desc = llm_response.choices[0].message.content.strip()

            new_prompt = f"{combined_prompt}, in the style of {style_desc}"

            response = openai.images.generate(
                prompt=new_prompt,
                n=1,
                size="1024x1024",
                model="dall-e-3",
                response_format="url"
            )
            image_url = response.data[0].url
        else:
            response = openai.images.generate(
                prompt=combined_prompt,
                n=1,
                size="1024x1024",
                model="dall-e-3",
                response_format="url"
            )
            image_url = response.data[0].url

        gen_image_response = requests.get(image_url)
        if gen_image_response.status_code != 200:
            raise HTTPException(
                status_code=500, detail="Failed to fetch generated image")
        generated_image_bytes = gen_image_response.content

        extracted_text = ""

        if ocr:
            try:
                with Image.open(io.BytesIO(generated_image_bytes)) as img:
                    extracted_text = pytesseract.image_to_string(img).strip()
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"OCR failed: {str(e)}")

            system_msg = "You are an assistant that extracts the expected text content from an image generation prompt."
            user_msg = f"Given the following prompt, what is the expected text that should appear in the generated image? Reply only with the exact expected text.\n\nPrompt:\n{combined_prompt}"

            llm_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0,
                max_tokens=100
            )
            intended_text = llm_response.choices[0].message.content.strip()

            normalized_ocr = extracted_text.lower().strip()
            normalized_intended = intended_text.lower().strip()

            if normalized_intended in normalized_ocr or normalized_ocr in normalized_intended:
                return JSONResponse(
                    status_code=200,
                    content={
                        "message": "Upload and OCR validation successful",
                        "image_url": image_url,
                        "extracted_text": extracted_text,
                        "expected_text": intended_text
                    }
                )
            else:
                return JSONResponse(
                    status_code=400,
                    content={
                        "message": "Text in image doesn't match the expected text extracted from prompt",
                        "image_url": image_url,
                        "extracted_text": extracted_text,
                        "expected_text": intended_text
                    }
                )
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Upload successful (no OCR validation)",
                    "image_url": image_url,
                    "extracted_text": extracted_text
                }
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
