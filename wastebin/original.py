# -*- coding: utf-8 -*-
"""
Clik extension that integrates with WTForms.

:author: Joe Joyce <joe@decafjoe.com>
:copyright: Copyright (c) Joe Joyce and contributors, 2017.
:license: BSD
"""
import argparse
import decimal

from clik import args as clik_args, parser as clik_parser
from clik.app import AttributeDict
from wtforms import BooleanField, DecimalField, FloatField, Form as BaseForm, \
    IntegerField, StringField

# - Boolean
# + Date
# + DateTime
# + Decimal
# + Time
# - File
# - MultipleFile
# + Float
# + Integer
# x Radio -- same as Select
# + Select
# + SelectMultiple
# x Submit -- no analogue in cli
# + String
# x Hidden -- no analog in cli?
# ? Password
# x TextArea -- same as String
# + FormField
# + FieldList

mappers = {}


class UnsupportedFieldType(Exception):
    """Raised when configuring the parser for an unsupported field type."""

    def __init__(self, type, form, field):
        fmt = 'unsupported field type: %s'
        super(UnsupportedFieldType, self).__init__(fmt % type)
        self.type = type
        self.form = form
        self.field = field


def decimal_type(value):
    try:
        return decimal.Decimal(value)
    except decimal.DecimalException:
        raise argparse.ArgumentTypeError("invalid decimal value: '%s'" % value)


def mapper(*types):
    def decorate(fn):
        for type in types:
            mappers[type] = fn
        return fn
    return decorate


def basic_kwargs(field, **extra_kwargs):
    rv = {}
    if field.description:
        rv['help'] = field.description
    if field.default is not None:
        rv['default'] = field.default
        if 'help' in rv:
            if len(str(field.default).split()) > 1:
                fmt = '"%(default)s"'
            else:
                fmt = '%(default)s'
            rv['help'] += ' (default: %s)' % fmt

    # This is a dumb hack to check whether the user explicitly
    # defined a label. If so, we want to use it as the metavar. If
    # not, we want to punt the metavar to argparse (by passing
    # nothing).
    #
    # As far as I can tell, there is no good way in WTForms to check
    # whether the label was defined in the form. In the Field
    # constructor, when label is unset, WTForms assigns it to a
    # default value (the value computed below). So we check for that
    # value, and if it matches, we ignore the label.
    #
    # I think the only end user failure case would be someone
    # explicitly setting the label to the default value and expecting
    # it to be the metavar. I'm ok with failing there.
    #
    # The other gotcha would be if WTForms changes how it computes the
    # default value. In that case, this check fails disastrously. That
    # should be fairly obvious, though, and a fix can be developed at
    # that time.
    default_label_text = field.name.replace('_', ' ').title()
    if field.label.text != default_label_text:
        rv['metavar'] = field.label.text

    rv.update(extra_kwargs)
    return rv


@mapper(BooleanField)
def get_boolean_kwargs(field):
    if field.default:
        action = 'store_false'
    else:
        action = 'store_true'
    kwargs = basic_kwargs(field, action=action)
    if 'metavar' in kwargs:
        del kwargs['metavar']
    return kwargs


@mapper(DecimalField)
def get_decimal_kwargs(field):
    return basic_kwargs(field, type=decimal_type)


@mapper(IntegerField)
def get_integer_kwargs(field):
    return basic_kwargs(field, type=int)


@mapper(FloatField)
def get_float_kwargs(field):
    return basic_kwargs(field, type=float)


@mapper(StringField)
def get_string_kwargs(field):
    return basic_kwargs(field)


class Form(BaseForm):
    def __init__(self, obj=None, meta=None, **kwargs):
        self._clik = AttributeDict(
            arguments={},
            kwargs=kwargs,
            meta=meta,
            obj=obj,
            rv=None,
        )

    def configure_argument(self, field_name, *args, **kwargs):
        self._clik.arguments[field_name] = (args, kwargs)

    def configure_parser(self, parser=None):
        if parser is None:
            parser = clik_parser

        # We are not yet initialized (since we don't yet have the args
        # data). Create a dummy instance of this form in order to
        # iterate over the fields.
        dummy_form = self.__class__()
        BaseForm.__init__(dummy_form)

        for field in dummy_form:
            method_name = 'configure_%s_argument' % field.name
            if field.name in self._clik.arguments:
                args, kwargs = self._clik.arguments[field.name]
                parser.add_argument(*args, **kwargs)
            elif hasattr(self, method_name):
                getattr(self, method_name)(parser)
            else:
                field_type = type(field)
                if field_type in mappers:
                    kwargs = mappers[field_type](field)
                    parser.add_argument('--%s' % field.name, **kwargs)
                else:
                    raise UnsupportedFieldType(field_type, self, field)

    def validate(self, args=None):
        if self._clik.rv is None:
            if args is None:
                args = clik_args
            super(Form, self).__init__(
                obj=self._clik.obj,
                meta=self._clik.meta,
                data=args.__dict__,
                **self._clik.kwargs
            )
            self._clik.rv = super(Form, self).validate()
        return self._clik.rv
