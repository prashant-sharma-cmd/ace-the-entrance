from django.shortcuts import render

def index_view(request):
    template_name = 'tos/index.html'

    return render(request, 'index.html')