# -*- coding: utf-8 -*-
"""
Tests for :mod:`clik_wtforms`.

:author: Joe Joyce <joe@decafjoe.com>
:copyright: Copyright (c) Joe Joyce and contributors, 2017-2019.
:license: BSD
"""
import datetime
import decimal
import io

import pytest
from clik.argparse import ArgumentParser
from clik.util import AttributeDict
from wtforms import SubmitField
from wtforms.validators import InputRequired, Optional

from clik_wtforms import DateField, DateTimeField, DecimalField, default, \
    FieldList, FloatField, Form, FormError, FormField, IntegerField, \
    Multidict, SelectField, SelectMultipleField, StringField


class Argument(object):
    """Represents argument data, as parsed from a ``--help`` message."""

    def __init__(self, name):
        """
        Instantiate the object.

        :param str name: Name of the argument
        """
        self.help = ''
        self.metavar = None
        self.name = name
        self.short_name = None

    def assert_choices(self, choices):
        """Assert choices string is in help message."""
        self.assert_in_help('choices: %s' % choices)

    def assert_datetime_example(self, example):
        """Assert datetime example is in help message."""
        self.assert_in_help('example: %s' % example)

    def assert_datetime_format(self, format):
        """Assert datetime format instructions are in help message."""
        self.assert_in_help('format: %s' % format)

    def assert_default(self, value):
        """Assert default value is in help message."""
        self.assert_in_help('default: %s' % value)

    def assert_in_help(self, text):
        """Assert ``text`` is in help message."""
        assert text in self.help

    def assert_metavar(self, metavar):
        """Assert metavar for this argument is ``metavar``."""
        assert metavar == self.metavar

    def assert_multiple(self):
        """Assert help message says argument can be supplied multiple times."""
        self.assert_in_help('may be supplied multiple times')

    def assert_short_name(self, short_name):
        """Assert short name for this argument."""
        assert short_name == self.short_name


class Harness(AttributeDict):
    """
    Test harness for clik-wtforms.

    This "runs" the program with ``--help`` to get the configured arguments,
    which are made available as the keys on the harness object. See
    :class:`Argument` for how these are used.

    This can also simulate user input and the resulting form data via the
    :meth:`result_for`.
    """

    def __init__(self, form_class, **kwargs):
        """
        Instantiate the harness.

        :param type form_class: Form class under test
        :param kwargs: Keyword arguments to pass to the form class constructor
                       when gathering the arguments from the help message
        """
        self.form_class = form_class
        self.parser = ArgumentParser()
        cpkwargs = {}
        if 'configure_parser_kwargs' in kwargs:
            cpkwargs = kwargs['configure_parser_kwargs']
            del kwargs['configure_parser_kwargs']
        self.form_class(**kwargs).configure_parser(self.parser, **cpkwargs)

        current_arg = None
        for line in self.parser.format_help().splitlines():
            line = line.strip()
            if line.startswith('-'):
                bits = line.split('  ', 1)
                arg_bits = bits[0].split(',')
                long_arg_bits = arg_bits[-1].strip().split()
                name = long_arg_bits[0][2:]
                current_arg = Argument(name)
                self[name] = current_arg
                if len(arg_bits) > 1:
                    current_arg.short_name = arg_bits[0].strip().split()[0][1:]
                if len(long_arg_bits) > 1:
                    current_arg.metavar = long_arg_bits[1]
                if len(bits) > 1:
                    current_arg.help += bits[1].strip()
            elif current_arg:
                current_arg.help += ' %s' % line

    def result_for(self, *argv, **kwargs):
        """
        Return form result from "calling the program" with given ``argv``.

        :param argv: Arguments to pass to the parser
        :type argv: Sequence
        :param kwargs: Keyword arguments to pass to the form class constructor
        :return: :attr:`wtforms.form.Form.data` after binding and validation
        :rtype: :class:`dict`
        """
        form = self.form_class(**kwargs)
        assert form.bind_and_validate(self.parser.parse_args(argv))
        return form.data


