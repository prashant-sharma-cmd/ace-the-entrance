# forum/views.py
import json
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from django.db.models import Count
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import Thread, Reply
from .utils import validate_image_upload, compress_image, check_image_upload_rate_limit


class IndexPageView(TemplateView):
    template_name = "discussion/index.html"


# ── Shared helper ──────────────────────────────────────────────────────────────

def _process_image(request, field_name: str = "image"):
    """
    Validate, rate-limit and compress an uploaded image from the request.

    Returns:
        (ContentFile | None, JsonResponse | None)
        On success  → (compressed_file_or_None, None)
        On failure  → (None, error_JsonResponse)

    Errors are added to Django's messages framework AND returned as a
    JSON detail so both server-rendered pages and the JS frontend
    surface a readable message.
    """
    from django.contrib import messages

    raw = request.FILES.get(field_name)
    if raw is None:
        return None, None  # no image uploaded — that's fine

    # 1. Validate type and size
    err = validate_image_upload(raw)
    if err:
        messages.error(request, err)
        return None, JsonResponse({"detail": err}, status=400)

    # 2. Rate-limit per user
    err = check_image_upload_rate_limit(request.user)
    if err:
        messages.error(request, err)
        return None, JsonResponse({"detail": err}, status=429)

    # 3. Compress / resize
    compressed = compress_image(raw, raw.name)
    return compressed, None


# ── Views ──────────────────────────────────────────────────────────────────────

class ThreadListView(View):
    """GET  /forum/api/threads/   — list threads
       POST /forum/api/threads/   — create thread (auth required)
    """

    def get(self, request):
        qs = Thread.objects.select_related("author").annotate(reply_count=Count("replies"))

        category = request.GET.get("category")
        if category:
            qs = qs.filter(category=category)

        sort = request.GET.get("sort", "recent")
        if sort == "popular":
            qs = qs.order_by("-likes", "-created_at")
        else:
            qs = qs.order_by("-created_at")

        data = [thread_to_dict(t) for t in qs]
        return JsonResponse(data, safe=False)

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)

        title    = request.POST.get("title", "").strip()
        body     = request.POST.get("body", "").strip()
        category = request.POST.get("category", "General")

        if not title or not body:
            return JsonResponse({"detail": "Title and body are required."}, status=400)

        image, err = _process_image(request)
        if err:
            return err

        thread = Thread.objects.create(
            title=title, body=body, category=category,
            author=request.user, image=image,
        )
        return JsonResponse(thread_to_dict(thread), status=201)


class ReplyListView(View):
    """GET  /forum/api/threads/<pk>/replies/
       POST /forum/api/threads/<pk>/replies/
    """

    def get(self, request, pk):
        replies = Reply.objects.filter(thread_id=pk).select_related("author")
        return JsonResponse([reply_to_dict(r) for r in replies], safe=False)

    def post(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)

        try:
            thread = Thread.objects.get(pk=pk)
        except Thread.DoesNotExist:
            return JsonResponse({"detail": "Thread not found."}, status=404)

        body = request.POST.get("body", "").strip()
        if not body:
            return JsonResponse({"detail": "Body is required."}, status=400)

        image, err = _process_image(request)
        if err:
            return err

        reply = Reply.objects.create(
            thread=thread, body=body,
            author=request.user, image=image,
        )
        return JsonResponse(reply_to_dict(reply), status=201)


class ThreadLikeView(View):
    """POST /forum/api/threads/<pk>/like/"""

    def post(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)
        try:
            thread = Thread.objects.get(pk=pk)
        except Thread.DoesNotExist:
            return JsonResponse({"detail": "Not found."}, status=404)

        Thread.objects.filter(pk=pk).update(likes=thread.likes + 1)
        thread.refresh_from_db()
        return JsonResponse({"likes": thread.likes})


class ReplyLikeView(View):
    """POST /forum/api/replies/<pk>/like/"""

    def post(self, request, pk):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required."}, status=401)
        try:
            reply = Reply.objects.get(pk=pk)
        except Reply.DoesNotExist:
            return JsonResponse({"detail": "Not found."}, status=404)

        Reply.objects.filter(pk=pk).update(likes=reply.likes + 1)
        reply.refresh_from_db()
        return JsonResponse({"likes": reply.likes})


