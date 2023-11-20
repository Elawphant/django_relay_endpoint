
import graphene
from graphql import Undefined, NullValueNode, BooleanValueNode
from datetime import timedelta
import ast
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from graphql.language.ast import (
    BooleanValueNode,
    FloatValueNode,
    IntValueNode,
    StringValueNode,
)
import re
import os
from typing import List, Any, Dict, Union, Tuple
from django.db import models
from django.forms import FilePathField as DjangoFilePathField
from django.utils.translation import gettext_lazy as _


class Duration(graphene.Int):
    @staticmethod
    def serialize(duration):
        if isinstance(duration, timedelta):
            # Serialize the timedelta as an integer representing microseconds
            return duration.total_seconds() * 1e6
        return Undefined

    @staticmethod
    def parse_literal(node):
        if isinstance(node, int):
            # Parse the integer value into a timedelta
            return timedelta(microseconds=node)
        return Undefined

    @staticmethod
    def parse_value(value):
        if isinstance(value, int):
            # Parse the integer value into a timedelta
            return timedelta(microseconds=value)
        return Undefined

    
class NullBoolean(graphene.Scalar):
    @staticmethod
    def serialize(value):
        return value

    @staticmethod
    def parse_value(value):
        if value in [True, False, None]:
            return value
        return Undefined

    @classmethod
    def parse_literal(cls, node):
        if isinstance(node, BooleanValueNode) or isinstance(node, NullValueNode):
            return node.value
        return Undefined
