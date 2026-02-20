# forum/views.py
import json
from django.http             import JsonResponse
from django.views            import View
from django.views.generic    import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import Thread, Reply


class IndexPageView(TemplateView):
    template_name = "discussion/index.html"


class ThreadListView(View):
    """GET  /forum/api/threads/   — list threads
       POST /forum/api/threads/   — create thread (auth required)
    """

    def get(self, request):
        qs = Thread.objects.select_related("author").annotate_reply_count()

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

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON."}, status=400)

        title    = payload.get("title", "").strip()
        body     = payload.get("body", "").strip()
        category = payload.get("category", "General")

        if not title or not body:
            return JsonResponse({"detail": "Title and body are required."}, status=400)

        thread = Thread.objects.create(
            title=title, body=body, category=category, author=request.user,
            image=request.FILES.get("image")
        )
        return JsonResponse(thread_to_dict(thread), status=201)


class ThreadDetailView(View):
    """GET /forum/api/threads/<pk>/"""

    def get(self, request, pk):
        try:
            thread = Thread.objects.select_related("author").get(pk=pk)
        except Thread.DoesNotExist:
            return JsonResponse({"detail": "Not found."}, status=404)
        return JsonResponse(thread_to_dict(thread))


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

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"detail": "Invalid JSON."}, status=400)

        body = payload.get("body", "").strip()
        if not body:
            return JsonResponse({"detail": "Body is required."}, status=400)

        reply = Reply.objects.create(thread=thread, body=body, author=request.user,
                                     image=request.FILES.get("image"))
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


# ── Serialisation helpers ──────────────────────────────────────────
def thread_to_dict(thread):
    return {
        "id":              thread.id,
        "title":           thread.title,
        "body":            thread.body,
        "category":        thread.category,
        "author_username": thread.author.username,
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
        "image_url":       reply.image.url if reply.image else None,
        "likes":           reply.likes,
        "created_at":      reply.created_at.isoformat(),
    }