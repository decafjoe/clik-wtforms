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
from wtforms.validators import InputRequired, Optional


#: Version of the library.
#:
#: :type: :class:`str`
__version__ = '0.90.0'


# =============================================================================
# ----- Fields ----------------------------------------------------------------
# =============================================================================

class DateField(DateFieldBase):
    """:class:`wtforms.fields.DateField` with :attr:`metavar`."""

    def __init__(self, metavar=None, **kwargs):
        """
        Instantiate unbound field.

        :param str metavar: Value for :attr:`metavar`
        :param kwargs: Keyword arguments to pass to parent initializer
        """
        super(DateField, self).__init__(**kwargs)

        #: Value to use for metavar_ keyword argument to
        #: :meth:`argparse.ArgumentParser.add_argument`.
        #:
        #: .. _metavar: https://docs.python.org/library/argparse.html#metavar
        #:
        #: :type: :class:`str` or ``None``
        self.metavar = metavar


class DateTimeField(DateTimeFieldBase):
    """:class:`wtforms.fields.DateTimeField` with :attr:`metavar`."""

    def __init__(self, metavar=None, **kwargs):
        """
        Instantiate unbound field.

        :param str metavar: Value for :attr:`metavar`
        :param kwargs: Keyword arguments to pass to parent initializer
        """
        super(DateTimeField, self).__init__(**kwargs)

        #: Value to use for metavar_ keyword argument to
        #: :meth:`argparse.ArgumentParser.add_argument`.
        #:
        #: .. _metavar: https://docs.python.org/library/argparse.html#metavar
        #:
        #: :type: :class:`str` or ``None``
        self.metavar = metavar


class DecimalField(DecimalFieldBase):
    """:class:`wtforms.fields.DecimalField` with :attr:`metavar`."""

    def __init__(self, metavar=None, **kwargs):
        """
        Instantiate unbound field.

        :param str metavar: Value for :attr:`metavar`
        :param kwargs: Keyword arguments to pass to parent initializer
        """
        super(DecimalField, self).__init__(**kwargs)

        #: Value to use for metavar_ keyword argument to
        #: :meth:`argparse.ArgumentParser.add_argument`.
        #:
        #: .. _metavar: https://docs.python.org/library/argparse.html#metavar
        #:
        #: :type: :class:`str` or ``None``
        self.metavar = metavar


class FieldList(FieldListBase):
    """:class:`wtforms.fields.FieldList` with :attr:`metavar`."""

    def __init__(self, unbound_field, metavar=None, **kwargs):
        """
        Instantiate unbound field.

        :param str metavar: Value for :attr:`metavar`
        :param kwargs: Keyword arguments to pass to parent initializer
        """
        super(FieldList, self).__init__(unbound_field, **kwargs)

        #: Value to use for metavar_ keyword argument to
        #: :meth:`argparse.ArgumentParser.add_argument`.
        #:
        #: .. _metavar: https://docs.python.org/library/argparse.html#metavar
        #:
        #: :type: :class:`str` or ``None``
        self.metavar = metavar


class FloatField(FloatFieldBase):
    """:class:`wtforms.fields.FloatField` with :attr:`metavar`."""

    def __init__(self, metavar=None, **kwargs):
        """
        Instantiate unbound field.

        :param str metavar: Value for :attr:`metavar`
        :param kwargs: Keyword arguments to pass to parent initializer
        """
        super(FloatField, self).__init__(**kwargs)

        #: Value to use for metavar_ keyword argument to
        #: :meth:`argparse.ArgumentParser.add_argument`.
        #:
        #: .. _metavar: https://docs.python.org/library/argparse.html#metavar
        #:
        #: :type: :class:`str` or ``None``
        self.metavar = metavar


class IntegerField(IntegerFieldBase):
    """:class:`wtforms.fields.IntegerField` with :attr:`metavar`."""

    def __init__(self, metavar=None, **kwargs):
        """
        Instantiate unbound field.

        :param str metavar: Value for :attr:`metavar`
        :param kwargs: Keyword arguments to pass to parent initializer
        """
        super(IntegerField, self).__init__(**kwargs)

        #: Value to use for metavar_ keyword argument to
        #: :meth:`argparse.ArgumentParser.add_argument`.
        #:
        #: .. _metavar: https://docs.python.org/library/argparse.html#metavar
        #:
        #: :type: :class:`str` or ``None``
        self.metavar = metavar


