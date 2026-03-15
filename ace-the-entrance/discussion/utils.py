# forum/utils.py
import io
from PIL import Image
from django.core.files.base import ContentFile
from django.core.cache import cache
from django.http import JsonResponse


# ── Constants ─────────────────────────────────────────────────────────────────

MAX_IMAGE_SIZE_BYTES  = 3 * 1024 * 1024          # 3 MB  (upload limit)
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS    = {".jpg", ".jpeg", ".png", ".webp"}

# Compression targets
COMPRESS_MAX_DIMENSION = 1024          # longest edge capped at 1024 px
COMPRESS_WEBP_QUALITY  = 65            # starting quality for WebP
COMPRESS_TARGET_BYTES  = 100 * 1024    # target <= 100 KB; bottoms out at quality 20

# Rate-limiting
IMAGE_UPLOAD_RATE_LIMIT  = 10          # max uploads per window
IMAGE_UPLOAD_WINDOW_SECS = 60 * 60    # 1 hour


# ── Validation ────────────────────────────────────────────────────────────────

def validate_image_upload(file) -> str | None:
    """
    Validate an uploaded file object.
    Returns an error message string on failure, or None on success.
    """
    import os

    if file is None:
        return None  # no file is fine; field is optional

    # 1. File size
    if file.size > MAX_IMAGE_SIZE_BYTES:
        mb = file.size / (1024 * 1024)
        return f"File too large ({mb:.1f} MB). Maximum allowed size is 3 MB."

    # 2. MIME type reported by the browser (easy spoof, but catches accidents)
    content_type = getattr(file, "content_type", "").lower()
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        return f"Unsupported file type '{content_type}'. Only JPEG, PNG and WebP are allowed."

    # 3. File extension
    _, ext = os.path.splitext(file.name.lower())
    if ext not in ALLOWED_EXTENSIONS:
        return f"Unsupported file extension '{ext}'. Only .jpg, .jpeg, .png, .webp are allowed."

    # 4. Actually try to open it with Pillow — catches disguised non-images
    try:
        file.seek(0)
        img = Image.open(file)
        img.verify()          # raises if not a valid image
        file.seek(0)          # reset after verify()
    except Exception:
        return "The uploaded file is not a valid image or is corrupted."

    return None               # all good


# ── Compression ───────────────────────────────────────────────────────────────

def compress_image(file, filename: str) -> ContentFile:
    """
    Compress and resize an uploaded image in-memory.
    Returns a Django ContentFile ready to be saved.

    Strategy
    --------
    • Resize so the longest edge <= 1024 px (preserves aspect ratio).
    • Convert to WebP — better compression than JPEG/PNG, widely supported.
    • Transparent images (PNG with alpha) are saved as RGBA WebP.
    • Adaptive quality loop: 65 -> 50 -> 35 -> 20 until <= 100 KB.
    """
    import os

    file.seek(0)
    img = Image.open(file)

    # Ensure we have pixel data (not just header)
    img.load()

    # ── Resize ────────────────────────────────────────────────────────────────
    w, h = img.size
    max_dim = COMPRESS_MAX_DIMENSION
    if max(w, h) > max_dim:
        ratio = max_dim / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    # ── Convert to WebP (best size/quality ratio, no GIF to worry about) ─────
    has_alpha = img.mode in ("RGBA", "LA", "PA") or (
        img.mode == "P" and "transparency" in img.info
    )
    img = img.convert("RGBA" if has_alpha else "RGB")

    # ── Adaptive quality loop — drop quality until under target ──────────────
    # Steps: 65 → 50 → 35 → 20  (4 attempts, bottoms out at 20)
    quality = COMPRESS_WEBP_QUALITY
    buf = io.BytesIO()

    for _ in range(4):
        buf.seek(0)
        buf.truncate()
        img.save(buf, format="WEBP", quality=quality, method=6)
        if buf.tell() <= COMPRESS_TARGET_BYTES or quality <= 20:
            break
        quality -= 15

    buf.seek(0)
    base = os.path.splitext(filename)[0]
    new_filename = base + ".webp"
    return ContentFile(buf.read(), name=new_filename)


# ── Rate limiting ─────────────────────────────────────────────────────────────

def _rate_limit_key(user_id: int) -> str:
    return f"forum:img_upload:{user_id}"


def check_image_upload_rate_limit(user) -> str | None:
    """
    Check whether the user has exceeded the image upload rate limit.
    Increments the counter on each call.
    Returns an error message if the limit is exceeded, else None.
    """
    if not user or not user.is_authenticated:
        return None  # validation handled elsewhere

    key   = _rate_limit_key(user.id)
    count = cache.get(key, 0)

    if count >= IMAGE_UPLOAD_RATE_LIMIT:
        return (
            f"You have uploaded too many images. "
            f"Please wait before uploading again "
            f"(limit: {IMAGE_UPLOAD_RATE_LIMIT} images per hour)."
        )

    # Increment; set TTL only on first write so the window doesn't slide
    if count == 0:
        cache.set(key, 1, timeout=IMAGE_UPLOAD_WINDOW_SECS)
    else:
        cache.incr(key)

    return None


def check_post_rate_limit(user, action: str = "post") -> str | None:
    """
    Prevent post spam. Limits per user per hour:
      - thread : 10 new threads
      - reply  : 30 new replies
    Returns an error message if exceeded, else None.
    """
    limits = {"thread": 10, "reply": 30}
    limit = limits.get(action, 10)

    key   = f"forum:post_rate:{action}:{user.id}"
    count = cache.get(key, 0)

    if count >= limit:
        return (
            f"You are posting too fast. "
            f"Please wait before submitting another {action} "
            f"(limit: {limit} per hour)."
        )

    if count == 0:
        cache.set(key, 1, timeout=IMAGE_UPLOAD_WINDOW_SECS)
    else:
        cache.incr(key)

    return None