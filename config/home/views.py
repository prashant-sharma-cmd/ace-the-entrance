from django.shortcuts import render
from django.views.generic import TemplateView

class HomePageView(TemplateView):
    template_name = 'home/index.html'

# class SignUpView(TemplateView):
#     pass