class SelectField(SelectFieldBase):
    """:class:`wtforms.fields.SelectField` specialized for CLI use."""

    def __init__(self, metavar=None, choices=None, validators=None, **kwargs):
        """
        Instantiate unbound form, changing some default WTForms behaviors.

        This subclass makes three changes to WTForms' default select field:

        1. Adds :attr:`metvar`
        2. Makes field optional by default, rather than required
        3. Takes a sequence of values for ``choices`` rather than a sequence
           of 2-tuples

        For (2), this subclass looks at the list of ``validators`` and, if
        :class:`wtforms.validators.InputRequired` is not present, adds
        :class:`wtforms.validators.Optional`.

        For ``choices``, by default WTForms expects something like this::

            (
                (value, label),
                ('milk', '2% Milk'),
                ('eggs', 'Half Dozen Eggs'),
                ('cheese', 'Cheddar Cheese'),
            )

        That makes sense for HTML forms, where ``<option>`` nodes have values
        and labels.

        For argparse, that doesn't translate at all. Instead, this class
        just wants the values::

            ('milk', 'eggs', 'cheese')

        This will be turned into a structure WTForms can handle::

            (('milk', 'milk'), ('eggs', 'eggs'), ('cheese', 'cheese'))

        Convenience at its finest.

        :param str metavar: Value for :attr:`metavar`
        :param choices: Sequence of valid values for this field
        :type choices: Sequence of :class:`str` values
        :param validators: Optional sequence of validators
        :type validators: Sequence of WTForms validators
        :param kwargs: Keyword arguments to pass to parent initializer
        """
        if choices is not None:
            choices = [(choice, choice) for choice in choices]
        if validators is None:
            validators = []
        for validator in validators:
            if isinstance(validator, InputRequired):
                break
        else:
            if not any(isinstance(v, Optional) for v in validators):
                validators.append(Optional())
        super_init = super(SelectField, self).__init__
        super_init(choices=choices, validators=validators, **kwargs)

        #: Value to use for metavar_ keyword argument to
        #: :meth:`argparse.ArgumentParser.add_argument`.
        #:
        #: .. _metavar: https://docs.python.org/library/argparse.html#metavar
        #:
        #: :type: :class:`str` or ``None``
        self.metavar = metavar

    def process_data(self, value):
        """Do not stringify ``None`` when there is no data."""
        self.data = None
        if value is not None:
            try:
                self.data = self.coerce(value)
            except (ValueError, TypeError):
                pass


class SelectMultipleField(SelectField, SelectMultipleFieldBase):
    """
    :class:`wtforms.fields.SelectMultipleField` specialized for CLI use.

    This is actually just a dumb container class that uses inheritance to
    pick up :meth:`SelectField.__init__` for the initializer and otherwise
    defer all calls to :class:`wtforms.fields.SelectMultipleField`.
    """


class StringField(StringFieldBase):
    """:class:`wtforms.fields.StringField` with :attr:`metavar`."""

    def __init__(self, metavar=None, **kwargs):
        """
        Instantiate unbound field.

        :param str metavar: Value for :attr:`metavar`
        :param kwargs: Keyword arguments to pass to parent initializer
        """
        super(StringField, self).__init__(**kwargs)

        #: Value to use for metavar_ keyword argument to
        #: :meth:`argparse.ArgumentParser.add_argument`.
        #:
        #: .. _metavar: https://docs.python.org/library/argparse.html#metavar
        #:
        #: :type: :class:`str` or ``None``
        self.metavar = metavar

    def process_formdata(self, valuelist):
        """
        Sanely set "no value" value to ``None``.

        By default, WTForms puts an empty string in ``data`` when no data
        is provided. This is in contrast to all other fields, whose ``data``
        is ``None`` when no data is supplied.

        I can't see a reason why WTForms would behave this way, so this
        method overrides the behavior, leaving ``data`` as ``None`` when
        no user input is provided.
        """
        if valuelist:
            self.data = valuelist[0]


