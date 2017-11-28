# -*- coding: utf-8 -*-
"""
Tests for :mod:`clik_wtforms`.

:author: Joe Joyce <joe@decafjoe.com>
:copyright: Copyright (c) Joe Joyce and contributors, 2017.
:license: BSD
"""
import datetime
import decimal

import pytest
from clik.argparse import ArgumentParser
from clik.util import AttributeDict
from wtforms.validators import Optional, Required

from clik_wtforms import default, DateField, DateTimeField, DecimalField, \
    FieldList, FloatField, Form, FormField, Multidict, IntegerField, \
    SelectField, SelectMultipleField, StringField


# TODO(jjoyce): test defaults by passing different kwargs to ctor and
#               seeing what data it spits out (compare to wtforms
#               proper?)


class Argument(object):
    def __init__(self, name):
        self.help = ''
        self.metavar = None
        self.name = name

    def assert_choices(self, choices):
        self.assert_in_help('choices: %s' % choices)

    def assert_datetime_example(self, example):
        self.assert_in_help('example: %s' % example)

    def assert_datetime_format(self, format):
        self.assert_in_help('format: %s' % format)

    def assert_default(self, value):
        self.assert_in_help('default: %s' % value)

    def assert_in_help(self, text):
        assert text in self.help

    def assert_metavar(self, metavar):
        assert metavar == self.metavar

    def assert_multiple(self):
        self.assert_in_help('may be supplied multiple times')


class Harness(AttributeDict):
    def __init__(self, form_class):
        self.form_class = form_class
        self.parser = ArgumentParser()
        self.form_class().configure_parser(self.parser)

        current_arg = None
        for line in self.parser.format_help().splitlines():
            line = line.strip()
            if line.startswith('-'):
                bits = line.split('  ', 1)
                long_arg_bits = bits[0].split(',')[-1].strip().split()
                current_arg = long_arg_bits[0][2:]
                self[current_arg] = Argument(current_arg)
                if len(long_arg_bits) > 1:
                    self[current_arg].metavar = long_arg_bits[1]
                if len(bits) > 1:
                    self[current_arg].help += bits[1].strip()
            elif current_arg:
                self[current_arg].help += ' %s' % line

    def result_for(self, *argv):
        form = self.form_class()
        form.bind_and_validate(self.parser.parse_args(argv))
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
        s_req = SelectField(validators=[Required()])
        sm_exp = SelectMultipleField(validators=[Optional()])
        sm_opt = SelectMultipleField()
        sm_req = SelectMultipleField(validators=[Required()])
    form = MyForm()

    def assert_optional(field):
        assert any(isinstance(v, Optional) for v in field.validators)
        assert not any(isinstance(v, Required) for v in field.validators)

    def assert_required(field):
        assert not any(isinstance(v, Optional) for v in field.validators)
        assert any(isinstance(v, Required) for v in field.validators)

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
        harness[name].assert_in_help(text)
        harness[name].assert_metavar(metavar)
        if default is not None:
            harness[name].assert_default(default)

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
    assert result['invalid'] == None
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
