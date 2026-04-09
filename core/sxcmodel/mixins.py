from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpRequest


class MyLoginRequiredMixin(LoginRequiredMixin):
    request : HttpRequest
    auth_message = "Please login in to access the page!"

    def handle_no_permission(self):
        messages.info(self.request, self.auth_message)
        return super().handle_no_permission()
