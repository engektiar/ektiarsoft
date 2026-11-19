"""AI text extraction (OCR) with Claude vision, used by the "AI Mode" of /image-to-text/.

The image is sent to the Claude API, the transcription is returned to the browser,
and nothing (neither the image nor the text) is stored by this site.

Settings / environment:
    ANTHROPIC_API_KEY   required to enable AI mode (Vercel -> Settings -> Environment Variables)
    OCR_AI_MODEL        default "claude-opus-5-5"
    OCR_AI_DAILY_LIMIT  AI extractions per user per day, default 30
"""
import base64
import logging
import os

log = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_BYTES = 4 * 1024 * 1024  # stays below Vercel's 4.5 MB request limit

PROMPT = (
    "Transcribe ALL text in this image exactly as written. It may be a photo of a form or document "
    "in Bangla and/or English.\n"
    "Rules:\n"
    "- Keep every word, number, date and code exactly as printed; keep Bangla in Bangla script.\n"
    "- Keep the reading order. Reproduce tables as Markdown tables (label | value), one row per line.\n"
    "- Keep section headings on their own lines.\n"
    "- If a character is unreadable write [?]. Do not guess, translate, summarise or add commentary.\n"
    "- Output only the transcription."
)


class OcrError(Exception):
    """Error with a message that is safe to show to the user."""


def ai_enabled():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def model_name():
    return os.environ.get("OCR_AI_MODEL", "claude-opus-5-5")


def daily_limit():
    try:
        return max(0, int(os.environ.get("OCR_AI_DAILY_LIMIT", "30")))
    except ValueError:
        return 30


def transcribe_image(data: bytes, media_type: str) -> str:
    """Return the text in the image. Raises OcrError with a user-facing message."""
    import anthropic

    if media_type not in ALLOWED_TYPES:
        raise OcrError("Please use a JPG, PNG, WebP or GIF image.")
    if not data or len(data) > MAX_BYTES:
        raise OcrError("The image is too large. Please use a smaller image (max 4 MB).")
    if not ai_enabled():
        raise OcrError("AI mode is not set up yet.")

    client = anthropic.Anthropic(timeout=120.0, max_retries=1)
    try:
        response = client.beta.messages.create(
            model=model_name(),
            max_tokens=16000,
            output_config={"effort": "low"},  # transcription needs little reasoning; keeps it fast
            # if the model declines, the API re-runs the request on a fallback model in the same call
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type,
                                                 "data": base64.standard_b64encode(data).decode("ascii")}},
                    {"type": "text", "text": PROMPT},
                ],
            }],
        )
    except anthropic.AuthenticationError:
        log.error("OCR: invalid ANTHROPIC_API_KEY")
        raise OcrError("AI mode is misconfigured (invalid API key). Please contact the site owner.")
    except anthropic.PermissionDeniedError:
        log.error("OCR: API key lacks permission / no credit")
        raise OcrError("AI mode is temporarily unavailable. Please try again later.")
    except anthropic.RateLimitError:
        raise OcrError("AI mode is busy right now. Please try again in a minute.")
    except anthropic.BadRequestError as e:
        log.warning("OCR: bad request %s", getattr(e, "message", e))
        raise OcrError("This image could not be processed. Try a different image.")
    except anthropic.APITimeoutError:
        raise OcrError("The AI took too long. Please try again with a smaller image.")
    except anthropic.APIStatusError as e:
        log.error("OCR: API error %s", e.status_code)
        raise OcrError("AI mode is temporarily unavailable. Please try again later.")
    except anthropic.APIConnectionError:
        raise OcrError("Could not reach the AI service. Please try again.")

    if response.stop_reason == "refusal":
        raise OcrError("The AI declined to read this image.")
    text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text").strip()
    if response.stop_reason == "max_tokens":
        text += "\n\n[…the text was cut off because it is very long]"
    if not text:
        raise OcrError("No text was found in this image.")
    return text