class ThreadDetailEditView(View):
    """
    GET    /forum/api/threads/<pk>/  — fetch single thread
    PATCH  /forum/api/threads/<pk>/  — update title/body/category (owner only)
    DELETE /forum/api/threads/<pk>/  — delete thread (owner only)
    """

    def get(self, request, pk):
        try:
            thread = Thread.objects.select_related("author").get(pk=pk)
        except Thread.DoesNotExist:
            return JsonResponse({"detail": "Not found."}, status=404)
        return JsonResponse(thread_to_dict(thread))

    def _get_thread_for_owner(self, request, pk):
        if not request.user.is_authenticated:
            return None, JsonResponse({"detail": "Authentication required."}, status=401)
        try:
            thread = Thread.objects.get(pk=pk)
        except Thread.DoesNotExist:
            return None, JsonResponse({"detail": "Thread not found."}, status=404)
        if thread.author != request.user and not request.user.is_superuser:
            return None, JsonResponse({"detail": "You do not have permission to modify this thread."}, status=403)
        return thread, None

    def patch(self, request, pk):
        thread, err = self._get_thread_for_owner(request, pk)
        if err:
            return err

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON."}, status=400)

        if "title" in payload:
            title = payload["title"].strip()
            if not title:
                return JsonResponse({"detail": "Title cannot be empty."}, status=400)
            thread.title = title

        if "body" in payload:
            body = payload["body"].strip()
            if not body:
                return JsonResponse({"detail": "Body cannot be empty."}, status=400)
            thread.body = body

        if "category" in payload:
            thread.category = payload["category"]

        thread.save()
        return JsonResponse(thread_to_dict(thread))

    def delete(self, request, pk):
        thread, err = self._get_thread_for_owner(request, pk)
        if err:
            return err
        thread.delete()
        return JsonResponse({}, status=204)


class ReplyDetailEditView(View):
    """
    PATCH  /forum/api/replies/<pk>/  — update body (owner only)
    DELETE /forum/api/replies/<pk>/  — delete reply (owner only)
    """

    def _get_reply_for_owner(self, request, pk):
        if not request.user.is_authenticated:
            return None, JsonResponse({"detail": "Authentication required."}, status=401)
        try:
            reply = Reply.objects.get(pk=pk)
        except Reply.DoesNotExist:
            return None, JsonResponse({"detail": "Reply not found."}, status=404)
        if reply.author != request.user and not request.user.is_superuser:
            return None, JsonResponse({"detail": "You do not have permission to modify this reply."}, status=403)
        return reply, None

    def patch(self, request, pk):
        reply, err = self._get_reply_for_owner(request, pk)
        if err:
            return err

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON."}, status=400)

        if "body" in payload:
            body = payload["body"].strip()
            if not body:
                return JsonResponse({"detail": "Body cannot be empty."}, status=400)
            reply.body = body

        reply.save()
        return JsonResponse(reply_to_dict(reply))

    def delete(self, request, pk):
        reply, err = self._get_reply_for_owner(request, pk)
        if err:
            return err
        reply.delete()
        return JsonResponse({}, status=204)


# ── Serialisation helpers ──────────────────────────────────────────────────────

def thread_to_dict(thread):
    return {
        "id":              thread.id,
        "title":           thread.title,
        "body":            thread.body,
        "category":        thread.category,
        "author_username": thread.author.username,
        "author_id":       thread.author.id,
        "likes":           thread.likes,
        "image_url":       thread.image.url if thread.image else None,
        "reply_count":     getattr(thread, "reply_count", thread.replies.count()),
        "created_at":      thread.created_at.isoformat(),
    }


def reply_to_dict(reply):
    return {
        "id":              reply.id,
        "body":            reply.body,
        "author_username": reply.author.username,
        "author_id":       reply.author.id,
        "image_url":       reply.image.url if reply.image else None,
        "likes":           reply.likes,
        "created_at":      reply.created_at.isoformat(),
    }