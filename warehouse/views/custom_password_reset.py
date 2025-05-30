from django.contrib.auth.views import PasswordResetView
from django.contrib.sites.models import Site

class CustomPasswordResetView(PasswordResetView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = Site.objects.get_current()
        context['domain'] = site.domain
        context['protocol'] = 'http'  # Change to 'https' if you use SSL
        return context

    def form_valid(self, form):
        site = Site.objects.get_current()
        return form.save(
            domain_override=site.domain,
            use_https=self.request.is_secure(),
            from_email=self.from_email,
            email_template_name=self.email_template_name,
            subject_template_name=self.subject_template_name,
            request=self.request,
        ) or super().form_valid(form)
