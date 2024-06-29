from django_factory.factories import Factory
from posts.models import Comment, Post


class PostFactory(Factory):

    model = "posts.Post"

    def definition(self) -> dict:
        return {
            "title": self.faker.sentence(),
            "content": self.faker.text(),
        }


class CommentFactory(Factory):
    model = Comment

    def definition(self) -> dict:
        return {
            "content": self.faker.text(),
            "post": PostFactory(),
        }


class CommentFactory2(Factory):
    model = Comment

    def definition(self) -> dict:
        return {
            "content": self.faker.text(),
            "post": "posts.PostFactory",
        }