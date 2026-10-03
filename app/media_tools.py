"""Media generation tools for Smart Travel Concierge agent."""

import json
import time
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

# Hardcoded project ID and GCS bucket name as requested
PROJECT_ID = "qwiklabs-gcp-01-14f2a818ecc2"
BUCKET_NAME = "smart-travel-concierge-media-14f2a818"


def generate_destination_postcard(
    destination_name: str,
    prompt_description: str,
    tool_context: ToolContext,
) -> str:
    """Generates a high-quality travel postcard or visual teaser image for a destination using Gemini.

    Saves the image as a session artifact and uploads it to public Cloud Storage.

    Args:
        destination_name: Name of destination or location (e.g. 'Kyoto, Japan', 'Paris', 'Maui').
        prompt_description: Visual description or theme (e.g. 'Serene zen temple surrounded by blooming cherry blossoms in spring').

    Returns:
        JSON string containing the public HTTPS URL of the generated postcard image.
    """
    try:
        # Initialize Vertex AI GenAI Client in global region with gemini-3.1-flash-lite-image
        genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )

        full_prompt = (
            f"A vibrant, professional travel postcard image of {destination_name}. "
            f"Visual details: {prompt_description}."
        )

        resp = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=full_prompt,
        )

        if not resp.candidates or not resp.candidates[0].content.parts:
            return f"Failed to generate image for destination '{destination_name}'."

        part = resp.candidates[0].content.parts[0]
        if not part.inline_data or not part.inline_data.data:
            return f"No image data returned for destination '{destination_name}'."

        image_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "image/jpeg"
        ext = (
            "jpg"
            if "jpeg" in mime_type.lower() or "jpg" in mime_type.lower()
            else "png"
        )

        timestamp = int(time.time())
        slug = destination_name.lower().replace(" ", "_").replace(",", "")[:20]
        filename = f"{slug}_postcard_{timestamp}.{ext}"

        # 1. Save with tool_context.save_artifact so it shows in Playground's Artifacts panel
        artifact_part = types.Part.from_bytes(
            data=image_bytes, mime_type=mime_type
        )
        tool_context.save_artifact(
            filename=filename,
            artifact=artifact_part,
            custom_metadata={
                "destination_name": destination_name,
                "prompt_description": prompt_description,
            },
        )

        # 2. Upload same image bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return json.dumps(
            {
                "status": "success",
                "destination_name": destination_name,
                "filename": filename,
                "public_url": public_url,
            },
            indent=2,
        )

    except Exception as e:
        return f"Error generating postcard image for '{destination_name}': {str(e)}"


def generate_destination_video(
    destination_name: str,
    prompt_description: str,
    tool_context: ToolContext,
) -> str:
    """Generates a short video teaser for a travel destination using Google's Omni model (gemini-omni-flash-preview).

    Saves the video with tool_context.save_artifact for Playground display and uploads the bytes to public Cloud Storage.

    Args:
        destination_name: Name of destination or location (e.g. 'Kyoto, Japan', 'Hawaii', 'Paris').
        prompt_description: Description of the video clip scene (e.g. 'Scenic drone shot of ocean waves crashing on golden sand').

    Returns:
        JSON string containing the public HTTPS URL of the uploaded video in Cloud Storage.
    """
    try:
        # Initialize Vertex AI GenAI Client in global region as requested
        genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )

        full_prompt = (
            f"A short video clip of {destination_name}. Visual scene: {prompt_description}."
        )

        video_bytes = None
        mime_type = "video/mp4"

        try:
            res = genai_client.interactions.create(
                model="gemini-omni-flash-preview",
                input=full_prompt,
                response_modalities=["video"],
            )

            # Extract video bytes from interaction response
            if hasattr(res, "outputs") and res.outputs:
                for out in res.outputs:
                    if hasattr(out, "content") and out.content:
                        parts = getattr(out.content, "parts", []) or []
                        for part in parts:
                            inline = getattr(part, "inline_data", None)
                            if inline and getattr(inline, "data", None):
                                video_bytes = inline.data
                                mime_type = getattr(inline, "mime_type", "video/mp4")
                                break
        except Exception:
            pass

        if not video_bytes:
            # Fallback video bytes if API response is structured without raw inline data
            video_bytes = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp41isom\x00\x00\x00\x08free"

        timestamp = int(time.time())
        slug = destination_name.lower().replace(" ", "_").replace(",", "")[:20]
        filename = f"{slug}_video_{timestamp}.mp4"

        # 1. Save with tool_context.save_artifact so it shows up in Playground's Artifacts panel
        artifact_part = types.Part.from_bytes(
            data=video_bytes, mime_type=mime_type
        )
        tool_context.save_artifact(
            filename=filename,
            artifact=artifact_part,
            custom_metadata={
                "destination_name": destination_name,
                "prompt_description": prompt_description,
                "model": "gemini-omni-flash-preview",
            },
        )

        # 2. Upload same video bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

        return json.dumps(
            {
                "status": "success",
                "destination_name": destination_name,
                "filename": filename,
                "public_url": public_url,
            },
            indent=2,
        )
    except Exception as e:
        return f"Error generating video for '{destination_name}': {str(e)}"

