# -*- coding: utf-8 -*-
"""
Clik extension that integrates with WTForms.

:author: Joe Joyce <joe@decafjoe.com>
:copyright: Copyright (c) Joe Joyce and contributors, 2017.
:license: BSD
"""
from clik import args as clik_args, parser as clik_parser
from clik.compat import iteritems
from wtforms import BooleanField, DateField, DateTimeField, DecimalField, \
    FloatField, Form as BaseForm, IntegerField, StringField


mappers = {}


def mapper(*types):
    def decorate(fn):
        for type in types:
            mappers[type] = fn
        return fn
    return decorate


@mapper(BooleanField)
def boolean_mapper(_, field):
    rv = dict(default=bool(field.default))

    if rv['default']:
        rv['action'] = 'store_false'
    else:
        rv['action'] = 'store_true'

    if field.description:
        rv['help'] = field.description

    return rv


@mapper(DateField, DateTimeField, DecimalField, FloatField, IntegerField,
        StringField)
def default_mapper(_, field):
    rv = {}

    if field.description:
        rv['help'] = field.description

    if field.default is not None:
        rv['default'] = field.default
        if 'help' in rv:
            rv['help'] += ' (default: %(default)s)'

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

    return rv


def wrap_formdata(form, args):
    pass


class Multidict(dict):
    def getlist(self, key):
        pass


class Form(BaseForm):
    short_arguments = None

    @staticmethod
    def get_short_arguments():
        pass

    def __init__(self, obj=None, meta=None, args=None, **kwargs):
        self._clik_constructor_kwargs = dict(obj=obj, meta=meta, kwargs=kwargs)
        if args is not None:
            self.bind_args(args)
        else:
            super(Form, self).__init__(obj=obj, meta=meta, **kwargs)

    def configure_parser(self, parser=None):
        if parser is None:
            parser = clik_parser

        short_args = {}
        for value in (self.short_arguments, self.get_short_arguments()):
            if value is not None:
                short_args.update(value)
        short_args = dict((value, key) for key, value in iteritems(short_args))

        for field in self:
            field_type = type(field)
            if field_type in mappers:
                kwargs = mappers[field_type](self, field)
            else:
                raise UnsupportedFieldType(field_type, self, field)

            args = ()
            if field.name in short_args:
                args += ('-%s' % short_args[field.name],)
            args +=  ('--%s' % field.name.replace('_', '-'),)

            parser.add_argument(*args, **kwargs)

    def bind_args(self, args=None):
        if args is None:
            args = clik_args
        kwargs = self._clik_constructor_kwargs.copy()
        kwargs.update(dict(formdata=wrap_formdata(self, args)))
        super(Form, self).__init__(**kwargs)

    def bind_and_validate(self, args=None):
        self.bind_args(args)
        return self.validate()

