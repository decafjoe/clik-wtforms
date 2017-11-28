#!.env/bin/python
import sys
from clik import app
from wtforms import *
from wtforms.validators import *
from clik_wtforms import Form


class CommentForm(Form):
    name = StringField()
    comment = StringField()


class TestingForm(Form):
    short_arguments = dict(
        i='integer',
        s='string',
    )

    @staticmethod
    def get_short_arguments():
        return dict(d='decimal', f='floating')

    comment = FormField(CommentForm)
    date = DateField()
    datetime = DateTimeField()
    decimal = DecimalField()
    floating = FloatField()
    integer = IntegerField()
    string = StringField()


@app
def sketch():
    form = TestingForm()
    form.configure_parser()
    yield
    if not form.bind_and_validate():
        print('error: validation error(s) in arguments', file=sys.stderr)
        for field in form:
            for error in field.errors:
                msg = '%s: %s' % (field.name.replace('_', '-'), error)
                print(msg, file=sys.stderr)
        yield 1
    print('   comment name: %s' % repr(form.comment.form.name.data))
    print('comment comment: %s' % repr(form.comment.form.comment.data))
    print('           date: %s' % repr(form.date.data))
    print('       datetime: %s' % repr(form.datetime.data))
    print('        decimal: %s' % repr(form.decimal.data))
    print('       floating: %s' % repr(form.floating.data))
    print('        integer: %s' % repr(form.integer.data))
    print('         string: %s' % repr(form.string.data))


if __name__ == '__main__':
    sketch.main()
