# -*- coding: utf-8 -*-
"""
Clik extension that integrates with WTForms.

:author: Joe Joyce <joe@decafjoe.com>
:copyright: Copyright (c) Joe Joyce and contributors, 2017.
:license: BSD
"""
from __future__ import print_function

import datetime
import functools
import sys

from clik import args as clik_args, parser as clik_parser
from clik.compat import iteritems
from clik.util import AttributeDict
from wtforms import \
    BooleanField, \
    DateField as DateFieldBase, \
    DateTimeField as DateTimeFieldBase, \
    DecimalField as DecimalFieldBase, \
    FieldList as FieldListBase, \
    FloatField as FloatFieldBase, \
    Form as FormBase, \
    FormField, \
    IntegerField as IntegerFieldBase, \
    SelectField as SelectFieldBase, \
    SelectMultipleField as SelectMultipleFieldBase, \
    StringField as StringFieldBase
from wtforms.validators import Optional, Required


# =============================================================================
# ----- Fields ----------------------------------------------------------------
# =============================================================================

class DateField(DateFieldBase):
    def __init__(self, metavar=None, **kwargs):
        super(DateField, self).__init__(**kwargs)
        self.metavar = metavar


class DateTimeField(DateTimeFieldBase):
    def __init__(self, metavar=None, **kwargs):
        super(DateTimeField, self).__init__(**kwargs)
        self.metavar = metavar


class DecimalField(DecimalFieldBase):
    def __init__(self, metavar=None, **kwargs):
        super(DecimalField, self).__init__(**kwargs)
        self.metavar = metavar


class FieldList(FieldListBase):
    def __init__(self, unbound_field, metavar=None, **kwargs):
        super(FieldList, self).__init__(unbound_field, **kwargs)
        self.metavar = metavar


class FloatField(FloatFieldBase):
    def __init__(self, metavar=None, **kwargs):
        super(FloatField, self).__init__(**kwargs)
        self.metavar = metavar


class IntegerField(IntegerFieldBase):
    def __init__(self, metavar=None, **kwargs):
        super(IntegerField, self).__init__(**kwargs)
        self.metavar = metavar


class SelectField(SelectFieldBase):
    def __init__(self, metavar=None, choices=None, validators=None, **kwargs):
        if choices is not None:
            choices = [(choice, choice) for choice in choices]
        if validators is None:
            validators = []
        for validator in validators:
            if isinstance(validator, Required):
                break
        else:
            if not any(isinstance(v, Optional) for v in validators):
                validators.append(Optional())
        super_init = super(SelectField, self).__init__
        super_init(choices=choices, validators=validators, **kwargs)
        self.metavar = metavar

    def process_data(self, value):
        self.data = None
        if value is not None:
            try:
                self.data = self.coerce(value)
            except (ValueError, TypeError):
                pass


class SelectMultipleField(SelectField, SelectMultipleFieldBase):
    pass


class StringField(StringFieldBase):
    def __init__(self, metavar=None, **kwargs):
        super(StringField, self).__init__(**kwargs)
        self.metavar = metavar

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = valuelist[0]


# =============================================================================
# ----- Miscellany ------------------------------------------------------------
# =============================================================================

COMMON_DEFAULT_CALLABLES = {
    datetime.date.today: 'today',
    datetime.datetime.today: 'now',
    datetime.time: 'now',
}
EXAMPLE_DATETIME = datetime.datetime(2017, 11, 27, 13, 52, 41)

DATETIME_TYPES = (DateField, DateFieldBase, DateTimeField, DateTimeFieldBase)
MULTIPLE_VALUE_TYPES = (FieldList, FieldListBase, SelectMultipleField,
                        SelectMultipleFieldBase)
PRIMITIVE_TYPES = (DecimalField, DecimalFieldBase, FloatField, FloatFieldBase,
                   IntegerField, IntegerFieldBase, StringField,
                   StringFieldBase)
SELECT_TYPES = (SelectField, SelectFieldBase, SelectMultipleField,
                SelectMultipleFieldBase)
