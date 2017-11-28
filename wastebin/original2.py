import argparse
import datetime
import decimal
import functools

from clik import args as clik_args, parser as clik_parser
from clik.compat import iteritems
from wtforms import Form as BaseForm


# attribute name -> argument name (_ -> -)
# label -> metavar
# description -> help text
# default -> default

# short_arguments = dict(foo='f')
# get_short_arguments() -> dict(foo='f')
# <field>_argument_kwargs() -> dict()
# configure_<field>_argument(???) -> None or args.name


mappers = {}


def mapper(type):
    def decorate(fn):
        mappers[type] = fn
        return fn
    return decorate


def basic_mapper(type, exclude_keys=None):
    if exclude_keys is None:
        exclude_keys = ()

    def decorator(fn):
        @mapper(type)
        @functools.wraps(fn)
        def decorate(form, field):
            rv = basic_kwargs(field, exclude_keys)
            extra = fn(form, field)
            if extra:
                rv.update(extra)
            return rv
        return decorate
    return decorator


def basic_kwargs(field, exclude_keys=None):
    rv = {}
    if exclude_keys is None:
        exclude_keys = ()

    if 'help' not in exclude_keys and field.description:
        rv['help'] = field.description

    if 'default' not in exclude_keys and field.default is not None:
        rv['default'] = field.default
        if 'help_default' not in exclude_keys and 'help' in rv:
            if len(str(field.default).split()) > 1:
                fmt = '"%(default)s"'
            else:
                fmt = '%(default)s'
            rv['help'] += ' (default: %s)' % fmt

    default_text = field.name.replace('_', ' ').title()
    if 'metavar' not in exclude_keys and field.label.text != default_text:
        rv['metavar'] = field.label.text

    return rv


def decimal_type(value):
    try:
        return decimal.Decimal(value)
    except decimal.DecimalException:
        raise argparse.ArgumentTypeError("invalid decimal value: '%s'" % value)


def make_datetime_type(field):
    def datetime_type(value):
        try:
            dt = datetime.strptime(value, field.format)
        except ValueError as e:
            fmt = "invalid date/time value: '%s' (%s)"
            raise argparse.ArgumentTypeError(fmt % (value, e))
        if isinstance(field, DateTimeField):
            return dt
        if isinstance(field, DateField):
            return dt.date()
        if isinstance(field, TimeField):
            return dt.time()
        raise Exception('unreachable')
    return datetime_type


@basic_mapper(BooleanField, exclude_keys=['metavar'])
def boolean_kwargs(_, field):
    return dict(action='store_false' if field.default else 'store_true')


@basic_mapper(DateField)
def date_kwargs(_, field):
    return dict(type=make_datetime_type(field))


@basic_mapper(DateTimeField)
def datetime_kwargs(_, field):
    return dict(type=make_datetime_type(field))


@basic_mapper(DecimalField)
def decimal_kwargs(*_):
    return dict(type=decimal_type)


@basic_mapper(FloatField)
def float_kwargs(*_):
    return dict(type=float)


@basic_mapper(IntegerField)
def integer_kwargs(*_):
    return dict(type=int)


@basic_mapper(StringField)
def string_kwargs(*_):
    pass


@basic_mapper(TimeField)
def time_kwargs(_, field):
    return dict(type=make_datetime_type(field))


class UnsupportedFieldType(Exception):
    """Raised when configuring the parser for an unsupported field type."""

    def __init__(self, type, form, field):
        fmt = 'unsupported field type: %s'
        super(UnsupportedFieldType, self).__init__(fmt % type)
        self.type = type
        self.form = form
        self.field = field


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
            args +=  ('--%s' % field.name,)

            parser.add_argument(*args, **kwargs)

    def bind_args(self, args=None):
        if args is None:
            args = clik_args
        kwargs = self._clik_constructor_kwargs.copy()
        kwargs.update(dict(data=args))
        super(Form, self).__init__(**kwargs)

    def bind_and_validate(self, args=None):
        self.bind_args(args)
        return self.validate()
