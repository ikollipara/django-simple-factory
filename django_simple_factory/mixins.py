"""
mixins.py
Ian Kollipara <ian.kollipara@cune.edu>

This file defines the mixins used by `django_factory`
"""

import typing
import unittest

from django.apps import apps

from django_simple_factory.factories import Factory

if typing.TYPE_CHECKING:  # pragma: no cover
    from django.db.models import Model


class _FactoryDictionary(dict["Model", Factory]):
    def __getitem__(self, key: str | type["Model"]):
        if isinstance(key, str):
            key = apps.get_model(key)
        return super().__getitem__(key)


class FactoryTestMixin(unittest.TestCase):
    """A mixin for testing factories.

    This mixin provides a setup class method that will create
    all of the factories defined in the `factories` attribute
    as instances of the factory class.

    To use this mixin, define a list of factories in the
    `factories` attribute of the test class. The factories
    can be either the factory class or the factory name as a string.

    Then use the `FactoryTestMixin.get_factory_for` helper to get a particular
    factory. This method also accepts a type parameter to handle the type of the model.

    Example:
    ```python
    class TestFactory(FactoryTestMixin, TestCase):

        factories = [PostFactory, "posts.CommentFactory"]

        def test_factory_make_returns_instance(self):
            post_factory = self.get_factory_for(models.Post)
            post = post_factory.make()
    ```

    Attributes:
        - factories (list[type[Factory] | str]): The factories to create.
    """

    factories: list[type[Factory] | str] = []

    @classmethod
    def setUpClass(cls) -> None:
        factories = _FactoryDictionary()
        for factory in cls.factories:
            factory_instance = (
                factory()
                if not isinstance(factory, str)
                else Factory.get_factory(factory)()
            )
            factories[factory_instance.model] = factory_instance
        cls.factories = factories
        super().setUpClass()

    @classmethod
    def get_factory_for[T: "Model"](cls, model: typing.Type[T] | str) -> Factory[T]:
        """Get the given factory for use in the tests."""

        return cls.factories[model]
