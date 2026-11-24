import datetime

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import generic

from blog.covers import SOCIAL_SIZE
from blog.models import content_language
from config import structured_data
from config.context_processors import years_of_experience
from config.forms import HONEYPOT_FIELD
from config.throttling import FormThrottle

from . import cases
from .forms import ContactForm
from .models import ContactRequest

# Link previews of the pages recruiters land on show his name and role (brand/source/gen.py makes it from OWNER_ROLE);
# the rest keep the brand image
PROFILE_SOCIAL_IMAGE = 'images/og-profile.png'

# The case the home's "How I work" links to, as a real example of it
HOW_I_WORK_EXAMPLE = 'mid-term-rental-crm'

# The home's "From the blog" waits for a post newer than this: a year-old latest post makes the site look abandoned
BLOG_FRESHNESS = datetime.timedelta(days=365)


class IndexView(generic.TemplateView):
    template_name = 'main/index.html'

    def get(self, request, *args, **kwargs):
        # The home used to list the posts a page at a time; those pages are the blog's now
        if 'page' in request.GET:
            return HttpResponsePermanentRedirect(f'{reverse("blog:post-list")}?{request.GET.urlencode()}')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs['structured_data'] = structured_data.home_page(self.request)
        kwargs['social_image_url'] = static(PROFILE_SOCIAL_IMAGE)
        kwargs['social_image_size'] = SOCIAL_SIZE
        kwargs['case_groups'] = cases.grouped_cases()
        kwargs['drafts_visible'] = cases.drafts_visible()
        example = cases.get_case(HOW_I_WORK_EXAMPLE)
        kwargs['how_i_work_example'] = example.localized() if example else None
        # Compared with the latest post the context processor already fetched (latest_posts): no query of its own
        kwargs['blog_shown_since'] = timezone.now() - BLOG_FRESHNESS

        return super().get_context_data(**kwargs)


class CasesView(generic.RedirectView):
    """
    There is no cases page: the home's section lists them. Temporary, so browsers don't cache it in case one is made.
    """

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return f'{reverse("main:index")}#cases'


class CaseDetailView(generic.TemplateView):
    template_name = 'main/case.html'

    def get_context_data(self, **kwargs):
        case = cases.get_case(self.kwargs['slug'])
        if case is None:
            raise Http404('No such case')
        localized = case.localized()

        kwargs['case'] = localized
        kwargs['blocks'] = case_blocks(localized)
        kwargs['next_case'] = cases.next_case(case).localized()
        kwargs['drafts_visible'] = cases.drafts_visible()
        kwargs['page_title'] = localized.title
        # Until the summary is written (drafts, in development), the site's own description stands in
        if localized.summary:
            kwargs['meta_description'] = localized.summary
        kwargs['og_type'] = 'article'
        kwargs['structured_data'] = structured_data.case_study(self.request, localized)

        return super().get_context_data(**kwargs)


def case_blocks(case):
    """
    The blocks of a case's page, in order, leaving out those the case has nothing for. Each labelled block takes the
    next number, so they run 01, 02... with no gaps; the screenshot has neither label nor number.
    """
    candidates = [
        ('problem', _('The problem'), case.problem),
        ('solution', _('What I built'), case.solution),
        ('screenshot', None, case.screenshot),
        ('how_built', _('How it was built'), case.how_built),
        ('stack', _('Stack'), case.stack),
        ('result', _('Result'), case.result),
        ('links', _('Links'), case.links),
    ]
    blocks = []
    number = 0
    for kind, label, value in candidates:
        if not value:
            continue
        if label:
            number += 1
        blocks.append({'kind': kind, 'label': label, 'number': f'{number:02d}' if label else None})
    return blocks


class AboutView(generic.TemplateView):
    template_name = 'main/about.html'

    def get_context_data(self, **kwargs):

        kwargs['page_title'] = _('About Me')
        kwargs['meta_description'] = _(
            'Get to know Nestor Bracho, %(role)s: backend systems, Python and technology for social impact. '
            'His journey, skills and what drives him.'
        ) % {'role': settings.OWNER_ROLE}

        return super().get_context_data(**kwargs)


class CVView(generic.TemplateView):
    template_name = 'main/cv.html'

    def get_context_data(self, **kwargs):
        # The role in the title too: it's what search results and link previews show first
        kwargs['full_title'] = _('CV · Nestor Bracho, %(role)s') % {'role': settings.OWNER_ROLE}
        kwargs['meta_description'] = _(
            'CV of Nestor Bracho, %(role)s with more than %(years)s years building web platforms with Python and '
            'Django.'
        ) % {'role': settings.OWNER_ROLE, 'years': years_of_experience()}
        kwargs['social_image_url'] = static(PROFILE_SOCIAL_IMAGE)
        kwargs['social_image_size'] = SOCIAL_SIZE
        kwargs['pdf_url'] = settings.OWNER_CV_PDF_URLS[content_language()]
        kwargs['structured_data'] = structured_data.profile_page(self.request)

        return super().get_context_data(**kwargs)


class PrivacyView(generic.TemplateView):
    template_name = 'main/privacy.html'

    def get_context_data(self, **kwargs):
        kwargs['page_title'] = _('Privacy policy')
        kwargs['meta_description'] = _('What personal data this site collects, why, and how to exercise your rights.')

        return super().get_context_data(**kwargs)


class ContactFormView(generic.CreateView):
    template_name = 'main/contact.html'
    form_class = ContactForm
    model = ContactRequest

    def get_context_data(self, **kwargs):

        kwargs['page_title'] = _('Contact')
        kwargs['meta_description'] = _(
            'Plug into the grid, whether you’re building something bold or need a '
            'sharp mind in the system, this is your uplink to start working together.'
        )

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        if not FormThrottle('contact').allow_request(self.request, self):
            # The form comes back with what they wrote, to send it again later
            form.add_error(
                None,
                _("You've sent several messages in a short time. Please try again later: your message is still here."),
            )
            return self.render_to_response(self.get_context_data(form=form), status=429)

        http_response = super().form_valid(form)
        messages.success(
            self.request,
            _("Your contact request has been successfully submitted. I'll get in touch as soon as possible!"),
        )
        return http_response

    def form_invalid(self, form):
        if form.has_error(HONEYPOT_FIELD):
            # Only bots fill in the hidden field: drop the request without telling them which field gave them away
            messages.error(self.request, _('Something went wrong. Try again later.'))
            return HttpResponseRedirect(self.get_success_url())
        # People get the form back with their text and an error next to each field to fix
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('main:index')
