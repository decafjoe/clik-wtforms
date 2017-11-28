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
    FieldList, FloatField, Form as BaseForm, FormField, IntegerField, \
    StringField


mappers = {}


def mapper(cls):
    for type in cls.get_supported_types():
        mappers[type] = cls
    return cls


class Mapper(object):
    @staticmethod
    def get_supported_types():
        raise NotImplementedError

    @staticmethod
    def configure_parser(parser, short_arg, form, field):
        raise NotImplementedError

    @staticmethod
    def populate_formdata(formdata, args, form, field):
        raise NotImplementedError


# TODO(jjoyce): break out date-based fields into a separate mapper
#               that shows expected format in the help message
class SimpleFieldMapper(Mapper):
    @staticmethod
    def get_supported_types():
        return (
            DateField,
            DateTimeField,
            DecimalField,
            FloatField,
            IntegerField,
            StringField,
            # TimeField,
        )

    @staticmethod
    def configure_parser(parser, short_arg, _, field):
        args, kwargs = (), {}

        if short_arg is not None:
            args += ('-%s' % short_arg,)
        args +=  ('--%s' % field.name.replace('_', '-'),)

        if field.description:
            kwargs['help'] = field.description

        # TODO(jjoyce): consider default values from form.obj and
        #               form.data?
        # TODO(jjoyce): figure out what to do if default is a callable
        if field.default is not None:
            kwargs['default'] = field.default
            if 'help' in kwargs:
                kwargs['help'] += ' (default: %(default)s)'

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
        default_label_text = field.short_name.replace('_', ' ').title()
        if field.label.text != default_label_text:
            kwargs['metavar'] = field.label.text

        parser.add_argument(*args, **kwargs)

    @staticmethod
    def populate_formdata(formdata, args, _, field):
        key = field.name.replace('-', '_')  # not sure if this is necessary
        value = getattr(args, key, None)
        print(formdata, args, field)
        if value is not None:
            formdata[key] = value


class FormFieldMapper(Mapper):
    @staticmethod
    def get_supported_types():
        return (FormField,)

    @staticmethod
    def configure_parser(parser, short_arg, _, field):
        if short_arg is not None:
            pass  # TODO(jjoyce): raise exception, cannot specify a short
                  #               arg for a FormField
        field.form._configure_parser(parser, short_arguments=False)

    @staticmethod
    def populate_formdata(formdata, args, _, field):
        print(field.separator)
        for subfield in field.form:
            SimpleFieldMapper.populate_formdata(formdata, args, form, subfield)


# Can't do class decorators because Python 2.6.
mapper(FormFieldMapper)
mapper(SimpleFieldMapper)


class Multidict(dict):
    def __getitem__(self, key):
        value = dict.__getitem__(self, key)
        if isinstance(value, list):
            return value[0]
        return value

    def getlist(self, key):
        value = self[key]
        if not isinstance(value, list):
            return [value]
        return value


class Form(BaseForm):
    short_arguments = None

    @staticmethod
    def get_short_arguments():
        pass

    def __init__(self, obj=None, prefix='', meta=None, data=None, **kwargs):
        if 'formdata' in kwargs:
            pass  # TODO(jjoyce): raise exception, formdata argument
                  #               is not supported, use bind_args
        self._clik_constructor_kwargs = dict(
            data=data,
            kwargs=kwargs,
            meta=meta,
            obj=obj,
            prefix=prefix,
        )
        super(Form, self).__init__(**self._clik_constructor_kwargs)

    def _get_mapper(self, field):
        rv = mappers.get(type(field), None)
        if rv is None:
            raise UnsupportedFieldType(self, field)
        return rv

    def _configure_parser(self, parser, short_arguments=True):
        short_args = {}
        if short_arguments:
            for value in (self.short_arguments, self.get_short_arguments()):
                if value is not None:
                    short_args.update(value)
            short_args = dict((v, k) for k, v in iteritems(short_args))

        for field in self:
            if len(field.name) == 1:
                pass  # TODO(jjoyce): raise exception, names must be
                      #               two or more characters long
                      #               so as not to conflict with
                      #               short arguments
            mapper = self._get_mapper(field)
            short_arg = short_args.get(field.name, None)
            mapper.configure_parser(parser, short_arg, self, field)

    def configure_parser(self, parser=None):
        if parser is None:
            parser = clik_parser
        self._configure_parser(parser)

    def bind_args(self, args=None):
        if args is None:
            args = clik_args
        # TODO(jjoyce): figure out why ``_=None`` is necessary for
        #               making processed string field data consistent --
        #               without it, when the multidict is completely
        #               empty, string values come back as ``None``;
        #               with it, when the multidict is not empty (but
        #               still has no relevant field data) the string
        #               values come back as an empty string
        formdata = Multidict(_=None)
        for field in self:
            mapper = self._get_mapper(field)
            mapper.populate_formdata(formdata, args, self, field)
        kwargs = self._clik_constructor_kwargs.copy()
        kwargs.update(dict(formdata=formdata))
        super(Form, self).__init__(**kwargs)

    def bind_and_validate(self, args=None):
        self.bind_args(args)
        return self.validate()
