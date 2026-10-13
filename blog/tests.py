from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Category, Post


# Data migrations already seed real categories, so tests use their own slugs
def create_category(slug='test-topic', **kwargs):
    fields = {'name_es': slug, 'name_en': slug, 'slug': slug, 'color': '#ae00ee', **kwargs}
    return Category.objects.create(**fields)


def create_post(title, days_ago=0, **kwargs):
    fields = {
        'title_es': title,
        'title_en': title,
        'body_es': 'Cuerpo',
        'body_en': 'Body',
        'description_es': 'Descripción',
        'description_en': 'Description',
        'is_published': True,
        **kwargs,
    }
    post = Post.objects.create(**fields)
    # `created` is auto_now_add, so it can only be moved after the insert
    Post.objects.filter(pk=post.pk).update(created=timezone.now() - timedelta(days=days_ago))
    post.refresh_from_db()
    return post


class PostDetailViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.category = create_category()
        cls.older = create_post('Older', days_ago=4, category=cls.category)
        cls.draft = create_post('Draft', days_ago=3, category=cls.category, is_published=False)
        cls.post = create_post('Current', days_ago=2, category=cls.category)
        cls.newer = create_post('Newer', days_ago=1, category=create_category('other-topic'))

    def get(self, post):
        return self.client.get(post.get_absolute_url())

    def test_renders_published_post(self):
        response = self.get(self.post)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.get_absolute_url())

    def test_post_without_category_renders(self):
        post = create_post('No category', category=None)

        response = self.get(post)

        self.assertEqual(response.status_code, 200)

    def test_unpublished_post_is_not_found(self):
        response = self.get(self.draft)

        self.assertEqual(response.status_code, 404)

    def test_social_image_is_an_absolute_url(self):
        response = self.get(self.post)

        self.assertContains(response, '<meta property="og:image" content="http://testserver/static/')


class CategoryDetailViewTests(TestCase):

    def test_post_cards_link_to_the_category_slug(self):
        category = create_category()
        create_post('Post', category=category)

        response = self.client.get(category.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{category.get_absolute_url()}"')
        self.assertNotContains(response, str(category.pk))

    def test_unknown_category_is_not_found(self):
        response = self.client.get(reverse('blog:category-detail', kwargs={'slug': 'missing'}))

        self.assertEqual(response.status_code, 404)


class CategoryDeletionTests(TestCase):

    def test_deleting_a_category_keeps_its_posts(self):
        category = create_category()
        post = create_post('Post', category=category)

        category.delete()

        post.refresh_from_db()
        self.assertIsNone(post.category)


class FeedTests(TestCase):

    def test_feed_lists_published_posts_only(self):
        create_post('Published post')
        create_post('Draft post', is_published=False)

        response = self.client.get(reverse('blog:feed'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('application/rss+xml', response['Content-Type'])
        self.assertContains(response, 'Published post')
        self.assertNotContains(response, 'Draft post')


class SitemapTests(TestCase):

    def test_sitemap_lists_pages_and_published_content(self):
        published = create_post('Published', category=create_category('other-topic'))
        draft = create_post('Draft', is_published=False, category=create_category('drafts-only'))

        response = self.client.get(reverse('sitemap'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'<loc>http://testserver{reverse("main:about")}</loc>')
        self.assertContains(response, f'<loc>http://testserver{published.get_absolute_url()}</loc>')
        self.assertContains(response, f'<loc>http://testserver{published.category.get_absolute_url()}</loc>')
        self.assertNotContains(response, draft.get_absolute_url())
        self.assertNotContains(response, draft.category.get_absolute_url())