def test_default_wrapper():
    """Check that default wrapper is transparent except __clik_wtf__."""
    def myfn():
        """Generate a default."""
        return 42

    wrapped = default(myfn, 'some default value')
    assert wrapped() == 42
    assert wrapped.__doc__ == 'Generate a default.'
    assert wrapped.__clik_wtf__ == 'some default value'


def test_metavar_kwarg():
    """Check that fields accept metavar kwarg and store on the instance."""
    test_types = (
        DateField,
        DateTimeField,
        DecimalField,
        FieldList,
        FloatField,
        IntegerField,
        SelectField,
        SelectMultipleField,
        StringField,
    )

    class MyForm(Form):
        pass
    for field_type in test_types:
        if field_type == FieldList:
            field = field_type(StringField(), metavar='FOO')
        else:
            field = field_type(metavar='FOO')
        setattr(MyForm, field_type.__name__.lower(), field)
    form = MyForm()
    for field_type in test_types:
        assert getattr(form, field_type.__name__.lower()).metavar == 'FOO'


def test_select_choices():
    """Check that choices for select fields get mapped correctly."""
    choices_in = ('foo', 'bar', 'baz')
    choices_out = [('foo', 'foo'), ('bar', 'bar'), ('baz', 'baz')]

    class MyForm(Form):
        select = SelectField(choices=choices_in)
        selectm = SelectMultipleField(choices=choices_in)

    form = MyForm()
    assert form.select.choices == choices_out
    assert form.selectm.choices == choices_out


def test_select_required():
    """Check that required/optional for selects is handled correctly."""
    class MyForm(Form):
        s_exp = SelectField(validators=[Optional()])
        s_opt = SelectField()
        s_req = SelectField(validators=[InputRequired()])
        sm_exp = SelectMultipleField(validators=[Optional()])
        sm_opt = SelectMultipleField()
        sm_req = SelectMultipleField(validators=[InputRequired()])
    form = MyForm()

    def assert_optional(field):
        assert any(isinstance(v, Optional) for v in field.validators)
        assert not any(isinstance(v, InputRequired) for v in field.validators)

    def assert_required(field):
        assert not any(isinstance(v, Optional) for v in field.validators)
        assert any(isinstance(v, InputRequired) for v in field.validators)

    assert_optional(form.s_exp)
    assert_optional(form.s_opt)
    assert_required(form.s_req)

    assert_optional(form.sm_exp)
    assert_optional(form.sm_opt)
    assert_required(form.sm_req)


def test_multidict():
    """Check that multidict data structure behaves correctly."""
    d = Multidict(a='foo', b=['bar', 'baz'])
    assert isinstance(d, dict)
    assert d['a'] == 'foo'
    assert d['b'] == 'bar'
    assert d.getlist('a') == ['foo']
    assert d.getlist('b') == ['bar', 'baz']


@pytest.mark.parametrize('field_type,default,default_str,value,value_str', [
    (
        DateField,
        datetime.date(2016, 11, 27),
        '2016-11-27',
        datetime.date(2018, 7, 22),
        '2018-07-22',
    ),
    (
        DateTimeField,
        datetime.datetime(2016, 11, 27, 12, 22, 42),
        '"2016-11-27 12:22:42"',
        datetime.datetime(2018, 7, 22, 18, 16, 14),
        '2018-07-22 18:16:14',
    ),
    (
        DecimalField,
        decimal.Decimal('7.42'),
        '7.42',
        decimal.Decimal('42.7'),
        '42.7',
    ),
    (FloatField, 7.42, '7.42', 42.7, '42.7'),
    (IntegerField, 7, '7', 42, '42'),
    (StringField, 'foo', 'foo', 'bar', 'bar'),
])
def test_field_basics(field_type, default, default_str, value, value_str):
    """Check basics for fields: defaults, descriptions, metavars."""
    class MyForm(Form):
        all = field_type(
            default=default,
            description='a helping message',
            metavar='FOO',
        )
        bare = field_type()
        desc = field_type(description='another help message')
        val = field_type(default=default)
        var = field_type(metavar='FOO')

    harness = Harness(MyForm)

    def assert_arg(name, default, text, metavar):
        assert name in harness
        arg = harness[name]
        arg.assert_in_help(text)
        arg.assert_metavar(metavar)
        arg.assert_short_name(None)
        if default is not None:
            arg.assert_default(default)

    assert_arg('all', default_str, 'a helping message', 'FOO')
    assert_arg('bare', None, '', 'BARE')
    assert_arg('desc', None, 'another help message', 'DESC')
    assert_arg('val', default_str, '', 'VAL')
    assert_arg('var', None, '', 'FOO')

    expected = dict(all=default, bare=None, desc=None, val=default, var=None)
    assert harness.result_for() == expected

    argv, expected = [], {}
    for key in ('all', 'bare', 'desc', 'val', 'var'):
        argv.append('--%s=%s' % (key, value_str))
        expected[key] = value
    assert harness.result_for(*argv) == expected


