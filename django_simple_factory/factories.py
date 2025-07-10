"""
registry.py
Ian Kollipara <ian.kollipara@cune.edu>

This file defines the base Factory class used by `django_factory`
"""

# Imports
import dataclasses
import typing
from copy import deepcopy
from itertools import cycle

import faker
from django.apps import apps
from django.core import exceptions
from django.db import models

T = typing.TypeVar("T", bound="models.Model")
F = typing.TypeVar("F", bound="models.Model")


@dataclasses.dataclass
class _RelatedGeneration:
    field_name: str
    factory: "Factory"
    kwargs: dict = dataclasses.field(default_factory=dict)


class Factory(typing.Generic[T]):
    """The base factory class for creating model instances.

    A factory is a class that is used to create model instances
    with fake data. Factories are used to create model instances
    for testing purposes.

    A Factory requires a model to be set and the `definition` method
    to be overriden. The `definition` method should return a dictionary
    of the fields that will be set on the model.

    Attributes:
        - model (typing.Type[T] | str): The model that the factory will create.
        - create_method (callable[[dict], T] | None): The method used when creating a model. Defaults to `.save()`.

    Methods:
        - get_factory: Get the factory for a given app and factory name.
        - configure_faker: Configure the faker instance for this factory.
        - definition: Generate a definition for the model.
        - make: Make a model instance.
        - create: Create a model instance.
        - create_quietly: Create a model instance quietly.
        - make_batch: Make a batch of model instances.
        - create_batch: Create a batch of model instances.
    """

    model: typing.Type[T] | str = None
    create_method: typing.Callable[[dict], T] | None = None
    _registry: dict[str, typing.Type["Factory"]] = {}

    @classmethod
    def get_factory(cls, app_name: str, factory_name: str = None) -> "Factory[F]":
        """Get the factory for a given app and factory name.

        If the factory name is not provided, it is assumed that the
        app_name is in the format "app_name.factory_name".

        Args:
            app_name (str): The name of the app.
            factory_name (str): The name of the factory.
        """

        if factory_name is None:
            app_name, factory_name = app_name.split(".")
        return cls._registry[f"{app_name}.{factory_name}"]

    def __init__(self):
        self.faker = self.configure_faker()
        self.model = self._get_model()
        self._related_generation: list[_RelatedGeneration] = []

    def configure_faker(self) -> "faker.Faker":
        """Configure the faker instance for this factory.

        This method should be overriden if there is a need
        for custom configuration of the faker instance.

        Returns:
            faker.Faker: The configured faker instance.
        """

        return faker.Faker()

    def definition(self) -> dict:
        """Generate a definition for the model.

        This method should be overriden to define the
        fields that will be set on the model.

        Returns:
            dict: The definition for the model.
        """

        raise NotImplementedError("The definition method must be overriden.")

    def has(
        self,
        related_name: str,
        *,
        count: int = 1,
        sequence: list[dict] = None,
        **kwargs,
    ):
        """Queue up multiple dependent relationships to create.

        The related name should be the related name from the model.
        If a factory implementation exists for it, it will use that.
        Otherwise a ValueError is thrown.
        """

        sequence = self.__resolve_sequence(count, sequence)

        model = self._get_model()
        related_model_field_name, related_factory = self.__resolve_related_field(
            model, related_name
        )
        kwargs = self.__handle_django_relationship_kwargs(kwargs)

        self._related_generation += [
            _RelatedGeneration(related_model_field_name, related_factory, model_kwargs)
            for model_kwargs in self.__resolve_sequence_with_kwargs(sequence, kwargs)
        ]

        return self

    def make(self, **kwargs) -> T:
        """Make a model instance.

        Args:
            **kwargs: Additional keyword arguments to pass to the model.

        Returns:
            T: The made model instance.
        """

        if len(self._related_generation) > 0:
            raise ValueError("Cannot use make when trying to create dependent models!")

        definition = self.__resolve_definition(**kwargs)

        return self.model(**definition)

    def create(self, **kwargs) -> T:
        """Create a model instance.

        Args:
            **kwargs: Additional keyword arguments to pass to the model.

        Returns:
            T: The created model instance.
        """

        definition = self.__resolve_definition(**kwargs)
        if self.create_method is None:
            instance = self.model(**definition)
            instance.save()
        else:
            instance = self.create_method(**definition)

        instance.refresh_from_db()

        for related_gen in self._related_generation:
            related_gen.factory.create(
                **(related_gen.kwargs | {related_gen.field_name: instance})
            )
        self._related_generation.clear()

        return instance

    def make_batch(self, size: int, sequence: list[dict] = None, **kwargs) -> list[T]:
        """Make a batch of model instances.

        Args:
            size (int): The size of the batch.
            sequence (list[dict]): The sequence to apply to the created models. Will be merged with kwargs.
            **kwargs: Additional keyword arguments to pass to the model.

        Returns:
            list[T]: The made model instances.
        """

        size_range = range(size)
        _sequence = self.__resolve_sequence_with_kwargs(
            sequence or [dict() for _ in size_range], kwargs
        )

        return [self.make(**params) for params, _ in zip(cycle(_sequence), size_range)]

    def create_batch(self, size: int, sequence: list[dict] = None, **kwargs) -> list[T]:
        """Create a batch of model instances.

        Args:
            size (int): The size of the batch.
            sequence (list[dict]): The sequence to apply to the created models. Will be merged with kwargs.
            **kwargs: Additional keyword arguments to pass to the model.

        Returns:
            list[T]: The created model instances.
        """

        size_range = range(size)
        _sequence = self.__resolve_sequence_with_kwargs(
            sequence or [dict() for _ in size_range], kwargs
        )

        return [
            self.create(**params) for params, _ in zip(cycle(_sequence), size_range)
        ]

    def __resolve_sequence_with_kwargs(self, sequence, kwargs):
        """Update the sequence dictionaries to include the kwargs."""

        try:
            return [(params | kwargs) for params in sequence]
        except TypeError as e:
            e.add_note("The sequence must be a list or tuple of dictionaries.")
            raise e

    @classmethod
    def _get_model(cls):
        """Resolve the model for the factory."""

        if isinstance(cls.model, str):
            return apps.get_model(cls.model)

        return cls.model

    def __resolve_definition(self, **kwargs):
        """Resolve the definition for the factory using the provided keyword arguments."""

        definition = self.definition()
        kwargs = self.__handle_django_relationship_kwargs(kwargs)
        for field, value in definition.items():
            definition[field] = self.__handle_related_field(field, value, kwargs)

        return definition

    def __handle_django_relationship_kwargs(self, kwargs: dict):
        _kwargs = deepcopy(kwargs)
        for keyword, value in ((k, v) for k, v in kwargs.items() if "__" in k):
            *models, property = keyword.split("__")
            nested_structure = _list_to_nested_dict(models, property, value)
            _kwargs.update(nested_structure)

        return _kwargs

    def __handle_related_field(self, field, value, kwargs):
        """Handle the creation of related models for the factory."""

        if field in kwargs.keys() and isinstance(kwargs[field], models.Model):
            return kwargs[field]

        if isinstance(value, Factory):
            return value.create(**kwargs.get(field, {}))

        # Handles the case where the provided value
        # is a factory string like "posts.PostFactory"
        if value in self._registry.keys():
            factory = self._registry[value]()
            return factory.create(**kwargs.get(field, {}))

        return kwargs.get(field, value)

    def __resolve_sequence(self, count: int, sequence: list[dict] | None) -> list[dict]:
        """Resolve the provided sequence to the correct count length."""
        if sequence is None:
            return [dict() for _ in range(count)]

        else:
            return [seq for seq, _ in zip(cycle(sequence), range(count))]

    def __resolve_related_field(self, model, related_name):
        try:
            related_field_name = model._meta.get_field(related_name).remote_field.name
            related_factory = self.__get_factory_for(
                model._meta.get_field(related_name).related_model
            )
            return related_field_name, related_factory
        except exceptions.FieldDoesNotExist as e:
            e.add_note(f"{related_name} is not a related field on the model.")
            raise LookupError(e.args)

    def __get_factory_for(
        self, model: typing.Type[models.Model]
    ) -> typing.Type["Factory"]:
        for factory in (f for f in self._registry.values() if f.model is not None):
            if factory._get_model()._meta.label == model._meta.label:
                return factory()

        raise ValueError(f"Cannot find factory for {model._meta.app_label}")


def _list_to_nested_dict(lst, property, value):
    if not lst:
        return {property: value}
    return {lst[0]: _list_to_nested_dict(lst[1:], property, value)}
