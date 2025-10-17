# AI Image Generation POC

Python 3.12, OpenAI (GPT-40 + DALL-E 3), GCS, OCR, Sveltekit

- Generates AI images
- Verifies generated image text matches prompt via an LLM + OCR
- Uploads images to GCS
- Web UI with drag/drop for prompt files and preview before upload
- Web UI with ability to view all uploaded generated images.

## Demo Video
<video src="simple_demo.mp4"></video>

## Setup

Copy `.env` to `.env.local` and fill out your local env.

I personally use [a mock GCS server](https://github.com/fsouza/fake-gcs-server)

An example `.env.local` is:
```env
OPENAI_API_KEY="sk-proj-..."
GCS_BUCKET_NAME="local"
GCS_CREDENTIALS_JSON="nil"
GCS_EMULATOR_HOST=http://localhost:4443
```

Run the backend
```sh
pip install -r requirements.txt
py main.py
```

Run the frontend
```sh
bun install
bun run dev
```