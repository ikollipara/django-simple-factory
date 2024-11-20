from django.test import TestCase

from django_simple_factory.factories import Factory
from django_simple_factory.mixins import FactoryTestMixin
from posts import factories, models

# Create your tests here.


class TestFactory(TestCase):
    def test_factory_must_be_implemented(self):
        with self.assertRaises(NotImplementedError):
            Factory().make()

    def test_get_factory(self):
        post_factory = Factory.get_factory("posts.PostFactory")
        self.assertEqual(post_factory, factories.PostFactory)

    def test_has_with_a_non_existent_factory_throws_a_value_error(self):
        post_factory = factories.PostFactory()
        with self.assertRaises(ValueError):
            post_factory.has("likes")

    def test_has_with_a_unrelated_name_throws_a_lookup_error(self):
        post_factory = factories.PostFactory()
        with self.assertRaises(LookupError):
            post_factory.has("unrelated")

    def test_factory_make_returns_instance(self):
        post_factory = factories.PostFactory()
        post = post_factory.make()
        self.assertIsNotNone(post)
        self.assertIsInstance(post, post_factory.model)

    def test_factory_make_with_has_throws_value_error(self):
        post_factory = factories.PostFactory()
        with self.assertRaises(ValueError):
            post_factory.has("comments", count=2).make()

    def test_factory_create_returns_instance(self):
        post_factory = factories.PostFactory()
        post = post_factory.create()
        self.assertIsNotNone(post)
        self.assertIsInstance(post, post_factory.model)
        self.assertIsNotNone(post.pk)

    def test_factory_create_with_has_returns_instance(self):
        post_factory = factories.PostFactory()
        post = post_factory.has("comments", count=5).create()
        self.assertIsNotNone(post)
        self.assertIsInstance(post, post_factory.model)
        self.assertIsNotNone(post.pk)
        self.assertEqual(post.comments.count(), 5)

    def test_factory_create_with_has_sequence_returns_instance(self):
        post_factory = factories.PostFactory()
        post = post_factory.has(
            "comments", count=5, sequence=[{"content": "Hello"}, {"content": "Post"}]
        ).create()
        self.assertIsNotNone(post)
        self.assertIsInstance(post, post_factory.model)
        self.assertIsNotNone(post.pk)
        self.assertEqual(post.comments.count(), 5)
        for comment in post.comments.all():
            self.assertIn(comment.content, ("Hello", "Post"))

    def test_factory_create_uses_custom_create_method_and_returns_instance(self):
        post_factory = factories.PostFactory2()
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

    def test_factory_make_batch_with_seq_returns_list(self):
        post_factory = factories.PostFactory()
        posts = post_factory.make_batch(3, sequence=[{"content": "Hello"}])
        self.assertIsNotNone(posts)
        self.assertIsInstance(posts, list)
        self.assertEqual(len(posts), 3)
        for post in posts:
            self.assertEqual(post.content, "Hello")

    def test_factory_create_batch_returns_list(self):
        post_factory = factories.PostFactory()
        posts = post_factory.create_batch(3)
        self.assertIsNotNone(posts)
        self.assertIsInstance(posts, list)
        self.assertEqual(len(posts), 3)
        for post in posts:
            self.assertIsNotNone(post.pk)

    def test_factory_create_batch_with_seq_returns_list(self):
        post_factory = factories.PostFactory()
        posts = post_factory.create_batch(3, sequence=[{"content": "Hello"}])
        self.assertIsNotNone(posts)
        self.assertIsInstance(posts, list)
        self.assertEqual(len(posts), 3)
        for post in posts:
            self.assertIsNotNone(post.pk)
            self.assertEqual(post.content, "Hello")

    def test_factory_with_incorrect_seq_raises_type_error(self):
        post_factory = factories.PostFactory()
        with self.assertRaises(TypeError):
            posts = post_factory.create_batch(3, sequence=[[]])

    def test_factory_handles_related_field(self):
        comment_factory = factories.CommentFactory()
        comment = comment_factory.create()
        self.assertIsNotNone(comment)
        self.assertIsNotNone(comment.pk)
        self.assertEqual(models.Post.objects.count(), 1)

    def test_factory_handles_related_field_model(self):
        comment_factory = factories.CommentFactory()
        post = factories.PostFactory().create()
        comment = comment_factory.create(post=post)
        self.assertIsNotNone(comment)
        self.assertIsNotNone(comment.pk)
        self.assertEqual(models.Post.objects.count(), 1)
        self.assertEqual(comment.post, post)

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

    def test_factory_handles_related_field_attr_overrides(self):
        comment_factory = factories.CommentFactory2()
        comment = comment_factory.create(post={"title": "My Title"})
        self.assertIsNotNone(comment)
        self.assertIsNotNone(comment.pk)
        self.assertEqual(models.Post.objects.count(), 1)
        self.assertEqual(comment.post.title, "My Title")

    def test_factory_handles_related_field_django_style_attr_overrides(self):
        comment_factory = factories.CommentFactory2()
        comment = comment_factory.create(post__title="My Title")
        self.assertIsNotNone(comment)
        self.assertIsNotNone(comment.pk)
        self.assertEqual(models.Post.objects.count(), 1)
        self.assertEqual(comment.post.title, "My Title")


class TestFactoryTestMixin(FactoryTestMixin, TestCase):
    factories = [factories.PostFactory, "posts.CommentFactory"]

    def test_factory_make_returns_instance(self):
        post_factory = self.get_factory_for(models.Post)
        post = post_factory.make()
        self.assertIsNotNone(post)
        self.assertIsInstance(post, post_factory.model)

    def test_factory_can_make_comment(self):
        comment_factory = self.get_factory_for("posts.Comment")
        comment = comment_factory.make()
        self.assertIsNotNone(comment)
        self.assertIsInstance(comment, comment_factory.model)
        self.assertIsNotNone(comment.post)
        self.assertIsInstance(comment.post, models.Post)
        self.assertIsNotNone(comment.post.pk)
        self.assertEqual(models.Post.objects.count(), 1)
