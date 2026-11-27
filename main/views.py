import datetime

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import reverse
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from django.views import generic

from blog.covers import SOCIAL_SIZE
from blog.models import content_language
from config import structured_data
from config.context_processors import years_of_experience
from config.forms import HONEYPOT_FIELD
from config.throttling import FormThrottle

from . import cases, services
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
        # What clients search for, around the role, which stays as it is (og-profile.png has it too)
        kwargs['full_title'] = _('Nestor Bracho, %(role)s · Freelance Django & Python, %(city)s') % {
            'role': settings.OWNER_ROLE,
            'city': settings.OWNER_CITY,
        }
        kwargs['structured_data'] = structured_data.home(self.request)
        kwargs['social_image_url'] = static(PROFILE_SOCIAL_IMAGE)
        kwargs['social_image_size'] = SOCIAL_SIZE
        kwargs['case_groups'] = cases.grouped_cases()
        kwargs['drafts_visible'] = cases.drafts_visible()
        example = cases.get_case(HOW_I_WORK_EXAMPLE)
        kwargs['how_i_work_example'] = example.localized() if example else None
        # Compared with the latest post the context processor already fetched (latest_posts): no query of its own
        kwargs['blog_shown_since'] = timezone.now() - BLOG_FRESHNESS

        return super().get_context_data(**kwargs)


class CasesView(generic.TemplateView):
    """The cases index: the cases the site shows, grouped as on the home, and the home's contact block."""

    template_name = 'main/cases.html'

    def get_context_data(self, **kwargs):
        groups = cases.grouped_cases()
        kwargs['case_groups'] = groups
        kwargs['drafts_visible'] = cases.drafts_visible()
        kwargs['intro'] = services.CASES_INDEX_INTRO
        kwargs['full_title'] = services.CASES_INDEX_TITLE
        kwargs['meta_description'] = services.CASES_INDEX_DESCRIPTION
        kwargs['structured_data'] = structured_data.cases_page(self.request, groups)

        return super().get_context_data(**kwargs)


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
        # The services whose pages list this case: the way back to what it proves
        kwargs['services'] = services.services_for_case(case.slug)
        kwargs['drafts_visible'] = cases.drafts_visible()
        kwargs['page_title'] = localized.title
        # Until the summary is written (drafts, in development), the site's own description stands in
        if localized.summary:
            kwargs['meta_description'] = localized.summary
        kwargs['og_type'] = 'article'
        kwargs['structured_data'] = structured_data.case_page(self.request, localized)

        return super().get_context_data(**kwargs)


class ServiceDetailView(generic.TemplateView):
    """A service's page (main/services.py, from docs/services-content.md)."""

    template_name = 'main/service.html'

    def get_context_data(self, **kwargs):
        service = services.get_service(self.kwargs['slug'])
        if service is None:
            raise Http404('No such service')
        localized = service.localized()

        kwargs['service'] = localized
        kwargs['blocks'] = numbered_blocks(
            [
                ('points', _('What I do'), localized.points),
                ('examples', _('Examples'), localized.examples),
                ('cases', _('Cases'), localized.cases),
                ('how_i_work', _('How I work'), localized.how_i_work),
                ('faq', _('Frequently asked questions'), localized.faq),
            ]
        )
        kwargs['drafts_visible'] = cases.drafts_visible()
        kwargs['full_title'] = localized.title
        kwargs['meta_description'] = localized.description
        kwargs['structured_data'] = structured_data.service_page(self.request, localized)

        return super().get_context_data(**kwargs)


class HowIWorkView(generic.TemplateView):
    """The method's own page; the home's How I work block summarizes it and links here."""

    template_name = 'main/how_i_work.html'

    def get_context_data(self, **kwargs):
        example = cases.get_case(HOW_I_WORK_EXAMPLE)
        kwargs['example'] = example.localized() if example else None
        faq = services.how_i_work_faq()
        kwargs['faq'] = faq
        kwargs['full_title'] = services.HOW_I_WORK_TITLE
        kwargs['meta_description'] = services.HOW_I_WORK_DESCRIPTION
        kwargs['structured_data'] = structured_data.how_i_work_page(self.request, faq)

        return super().get_context_data(**kwargs)


def numbered_blocks(candidates):
    """
    The labelled blocks of a page, in order, leaving out those it has nothing for: each takes the next number, so
    they run 01, 02... with no gaps. `candidates` is [(kind, label, value)...].
    """
    blocks = []
    for kind, label, value in candidates:
        if value:
            blocks.append({'kind': kind, 'label': label, 'number': f'{len(blocks) + 1:02d}'})
    return blocks


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


class LlmsTxtView(generic.View):
    """
    /llms.txt (llmstxt.org): a Markdown map of the site's key pages for AI systems. At the root, like robots.txt, so
    always in English, with the Spanish home listed beside the English one.
    """

    def get(self, request, *args, **kwargs):
        def url(name):
            return request.build_absolute_uri(reverse(name))

        with translation.override('en'):
            context = {
                'home_url': url('main:index'),
                'about_url': url('main:about'),
                'cv_url': url('main:cv'),
                'blog_url': url('blog:post-list'),
                'role': settings.OWNER_ROLE,
                'years': years_of_experience(),
                'city': settings.OWNER_CITY,
                # Only the published ones, even in development
                'cases': [
                    {'title': case.title, 'summary': case.summary, 'url': request.build_absolute_uri(case.url)}
                    for case in (published.localized() for published in cases.CASES if published.is_published())
                ],
                # Each with its SEO description as its line
                'services': [
                    {
                        'name': service.name,
                        'description': service.description,
                        'url': request.build_absolute_uri(service.url),
                    }
                    for service in (service.localized() for service in services.SERVICES)
                ],
                'how_i_work_url': url('main:how-i-work'),
                'how_i_work_description': services.HOW_I_WORK_DESCRIPTION,
                'cases_url': url('main:cases'),
                'cases_description': services.CASES_INDEX_DESCRIPTION,
            }
            with translation.override('es'):
                context['home_es_url'] = url('main:index')
            content = render_to_string('llms.txt', context, request)
        return HttpResponse(content, content_type='text/plain; charset=utf-8')


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