@pytest.mark.parametrize(
    'field_type'
    ',default_format'
    ',default_example'
    ',custom_format'
    ',custom_example'
    ',value'
    ',default_string'
    ',custom_string', [
        (
            DateField,
            '%Y-%m-%d',
            '2017-11-27',
            '%Y%m%d',
            '20171127',
            datetime.date(2018, 7, 22),
            '2018-07-22',
            '20180722',
        ),
        (
            DateTimeField,
            '"%Y-%m-%d %H:%M:%S"',
            '"2017-11-27 13:52:41"',
            '%Y%m%d%H%M%S',
            '20171127135241',
            datetime.datetime(2018, 7, 22, 18, 16, 14),
            '2018-07-22 18:16:14',
            '20180722181614',
        ),
    ])
def test_datetime_fields(field_type, default_format, default_example,
                         custom_format, custom_example, value, default_string,
                         custom_string):
    """Check format handling for date/time based fields."""
    class MyForm(Form):
        custom = field_type(format=custom_format)
        default = field_type()

    harness = Harness(MyForm)

    assert 'custom' in harness
    harness.custom.assert_datetime_format(custom_format)
    harness.custom.assert_datetime_example(custom_example)

    assert 'default' in harness
    harness.default.assert_datetime_format(default_format)
    harness.default.assert_datetime_example(default_example)

    args = ('--custom', custom_string, '--default', default_string)
    assert harness.result_for(*args) == dict(custom=value, default=value)


def test_select_fields():
    """Check configuration and data handling for select fields."""
    choices = ('foo', 'bar', 'baz qux')
    choices_str = 'foo, bar, "baz qux"'

    class MyForm(Form):
        default = SelectField(choices=choices, default='foo')
        invalid = SelectField(choices=choices, coerce=int, default='foo')
        multiple = SelectMultipleField(choices=choices)
        single = SelectField(choices=choices)

    harness = Harness(MyForm)

    assert 'default' in harness
    harness.default.assert_choices(choices_str)
    harness.default.assert_default('foo')

    assert 'invalid' in harness
    harness.invalid.assert_choices(choices_str)
    harness.invalid.assert_default('foo')

    assert 'multiple' in harness
    harness.multiple.assert_choices(choices_str)
    harness.multiple.assert_multiple()

    assert 'single' in harness
    harness.single.assert_choices(choices_str)

    expected = dict(default='foo', invalid=None, multiple=[], single=None)
    assert harness.result_for() == expected

    args = ('--single=foo', '--single=bar', '--multiple=foo', '--multiple=bar')
    result = harness.result_for(*args)
    assert 'default' in result
    assert result['default'] == 'foo'
    assert 'invalid' in result
    assert result['invalid'] is None
    assert 'multiple' in result
    assert isinstance(result['multiple'], list)
    assert set(result['multiple']) == set(('foo', 'bar'))
    assert 'single' in result
    assert result['single'] == 'bar'