SIMPLE_TYPES = DATETIME_TYPES + PRIMITIVE_TYPES + SELECT_TYPES


def default(fn, parser_help_value):
    @functools.wraps(fn)
    def wrapper():
        return fn()
    wrapper.__clik_wtf__ = parser_help_value
    return wrapper


class FormError(Exception):
    """Error type for exceptions raised from this module."""


class Multidict(dict):
    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        if isinstance(value, list) and value:
            return value[0]
        return value

    def getlist(self, key):
        value = dict.__getitem__(self, key)
        if not isinstance(value, list):
            return [value]
        return value


# =============================================================================
# ----- Form ------------------------------------------------------------------
# =============================================================================

class Form(FormBase):
    short_arguments = None

    @staticmethod
    def get_short_arguments():
        pass

    def __init__(self, obj=None, prefix='', meta=None, data=None, **kwargs):
        if 'formdata' in kwargs:
            del kwargs['formdata']
        self._clik_constructor_kwargs = AttributeDict(
            data=data,
            kwargs=kwargs,
            meta=meta,
            obj=obj,
            prefix=prefix,
        )
        super(Form, self).__init__(**self._clik_constructor_kwargs)
        self._args = None

    def _configure_parser(self, parser, root=False):
        def quote(value):
            """Convenience fn that does not deserve its own top-level slot."""
            if len(value.split()) > 1:
                return '"%s"' % value
            return str(value)

        # Only the top-level form can have short arguments. Any
        # subforms (by way of FormFields) will ignore short arguments.
        short_args = {}
        if root:
            for value in (self.short_arguments, self.get_short_arguments()):
                if value is not None:
                    short_args.update(value)
            short_args = dict((v, k) for k, v in iteritems(short_args))

        for field in self:
            # Single-letter form fields would conflict with short
            # arguments.
            if len(field.name) == 1:
                fmt = 'field names must be at least two characters (got: "%s")'
                raise FormError(fmt % field.name)

            short_arg = short_args.get(field.name, None)

            if isinstance(field, FormField):
                # Form field is actually multiple fields, so there's
                # not a neat mapping for a short argument.
                if short_arg is not None:
                    msg = 'cannot assign a short argument to a FormField'
                    raise FormError(msg)

                # Recursively configure subforms.
                field.form._configure_parser(parser)
            else:
                # Do a bunch of order-sensitive computation and
                # manipulation of args and kwargs, then ultimately
                # call parser.add_argument(*args, **kwargs).
                args = ()
                if short_arg is not None:
                    args += ('-%s' % short_arg,)
                args += ('--%s' % field.name.replace('_', '-'),)
                kwargs = dict(help=field.description)

                def add_to_help(note):
                    if kwargs['help']:
                        kwargs['help'] += ' (%s)' % note
                    else:
                        kwargs['help'] = note

                if isinstance(field, FieldList):
                    kwargs['action'] = 'append'
                    kwargs['default'] = []
                    add_to_help('may be supplied multiple times')
                else:
                    # Mimic the way WTForms computes defaults. ``obj``
                    # overrides constructor ``kwargs``, which
                    # overrides ``data``, which overrides the defaults
                    # set on fields.
                    ctor_data = self._clik_constructor_kwargs.data
                    ctor_kwargs = self._clik_constructor_kwargs.kwargs
                    ctor_obj = self._clik_constructor_kwargs.obj
                    default = field.default
                    if ctor_obj and hasattr(ctor_obj, field.name):
                        default = getattr(ctor_obj, field.name)
                    # Overriding with plain ctor kwargs doesn't seem
                    # to work.
                    # elif field.name in ctor_kwargs:
                    #     default = ctor_kwargs[field.name]
                    elif ctor_data and field.name in ctor_data:
                        default = ctor_data[field.name]

                    if isinstance(field, SIMPLE_TYPES):
                        if getattr(field, 'metavar', None) is not None:
                            kwargs['metavar'] = field.metavar
                        handle_default = True
                        if isinstance(field, DATETIME_TYPES):
                            note_dt = EXAMPLE_DATETIME.strftime(field.format)
                            note_fmt = 'format: %s, example: %s'
                            note_args = (field.format, note_dt)
                            note = note_fmt % tuple(map(quote, note_args))
                            add_to_help(note.replace('%', '%%'))
                            if default and not callable(default):
                                handle_default = False
                                string = default.strftime(field.format)
                                add_to_help('default: %s' % quote(string))
                        if isinstance(field, SELECT_TYPES):
                            choices = [value for value, _ in field.choices]
                            quoted = [quote(choice) for choice in choices]
                            add_to_help('choices: %s' % ', '.join(quoted))
                            if isinstance(field, SelectMultipleField):
                                handle_default = False
                                kwargs['action'] = 'append'
                                kwargs['default'] = []
                                # Defaults on multiple select fields
                                # don't seem to work.
                                # if default:
                                #     if callable(default):
                                #         val = 'dynamic'
                                #     else:
                                #         quoted = [quote(v) for v in default]
                                #         val = ', '.join(quoted)
                                #     add_to_help('default: %s' % val)
                                add_to_help('may be supplied multiple times')
                        if handle_default:
                            val = None
                            if callable(default):
                                val = 'dynamic'
                                if hasattr(default, '__clik_wtf__'):
                                    val = default.__clik_wtf__
                                elif default in COMMON_DEFAULT_CALLABLES:
                                    val = COMMON_DEFAULT_CALLABLES[default]
                            elif default is not None:
                                val = quote(str(default))
                            if val is not None:
                                add_to_help('default: %s' % val)
                    # I am not happy with this implementation, and I'm
                    # not sure how to fix it.
                    # elif isinstance(field, BooleanField):
                    #     val = default
                    #     if callable(default):
                    #         val = default()
                    #     kwargs['default'] = val
                    #     if val:
                    #         kwargs['action'] = 'store_false'
                    #     else:
                    #         kwargs['action'] = 'store_true'
                    else:
                        fmt = 'unsupported field type: %s'
                        raise FormError(fmt % type(field))

                parser.add_argument(*args, **kwargs)

    def configure_parser(self, parser=None):
        if parser is None:  # pragma: no cover (obviously correct)
            parser = clik_parser
        self._configure_parser(parser, root=True)

    def _populate_formdata(self, formdata, args, hyphens=()):
        for field in self:
            if isinstance(field, FormField):
                hyphen = (len(field.name) + 1,)
                field.form._populate_formdata(formdata, args, hyphens + hyphen)
            else:
                key = field.name.replace('-', '_')
                value = getattr(args, key)
                if value is not None:
                    for i in hyphens:
                        key = '%s-%s' % (key[:i - 1], key[i:])
                    if isinstance(field, FieldList):
                        for i, item in enumerate(value):
                            formdata['%s-%i' % (key, i)] = item
                    else:
                        formdata[key] = value

    def _bind_formdata(self, formdata, args):
        self._args = args
        kwargs = self._clik_constructor_kwargs.copy()
        kwargs.update(dict(formdata=formdata))
        super(Form, self).__init__(**kwargs)
        for field in self:
            if isinstance(field, FormField):
                field.form._bind_formdata(formdata, args)

    def bind_args(self, args=None):
        if args is None:  # pragma: no cover (obviously correct)
            args = clik_args
        formdata = Multidict({'_': object()})
        self._populate_formdata(formdata, args)
        self._bind_formdata(formdata, args)

    def bind_and_validate(self, args=None):
        self.bind_args(args)
        return self.validate()

    def print_errors(self, file=sys.stderr):
        for field in self:
            if isinstance(field, FormField):
                field.form.print_errors(file)
            else:
                for error in field.errors:
                    error = error[0].lower() + error[1:]
                    msg = '%s: ' % field.name.replace('_', '-')
                    if not isinstance(field, MULTIPLE_VALUE_TYPES):
                        name = field.name.replace('-', '_')
                        msg += '%s: ' % getattr(self._args, name)
                    msg += error
                    print(msg, file=file)
