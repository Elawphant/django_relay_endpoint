Django Relay Endpoint
=====

"Django Relay Endpoint" is a Django addon that automatically configures a customizable graphql endpoint based on models.
The addon is made for "graphene_django".

Table of Contents
-----

- [Django Relay Endpoint](#django-relay-endpoint)
  - [Table of Contents](#table-of-contents)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [How to use](#how-to-use)
  - [Configuring NodeType subclasses](#configuring-nodetype-subclasses)
  - [Validators](#validators)
  - [Permissions](#permissions)
  - [License](#license)
  - [Tip the author](#tip-the-author)
  - [Docs](#docs)



Requirements
-----
Python 3.8 or higher
Django 4.2.7 or higher

This package will also install `graphene-django`, `graphene-file-upload` and `django_filter`.


Installation
-----

Install using pip...

```
pip install git+https://github.com/Elawphant/django_relay_endpoint.git
```

How to use
-----
1. Declare your NodeTypes and pass it to the SchemaConfigurator to get the schema. e.g.

```
# endpoint.py
from django_relay_endpoint import NodeType, SchemaConfigurator

class AuthorType(NodeType):
    @staticmethod
    def get_queryset(object_type, queryset, info):
        return queryset.filter(age__gte=35) # filter authors with age higher than 35

    class Meta:
        model = 'my_app.Author'
        fields = ['id', 'name', 'age', 'books']
        filter_fields = {
            'id': ('exact',),
            'name': ('iexact', 'icontains'),
        }
        extra_kwargs: {
            'name': {
                "required": True,
            },
            'age': {
                "required": True,
            }
        }

class BookType(NodeType):
    class Meta:
        model = 'my_app.Book'
        fields = ['id', 'name', 'authors']


schema = SchemaConfigurator([
    AuthorType,
    BookType,
]).schema()

```

2. In your urls.py add the endpoint
```
# urls.py
from graphene_file_upload.django import FileUploadGraphQLView
from my_app.endpoint import schema
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    # ... other urls
    path("graphql_dashboard_v1", csrf_exempt(FileUploadGraphQLView.as_view(graphiql=True, schema=schema))),
]

```

Configuring NodeType subclasses
-----

A subclass of NodeType can be configured via its Meta class.

Available options are as follows: 

**Following options can be configured on class Meta**:

- **model**: (Union[str, Type[models.Model]]) - a string composed of 'app_name.model_name' or actual django model.

- **fields**: List[str] | Literal["__all__"] - an explicit list of field names or '__all__'.

- **query_root_name**: str | None - a root field name. Defaults to lowered snake-case model._meta.verbose_name.

- **query_root_name_plural**: str | None - a root field name. Defaults to lowered snake-case model._meta.verbose_name_plural.

- **filter_fields**: Union[Dict[str, List[str]], List[str]] - fielter_fields configurations. see <https://docs.graphene-python.org/projects/django/en/latest/filtering/#filterable-fields>.

- **filterset_class**: FilterSet - a filterset_class. see <https://docs.graphene-python.org/projects/django/en/latest/filtering/#custom-filtersets>.

- **query_operations**: Literal["list", "detail"] - whether the query root field should be configured for single and multiple results. Defaults to `["list", "detail"]` which means both will be configured.

- **object_type_name**: str | None - The classname of the DjangoObjectType that will be configured. Defaults to camel-case `AppNameModelNameType`.

- **mutation_operations**: Literal["create", "update", "delete"] - similar to query_operations, this limits the root field configuration, defaults to `["create", "update", "delete"]`.

- **extra_kwargs**: Dict[str, Dict[str, Any]] - the mutation type fields are configured via assigned django form field; this option is similar to rest framework serializer `extra_kwargs`, which is a dictionary of field_names mapped to a dictionary of django form field kwargs. The configurator automatically maps the field to the respective form field: for field mapping see <https://docs.djangoproject.com/en/4.2/topics/forms/modelforms/#field-types>. For relations, it maps the fields to `graphene.List(graphene.ID, **field_kwargs)` `and graphene.ID(**field_kwargs)`, it will also infer the `required` parameter value from the declared `allow_blank` and `allow_null` parameters of the respective model.field.

- **field_validators**: Dict[str, List[Callable]] - a dictionary of field_names mapped to the list of validators: see [Validators](#Validators).

- **non_field_validators**: List[Callable] - list of validators: see [Validators](#Validators).

- **success_keyword**: str - a success keyword for mutation responses. by defualt it is 'success'. 

- **input_field_name**: str - a Input field name for mutations. Defaults to 'data'.

- **return_field_name**: str - the field name on the response on create and update mutations, if none provided, model._meta.model_name will be used.

- **permissions**: List[str] - A list of permission names, defaults to empty list, i.e. no permissions will be checked.

- **permission_classes**: List[Type[BasePermission]] - A list of permission classes. see [Permissions](#Permissions).

**Following fields can be configured on the subclass of the NodeType**:

- **get_queryset**: Callable - a static get_queryset method. Important! this method should be declared as staticmethod, it will be returned with the configured subclass of DjangoObjectType, queryset and info. It behaves as overwrite of get_queryset method, but is a staticmethod. See the example in [How to use](#how-to-use).


Validators
-----
A validator passed to `field_validators` or `non_field_validators` is a function that takes the following arguments:
- **data**: the field value for field_validators and whole data object for non_field_validators 

- **not_updated_model_instance**: the instance with the state before merging data with the instance 

- **info**: the graphene resolve info object instance.


Permissions
-----
We have extended DjangoObjectType and ClientIDMutation to support string permissions and class based permissions for queryset and object level permission checks.

Class based permissions extend custom `BasePermission` class, which implements `has_permission(self, info) -> bool` and `has_object_permission(self, info, obj) -> bool` methods. If the class returns `False` a permission-denied error will be raised. Following default permission classes can be found in graphene_relay_endpoint:
- **AllowAny**: This class is intended only for explicit declaration. It does nothing similar to the same permission in REST framework

- **IsAuthenticated**: Checks for authentication.

- **IsAdminUser**: Checks for admin privilege.

- **IsAuthenticatedOrReadOnly**: Limits mutation operations to authenticated users.

- **BasePermission**: A base class to subclass for custom permission classes.


License
-----
See the MIT licens in the LICENSE file in the project.

Tip the author
-----
If this project has facilitated your job and saved time spent on boilerplate code and pain of standardizing and debugging a relay style endpoint, consider tipping the author with some crypto:

**Bitcoin**: `3N5ot3DA2vSLwEqhjTGhfVnGaAuQoWBrCf`

Thank you!

Docs
-----
The addon is pretty simple. The [How to use](#how-to-use) and [Configuring NodeType subclasses](#configuring-nodetype-subclasses)  explains it all. Each piece of code is also documented with dockstrings and has respective type hints.
