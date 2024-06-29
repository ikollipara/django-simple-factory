"""
factories.py
Ian Kollipara <ian.kollipara@cune.edu>

This file defines the base Factory class used by `django_factory`
"""

# Imports
import typing

import faker
from django.apps import apps
from django.db import models


class Factory[T: "models.Model"]:
    """The base factory class for creating model instances.

    A factory is a class that is used to create model instances
    with fake data. Factories are used to create model instances
    for testing purposes.

    A Factory requires a model to be set and the `definition` method
    to be overriden. The `definition` method should return a dictionary
    of the fields that will be set on the model.

    Attributes:
        - model (typing.Type[T] | str): The model that the factory will create.

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
    __factories: dict[str, "Factory"] = {}

    def __init_subclass__(cls) -> None:
        app_name = cls.__module__.split(".")[0]
        factory_name = cls.__name__
        cls.__factories[f"{app_name}.{factory_name}"] = cls

    @classmethod
    def get_factory(cls, app_name: str, factory_name: str = None) -> "Factory":
        """Get the factory for a given app and factory name.

        If the factory name is not provided, it is assumed that the
        app_name is in the format "app_name.factory_name".

        Args:
            app_name (str): The name of the app.
            factory_name (str): The name of the factory.
        """

        if factory_name is None:
            app_name, factory_name = app_name.split(".")
        return cls.__factories[f"{app_name}.{factory_name}"]

    def __init__(self):
        self.faker = self.configure_faker()
        self.model = (
            apps.get_model(self.model) if isinstance(self.model, str) else self.model
        )

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

    def make(self, **kwargs) -> T:
        """Make a model instance.

        Args:
            **kwargs: Additional keyword arguments to pass to the model.

        Returns:
            T: The made model instance.
        """

        definition = self.definition()
        for field, value in definition.items():
            definition[field] = self.__handle_related_field(field, value, kwargs)

        return self.model(**definition)

    def create(self, **kwargs) -> T:
        """Create a model instance.

        Args:
            **kwargs: Additional keyword arguments to pass to the model.

        Returns:
            T: The created model instance.
        """

        instance = self.make(**kwargs)

        if i := instance.save():
            return i
        return instance

    def create_quietly(self, **kwargs) -> T:
        """Create a model instance quietly.

        A quiet creation will not fire the `post_save` signal.

        Args:
            **kwargs: Additional keyword arguments to pass to the model.

        Returns:
            T: The created model instance.
        """

        from django.db.models import signals

        has_pre_init = signals.pre_init.has_listeners(self.model)
        has_post_init = signals.post_init.has_listeners(self.model)
        has_pre_save = signals.pre_save.has_listeners(self.model)
        has_post_save = signals.post_save.has_listeners(self.model)
        try:
            if has_pre_init:
                signals.pre_init.disconnect(self.model)
            if has_post_init:
                signals.post_init.disconnect(self.model)
            if has_pre_save:
                signals.pre_save.disconnect(self.model)
            if has_post_save:
                signals.post_save.disconnect(self.model)
            instance = self.create(**kwargs)
        finally:
            if has_pre_init:
                signals.pre_init.connect(self.model)
            if has_post_init:
                signals.post_init.connect(self.model)
            if has_pre_save:
                signals.pre_save.connect(self.model)
            if has_post_save:
                signals.post_save.connect(self.model)

        return instance

    def make_batch(self, size: int, **kwargs) -> list[T]:
        """Make a batch of model instances.

        Args:
            size (int): The size of the batch.
            **kwargs: Additional keyword arguments to pass to the model.

        Returns:
            list[T]: The made model instances.
        """

        return [self.make(**kwargs) for _ in range(size)]

    def create_batch(self, size: int, **kwargs) -> list[T]:
        """Create a batch of model instances.

        Args:
            size (int): The size of the batch.
            **kwargs: Additional keyword arguments to pass to the model.

        Returns:
            list[T]: The created model instances.
        """

        return [self.create(**kwargs) for _ in range(size)]

    def __handle_related_field(self, field, value, kwargs):
        if field in kwargs.keys() and isinstance(kwargs[field], models.Model):
            return kwargs[field]
        if isinstance(value, Factory):
            return value.create(**kwargs.get(field, {}))
        if value in self.__factories.keys():
            factory = self.__factories[value]()
            return factory.create(**kwargs.get(field, {}))
        return kwargs.get(field, value)
