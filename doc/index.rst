
==============
 clik-wtforms
==============

clik-wtforms adapts WTForms_ for use on the command line. WTForms
provides a pattern for organizing user-input-handling code and a rich
set of field types and built-in validators. Those facilities are
increasingly useful as a set of user inputs grows past a handful of
fields with simple validation rules.

clik-wtforms is easy to integrate into clik_ applications. Here's an
example::

  from clik import app
  from clik_wtforms import Form
  from wtforms import BooleanField, IntegerField, StringField
  from wtforms.validators import NumberRange


  class RatingForm(Form):
      comment = StringField(description='optional comment for rating')
      public = BooleanField(default=False, description='make rating public')
      stars = IntegerField(
          description='rating, 1 to 5',
          validators=[NumberRange(min=1, max=5, 'rating must be 1 to 5')],
      )


  @app
  def myapp():
      """Example application to show basic clik-wtforms flow."""
      form = RatingForm()
      form.configure_parser()
      yield
      if not form.bind_and_validate():
          # do stuff with form.errors
          yield 1
      # do stuff with form data

.. toctree::
   :maxdepth: 2

   changelog