# =============================================================================
# ----- Miscellany ------------------------------------------------------------
# =============================================================================

#: Maps functions that are commonly used to generate default values to
#: human-friendly strings to be shown in help messages.
#:
#: :type: :class:`dict` mapping ``fn -> str``
COMMON_DEFAULT_CALLABLES = {
    datetime.date.today: 'today',
    datetime.datetime.today: 'now',
    datetime.time: 'now',
}

#: Datetime instance used when generating example inputs for help
#: messages for date/time based fields.
#:
#: :type: :class:`datetime.datetime`
EXAMPLE_DATETIME = datetime.datetime(2017, 11, 27, 13, 52, 41)

#: Types that are date/time related.
#:
#: :type: :func:`tuple`
DATETIME_TYPES = (DateField, DateFieldBase, DateTimeField, DateTimeFieldBase)

#: Types that accept multiple values.
#:
#: :type: :func:`tuple`
MULTIPLE_VALUE_TYPES = (FieldList, FieldListBase, SelectMultipleField,
                        SelectMultipleFieldBase)

#: Types that represent primitive values. "Primitive" does not have a
#: hard definition in this context.
#:
#: :type: :func:`tuple`
PRIMITIVE_TYPES = (DecimalField, DecimalFieldBase, FloatField, FloatFieldBase,
                   IntegerField, IntegerFieldBase, StringField,
                   StringFieldBase)

#: Types deriving from :class:`wtforms.fields.SelectField`.
#:
#: :type: :func:`tuple`
SELECT_TYPES = (SelectField, SelectFieldBase, SelectMultipleField,
                SelectMultipleFieldBase)

#: Types that are "simple." Like :data:`PRIMITIVE_TYPES`, there isn't
#: a hard definition for simple outside of "what makes sense for the
#: code below."
#:
#: This is simply an amalgamation of :data:`DATETIME_TYPES`,
#: :data:`PRIMITIVE_TYPES`, and :data:`SELECT_TYPES`.
#:
#: :type: :func:`tuple`
SIMPLE_TYPES = DATETIME_TYPES + PRIMITIVE_TYPES + SELECT_TYPES


def default(fn, parser_help_value):
    """
    Specify human-friendly labels for default value functions.

    Consider the following (silly) form::

        def my_default():
            return datetime.date.today().strftime('%Y-%m-%d')

        class MyForm(Form):
            value = StringField(default=my_default)

    clik-wtforms can't know the default value, so for help messages it simply
    shows ``default: dynamic``. The :func:`default` function allows the
    caller to change the label::

        class MyForm(Form):
            value = StringField(default=default(my_default, 'today'))

    In the help message, the default will now be shown as ``default: today``.

    :param fn: Function to wrap
    :type fn: ``fn() -> default value``
    :param str parser_help_value: Value to show as the default in the help
                                  message
    :return: ``fn``
    """
    @functools.wraps(fn)
    def wrapper():
        return fn()
    wrapper.__clik_wtf__ = parser_help_value
    return wrapper


def stringify(value):
    """
    Return string ``value``, with quotes around if there is whitespace.

    :param value: Value to stringify
    :return: Stringified, possibly quoted, value
    :rtype: :class:`str`
    """
    rv = str(value)
    if len(rv.split()) > 1:
        return '"%s"' % rv
    return rv


class FormError(Exception):
    """Error type for exceptions raised from this module."""


class Multidict(dict):
    """Just enough multidict to make WTForms happy."""

    def __getitem__(self, key):
        """Return value for ``key``, or first item if value is list."""
        value = dict.__getitem__(self, key)
        if isinstance(value, list) and value:
            return value[0]
        return value

    def getlist(self, key):
        """
        Return list value for ``key``.

        If value is a list, it is returned directly. If value is not a list,
        it is returned as the single item in a new list (i.e. ``[value]``).
        """
        value = dict.__getitem__(self, key)
        if not isinstance(value, list):
            return [value]
        return value


# =============================================================================
# ----- Form ------------------------------------------------------------------
# =============================================================================

