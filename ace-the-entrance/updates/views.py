from django.shortcuts import render
from .models import Update


def updates_page(request):
    active_tab = request.GET.get('tab', 'entrance')

    entrance_updates = Update.objects.filter(
        category='entrance', is_published=True
    ).order_by('-created_at')

    changelog_updates = Update.objects.filter(
        category='changelog', is_published=True
    ).order_by('-created_at')

    context = {
        'entrance_updates': entrance_updates,
        'changelog_updates': changelog_updates,
        'active_tab': active_tab,
        'entrance_count': entrance_updates.count(),
        'changelog_count': changelog_updates.count(),
    }
    return render(request, 'updates/updates.html', context)