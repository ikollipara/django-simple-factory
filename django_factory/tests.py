from django.test import TestCase

from django_factory.factories import Factory
from posts import factories, models

# Create your tests here.


class TestFactory(TestCase):

    def test_get_factory(self):
        post_factory = Factory.get_factory("posts.PostFactory")
        self.assertEqual(post_factory, factories.PostFactory)

    def test_factory_make_returns_instance(self):
        post_factory = factories.PostFactory()
        post = post_factory.make()
        self.assertIsNotNone(post)
        self.assertIsInstance(post, post_factory.model)

    def test_factory_create_returns_instance(self):
        post_factory = factories.PostFactory()
        post = post_factory.create()
        self.assertIsNotNone(post)
        self.assertIsInstance(post, post_factory.model)
        self.assertIsNotNone(post.pk)

    def test_factory_make_batch_returns_list(self):
        post_factory = factories.PostFactory()
        posts = post_factory.make_batch(3)
        self.assertIsNotNone(posts)
        self.assertIsInstance(posts, list)
        self.assertEqual(len(posts), 3)

    def test_factory_create_batch_returns_list(self):
        post_factory = factories.PostFactory()
        posts = post_factory.create_batch(3)
        self.assertIsNotNone(posts)
        self.assertIsInstance(posts, list)
        self.assertEqual(len(posts), 3)
        for post in posts:
            self.assertIsNotNone(post.pk)

    def test_factory_handles_related_field(self):
        comment_factory = factories.CommentFactory()
        comment = comment_factory.create()
        self.assertIsNotNone(comment)
        self.assertIsNotNone(comment.pk)
        self.assertEqual(models.Post.objects.count(), 1)

    def test_factory_handles_related_field_string(self):
        comment_factory = factories.CommentFactory2()
        comment = comment_factory.create()
        self.assertIsNotNone(comment)
        self.assertIsNotNone(comment.pk)
        self.assertEqual(models.Post.objects.count(), 1)

    def test_factory_make_handles_override(self):
        post_factory = factories.PostFactory()
        post = post_factory.make(title="Test Title")
        self.assertIsNotNone(post)
        self.assertEqual(post.title, "Test Title")