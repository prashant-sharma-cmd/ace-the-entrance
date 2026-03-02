from allauth.core.internal.httpkit import redirect
from django.shortcuts import render
from rest_framework.reverse import reverse_lazy


def index_view(request):
    template_name = 'about/index.html'

    return render(request, template_name)

def contact_view(request):
    url_path = reverse_lazy('home:index')
    target_url = url_path + "#contact"

    return redirect(target_url)