@pytest.mark.parametrize('field_type,value_strs,values', [
    (
        DateField,
        ('2018-07-22', '2016-05-27'),
        (datetime.date(2018, 7, 22), datetime.date(2016, 5, 27)),
    ),
    (
        DateTimeField,
        ('2018-07-22 17:42:07', '2016-05-27 09:12:29'),
        (
            datetime.datetime(2018, 7, 22, 17, 42, 7),
            datetime.datetime(2016, 5, 27, 9, 12, 29),
        ),
    ),
    (
        DecimalField,
        ('42.7', '7.42'),
        (decimal.Decimal('42.7'), decimal.Decimal('7.42')),
    ),
    (FloatField, ('42.7', '7.42'), (42.7, 7.42)),
    (IntegerField, ('42', '7'), (42, 7)),
    (StringField, ('foo', 'bar'), ('foo', 'bar')),
])
def test_field_list(field_type, value_strs, values):
    """Check behavior of field lists."""
    class MyForm(Form):
        value = FieldList(field_type())

    harness = Harness(MyForm)

    assert 'value' in harness
    harness.value.assert_multiple()

    assert harness.result_for() == dict(value=[])

    args = []
    for value_str in value_strs:
        args.extend(('--value', value_str))
    assert harness.result_for(*args) == dict(value=list(values))


def test_form_field():
    """
    Very ugly test for form fields.

    This test tries to be as "mean" as possible, with multiply-nested forms
    and lots of underscores. The idea is to stress the form data translation
    bits of the code.
    """
    class GrandchildForm(Form):
        value = StringField()

    class ChildForm(Form):
        aaa = FormField(GrandchildForm)
        b_bb = FormField(GrandchildForm)
        c_c_c = FormField(GrandchildForm)

    class ParentForm(Form):
        xxx = FormField(ChildForm)
        y_yy = FormField(ChildForm)
        z_z_z = FormField(ChildForm)

    harness = Harness(ParentForm)
    assert 'xxx-aaa-value' in harness
    assert 'xxx-b-bb-value' in harness
    assert 'xxx-c-c-c-value' in harness
    assert 'y-yy-aaa-value' in harness
    assert 'y-yy-b-bb-value' in harness
    assert 'y-yy-c-c-c-value' in harness
    assert 'z-z-z-aaa-value' in harness
    assert 'z-z-z-b-bb-value' in harness
    assert 'z-z-z-c-c-c-value' in harness

    assert harness.result_for() == dict(
        xxx=dict(
            aaa=dict(value=None),
            b_bb=dict(value=None),
            c_c_c=dict(value=None),
        ),
        y_yy=dict(
            aaa=dict(value=None),
            b_bb=dict(value=None),
            c_c_c=dict(value=None),
        ),
        z_z_z=dict(
            aaa=dict(value=None),
            b_bb=dict(value=None),
            c_c_c=dict(value=None),
        ),
    )

    args = (
        '--xxx-aaa-value', 'xa',
        '--xxx-b-bb-value', 'xb',
        '--xxx-c-c-c-value', 'xc',
        '--y-yy-aaa-value', 'ya',
        '--y-yy-b-bb-value', 'yb',
        '--y-yy-c-c-c-value', 'yc',
        '--z-z-z-aaa-value', 'za',
        '--z-z-z-b-bb-value', 'zb',
        '--z-z-z-c-c-c-value', 'zc',
    )
    assert harness.result_for(*args) == dict(
        xxx=dict(
            aaa=dict(value='xa'),
            b_bb=dict(value='xb'),
            c_c_c=dict(value='xc'),
        ),
        y_yy=dict(
            aaa=dict(value='ya'),
            b_bb=dict(value='yb'),
            c_c_c=dict(value='yc'),
        ),
        z_z_z=dict(
            aaa=dict(value='za'),
            b_bb=dict(value='zb'),
            c_c_c=dict(value='zc'),
        ),
    )


def test_exclude_fields():
    """Check that excluded fields are not configured in the parser."""
    class MyForm(Form):
        value = StringField()

    harness = Harness(MyForm, configure_parser_kwargs=dict(exclude=['value']))
    assert 'value' not in harness


