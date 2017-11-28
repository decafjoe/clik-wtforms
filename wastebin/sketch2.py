#!.env/bin/python
from datetime import *
import sys
from clik import app
#from wtforms import *
from wtforms.validators import *
from clik_wtforms import *


class CommentForm(Form):
    short_arguments = dict(c='check')
    # check = SelectField(choices=('foo', 'bar', 'baz qux'), default='bar')
    # date = DateField(
    #     description='date of the comment',
    #     default=default(date.today, 'hai'),
    # )
    # datetime = DateTimeField(default=datetime.today)
    # decimal = DecimalField()
    # floating = FloatField()
    # integer = IntegerField()
    # string = StringField()
    name = StringField(description='name of commentor')
    comment = StringField(description='comment content')
    check = FieldList(StringField())


class RatingForm(Form):
    # private = BooleanField(description='rating should be private, not public')
    stars = IntegerField(
        label='NUMBER',
        default=5,
        description='customer rating measured in stars',
        validators=[NumberRange(min=1, max=5)],
    )
    comment = FormField(CommentForm)
    other_comment = FormField(CommentForm)
    yet_other_comment = FormField(CommentForm)


class FeedbackForm(Form):
    product = StringField(
        description='name of the product this feedback is for',
    )
    rating = FormField(RatingForm)
    other_rating = FormField(RatingForm)



@app
def sketch():
    # form = FeedbackForm()
    form = CommentForm()
    form.configure_parser()
    yield
    if not form.bind_and_validate():
        print('error: validation error(s) in arguments', file=sys.stderr)
        form.print_errors()
        yield 1
    from pprint import pprint; pprint(form.data)
    #from pprint import pprint; pprint(form.other_rating.form.yet_other_comment.form.comment.data)


if __name__ == '__main__':
    sketch.main()