class Form(FormBase):
    """
    Bridge between :mod:`argparse` and :mod:`wtforms`.

    The bridge works by configuring an argument parser to accept user input
    for the form fields, then translating the parsed arguments back into
    a multidict that mimics what WTForms would get from an HTML form.

    Due to the difference in the environments, the instance lifecycle is
    a little weird. For the web environment, end user data is available
    up front in ``request.POST`` (or whatever) when the form object is
    instantiated. For the CLI environment, we have to instantiate the
    form object *before* we have user data, in order to configure the
    parser.

    As a result, it doesn't make sense to pass ``formdata`` to the
    constructor of a CLI form. Any formdata constructor arguments are
    silently deleted [#]_.

    When a form is instantiated, the constructor keyword arguments are
    captured and the superclass constructor (:class:`wtforms.form.Form`)
    is called with no arguments. This causes the fields to be bound, which
    lets us iterate them in order to configure the parser, using
    :meth:`configure_parser`. Note that there will be no data available at
    this point if ``validate()`` is called.

    After the end-user arguments are obtained, they are "bound" to the
    form using :meth:`bind_args`. During the bind, the arguments are
    translated into a multidict that mimics what WTForms would get from an
    HTML form, then the superclass constructor (:class:`wtforms.form.Form`) is
    re-called with the multidict and the keyword arguments captured when the
    form was initialized.

    At that point the form can be validated, and behaves exactly as a stock
    WTForms form.

    .. [#] I'd love to raise an error as a signal to callers not to pass
           the argument. But WTForms passes this argument as part of its
           handling of ``FormField`` fields, so raising an error completely
           breaks ``FormField``. Since we can't tell whether the caller
           an end user or WTForms itself, the best we can do is silently
           ignore the parameter.
    """

    #: Dictionary mapping single-letter short arguments to field
    #: names. See :meth:`get_short_arguments` for more info.
    #:
    #: :type: :class:`dict` mapping ``char -> str`` (where ``char`` is
    #:        a single-letter string) or ``None``
    short_arguments = None

    @staticmethod
    def get_short_arguments():
        """
        Return dictionary mapping single-letter short arguments to field names.

        Short arguments can be specified by subclasses statically by defining
        :attr:`short_arguments` or dynamically by defining this method. When
        both are defined, the dictionaries are merged, with
        :meth:`get_short_arguments` overriding :attr:`short_arguments` for
        any conflicts.

        Dictionaries look like this::

            class MyForm(Form):
                short_arguments = dict(c='comment')

                @staticmethod
                def get_short_arguments():
                    # Just for demonstration. In real code this would go in
                    # the short_arguments attribute above.
                    return dict(n='name')

                comment = StringField()
                name = StringField()

        The end user can now specify values for ``comment`` and ``name`` using
        ``-c 'my comment'`` and ``-n 'My Name'``, respectively.
        """

    def __init__(self, obj=None, prefix='', meta=None, data=None, **kwargs):
        """
        Instantiate the form object.

        This captures the supplied arguments to be later used when the form
        is instantiated "for real," when it's bound to end user arguments
        using :meth:`bind_args`.
        """
        if 'formdata' in kwargs:
            del kwargs['formdata']
        self._clik_constructor_kwargs = AttributeDict(
            data=data,
            kwargs=kwargs,
            meta=meta,
            obj=obj,
            prefix=prefix,
        )
        super(Form, self).__init__(prefix=prefix)
        self._args = None

    def _configure_parser(self, parser, root=False):
        """
        Super-spaghetti method that does the heavy lifting for parser config.

        :param parser: Parser we are currently configuring
        :type parser: :class:`clik.argparse.ArgumentParser`
        :param bool root: Whether this form instance is the root form (if
                          ``False``, this form is being configured because
                          it is a ``FormField`` of a parent form)
        """
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
                    # ctor_kwargs = self._clik_constructor_kwargs.kwargs
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
                            note = note_fmt % tuple(map(stringify, note_args))
                            add_to_help(note.replace('%', '%%'))
                            if default and not callable(default):
                                handle_default = False
                                string = default.strftime(field.format)
                                add_to_help('default: %s' % stringify(string))
                        if isinstance(field, SELECT_TYPES):
                            choices = [value for value, _ in field.choices]
                            quoted = [stringify(choice) for choice in choices]
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
                                #         s = [stringify(v) for v in default]
                                #         val = ', '.join(s)
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
                                val = stringify(default)
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
        """
        Add arguments to ``parser`` for this form's fields.

        :param parser: Optional parser to configure, defaults to
                       :data:`clik.app.parser`
        :type parser: :class:`clik.argparse.ArgumentParser`
        """
        if parser is None:  # pragma: no cover (obviously correct)
            parser = clik_parser
        self._configure_parser(parser, root=True)

    def _populate_formdata(self, formdata, args, hyphens=()):
        """
        Translate argparse ``args`` into the WTForms multidict ``formdata``.

        The tricky part is translating keys in the context of subforms.
        Argparse arguments use all underscores; WTForms uses a mixture of
        underscores and hyphens to "scope" each form.

        Consider the set of forms::

            class GrandchildForm(Form):
                a_aa = StringField()

            class ChildForm(Form):
                b_b_b = FormField(GrandchildForm)

            class ParentForm(Form):
                ccc = FormField(ChildForm)

        .. highlight:: none

        This boils down to a single argument::

            --ccc-b-b-b-a-aa

        For ``args``, the key will come back as::

            ccc_b_b_b_a_aa

        In order to scope the value properly, WTForms wants this::

            ccc-b_b_b-a_aa

        Translating ``args`` into what WTForms wants is the heart of this
        method, and relies on the ``hyphens`` argument. ``hyphens`` is a
        tuple of integers representing indices of underscores that need to
        be changed to hyphens.

        For the root form (``ParentForm`` in the example above), ``hyphens``
        starts out empty. All underscores are left as is when populating
        the form data.

        When the root form encounters a ``FormField``, it looks at the
        length of the field name, adds 1, and appends that integer to the
        ``hyphens`` tuple. It doesn't matter if the field name is ``"simple"``
        or ``"more_complex_with_underscores"``, all we care is that the
        character after that (which will be an underscore, to scope the
        fields of the subform) is translated to a hyphen.

        This process is done recursively for all child forms.

        The other (less) tricky part is how WTForms handles ``FieldList``
        fields. For whatever reason, it wants them sort of pseudo-indexed
        in the keys of the formdata. (I'm not sure how else to describe it.)

        .. highlight:: python

        For example, consider the form::

            class MyForm(Form):
                value = FieldList(StringField())

        Unlike ``SelectMultipleField``, which can simply take a list of values
        from the multidict, ``FieldList`` requires separate keys for each
        argument, like this::

            {'value-0': 'foo', 'value-1': 'bar', 'value-2': 'baz'}

        I think this is designed to provide a friendly workflow for HTML
        forms, but it's kind of stupid in a CLI context. In any case,
        we also translate values from ``FieldList`` fields into the
        appropriate structure inside formdata.

        :param Multidict formdata: Data object we are currently populating
        :param argparse.Namespace args: Arguments from the end user
        :param tuple hyphens: Sequence of indices of underscores that must be
                              replaced with hyphens in key names from ``args``
        """
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
        """Recursively bind this form and its child forms."""
        self._args = args
        kwargs = self._clik_constructor_kwargs.copy()
        kwargs.update(dict(formdata=formdata))
        super(Form, self).__init__(**kwargs)
        for field in self:
            if isinstance(field, FormField):
                field.form._bind_formdata(formdata, args)

    def bind_args(self, args=None):
        """
        Bind arguments to the form.

        :param args: End user arguments to bind to the form, defaults to
                     :data:`clik.app.args`
        :type args: :class:`argparse.Namespace`
        """
        if args is None:  # pragma: no cover (obviously correct)
            args = clik_args
        formdata = Multidict({'_': object()})
        self._populate_formdata(formdata, args)
        self._bind_formdata(formdata, args)

    def bind_and_validate(self, args=None):
        """
        Bind and validate the form.

        Calls :meth:`bind_args` then :meth:`wtforms.form.Form.validate`.

        :return: Boolean indicating whether validation was successful
        :rtype: :class:`bool`
        """
        self.bind_args(args)
        return self.validate()

    def print_errors(self, file=sys.stderr):
        """
        Print error messages to ``file``.

        :param file: Stream to output to
        :type file: file-like object
        """
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
