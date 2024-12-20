# Django Simple Factory

A simple factory implementation built upon `Faker`.

## Installation
```
pip install django-simple-factory
```

## Usage
To use factories, create a `factories.py` inside of a Django app.
Then subclass the `django_simple_factory.factories.Factory` class.
To define the model generation, override the `definition` method.
```python
from django_simple_factory.factories import Factory
from posts import models

class PostFactory(Factory):
    model = models.Post

    def definition(self):
        return {
            "title": self.faker.word(),
            "content": self.faker.text(),
        }

class CommentFactory(Factory):
    model = "comments.Comment" # You can provide a model string

    def definition(self):
        return {
            "content": self.faker.text(),
            "post": PostFactory() # You can provide either a factory instance or a factory string (e.g)
        }
```

To use these models, instaniate the factories, then call either `make` or `create`.
```python
post_factory = PostFactory()
post_factory.make() # Does not persist
post_factory.create() # Does Persist
```

Factories that have related factories, say a Comment requires a Post, can pass a new dictionary for the post values to override.
```python
comment_factory = CommentFactory()
comment = comment_factory.make(content="Hello", post={"title": "My Post"})

comment.content # Hello
comment.post.title # My Post
```

Alternatively, you may use the "django-style" of `post__title="My Title"`.
```python
comment_factory = CommentFactory()
comment = comment_factory.make(content="Hello", post__title="My Post")

comment.content # Hello
comment.post.title # My Post
```

To create related models (those that have a foreign key to the curren model) use the `has` method.
Use the `related_name` to specify. You can optionally provide arguments and an amount to generate.
```python
post_factory = PostFactory()
post = post_factory.has("comments").create() # Creates a Post with a related comment.
```

To enable easier testing, a `FactoryTestMixin` has been included that enables rich definition of factories.
```python
from django_simple_factory.mixins import FactoryTestMixin
from django.test import TestCase
from posts import models

class PostTest(FactoryTestMixin, TestCase):
    factories = ["posts.PostFactory"]

    def test_post_creation(self):
        post = self.factories[models.Post].create()
        ...
```

## API

### `django_simple_factory.factories.Factory`
The primary class of the package, factories allow for simple and easy testing of Django models.

| Method | Description |
|--------|-------------|
| `configure_faker` | A hook that enables the configuration of the factory's faker instance. Each factory contains its own separate faker instance. |
| `get_factory` | A class method that enables the discovery of a Factory (e.g. ```Factory.get_factory("posts.PostFactory")```). The string passed in mimics the models access. To access a factory via string it should be of the form `<app_name>.<factory_name>`. |
| `make` | Make is one of the primary methods for creating an model. `make` does not persist the model, rather it just gives an instance. To override the generated values, provide keyword arguments to the method. If you want to override related object creation, provide a keyword argument with a dictionary (e.g. ```post_factory.make(user={"email": "test@example.com"})```) |
| `create` | Create is very much like make, except it does persist the model. |

## Contact
If there are any issues, please feel free to make an issue.
If you have suggested improvements, please make an issue where we can discuss.