def test_defaults():
    """Check that defaults handling and precedence works as expected."""
    class MyForm(Form):
        value = StringField()

    class Object(object):
        value = 'foo'

    obj = Object()
    # kwargs = dict(value='bar')
    data = dict(value='baz')

    def assert_default(default, **kwargs):
        harness = Harness(MyForm, **kwargs)
        assert 'value' in harness
        harness.value.assert_default(default)

    assert_default('foo', obj=obj)
    # assert_default('bar', **kwargs)
    assert_default('baz', data=data)

    # assert_default('foo', obj=obj, **kwargs)
    assert_default('foo', obj=obj, data=data)
    # assert_default('bar', data=data, **kwargs)

    # assert_default('foo', obj=obj, data=data, **kwargs)

    harness = Harness(MyForm)
    assert harness.result_for() == dict(value=None)
    assert harness.result_for(obj=obj) == dict(value='foo')
    # assert harness.result_for(**kwargs) == dict(value='bar')
    assert harness.result_for(data=data) == dict(value='baz')


def test_callable_default():
    """Check default value help output for callable defaults."""
    class MyForm(Form):
        common = DateTimeField(default=datetime.datetime.today)
        specified = StringField(default=default(lambda: 'bar', 'always bar'))
        unknown = StringField(default=lambda: 'foo')

    harness = Harness(MyForm)

    assert 'common' in harness
    harness.common.assert_default('now')

    assert 'specified' in harness
    harness.specified.assert_default('always bar')

    assert 'unknown' in harness
    harness.unknown.assert_default('dynamic')


def test_short_arguments():
    """Check that short arguments are merged and assigned correctly."""
    class MyForm(Form):
        short_arguments = dict(a='alpha', b='bravo', c='echo')

        @staticmethod
        def get_short_arguments():
            return dict(c='charlie', d='delta')

        alpha = StringField()
        bravo = StringField()
        charlie = StringField()
        delta = StringField()

    harness = Harness(MyForm)
    for name in ('alpha', 'bravo', 'charlie', 'delta'):
        assert name in harness
        harness[name].assert_short_name(name[0])

    expected = dict(alpha=None, bravo=None, charlie=None, delta=None)
    assert harness.result_for() == expected

    args = ('-aecho', '-bgolf', '-ckilo', '-dlima')
    expected = dict(alpha='echo', bravo='golf', charlie='kilo', delta='lima')
    assert harness.result_for(*args) == expected


def test_short_argument_form_field():
    """Check that short arguments cannot be assigned to a ``FormField``."""
    class ChildForm(Form):
        value = StringField()

    class ParentForm(Form):
        short_arguments = dict(c='child')
        child = FormField(ChildForm)

    with pytest.raises(FormError) as ei:
        Harness(ParentForm)
    e = ei.value
    assert 'cannot assign a short argument to a FormField' in str(e)


def test_single_character_field_name():
    """Check that single-character field names are disallowed."""
    class MyForm(Form):
        a = StringField()

    with pytest.raises(FormError) as ei:
        Harness(MyForm)
    e = ei.value
    assert 'field names must be at least two characters' in str(e)


def test_unsupported_field_type():
    """Check that using an unsupported field type raises an exception."""
    class MyForm(Form):
        submit = SubmitField()

    with pytest.raises(FormError) as ei:
        Harness(MyForm)
    e = ei.value
    assert 'unsupported field type' in str(e)
    assert 'wtforms.fields.simple.SubmitField' in str(e)


def test_print_errors():
    """Check the output of :meth:`clik_wtforms.Form.print_errors`."""
    class ChildForm(Form):
        value = SelectField(choices=())

    class ParentForm(Form):
        child = FormField(ChildForm)
        multiple = SelectMultipleField(choices=())
        number = IntegerField()

    parser = ArgumentParser()
    form = ParentForm()
    form.configure_parser(parser)
    args = parser.parse_args((
        '--child-value', 'foo',
        '--multiple', 'bar',
        '--number', 'baz',
    ))
    assert not form.bind_and_validate(args)
    string_io = io.StringIO()
    form.print_errors(string_io)
    expected_lines = (
        'child-value: foo: not a valid choice',
        "multiple: 'bar' is not a valid choice for this field",
        'number: baz: not a valid integer value',
    )
    assert string_io.getvalue() == '%s\n' % '\n'.join(expected_lines)
