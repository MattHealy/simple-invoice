from flask import g, current_app
from flask.ext.wtf import Form
from wtforms import TextField, HiddenField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Optional, Email
from flask_wtf.file import FileField, FileAllowed

class LoginForm(Form):
    email = TextField('email', validators=[Required(), Email()])
    password = PasswordField('password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class ClientForm(Form):
    client_id = HiddenField('client_id')
    name = TextField('name', validators=[Required()])
    contact_firstname = TextField('contact_firstname', validators=[Required()])
    contact_lastname = TextField('contact_lastname', validators=[Required()])
    contact_email = TextField('contact_email', validators=[Required(), Email()])
    website = TextField('website')
    address_line1 = TextField('address_line1')
    address_line2 = TextField('address_line2')
    eftref = TextField('eftref')
    abn = TextField('abn')
    submit = SubmitField('Submit')

class InvoiceForm(Form):
    invoice_id = HiddenField('invoice_id')
    client_id = HiddenField('client_id')
    number = TextField('number', validators=[Required()])
    invoicedate = TextField('invoicedate', validators=[Required()])
    duedate = TextField('duedate', validators=[Required()])
    submit = SubmitField('Submit')

class LineItemForm(Form):
    lineitem_id = HiddenField('lineitem_id')
    invoice_id = HiddenField('invoice_id')
    name = TextField('name', validators=[Required()])
    priceperunit = TextField('priceperunit', validators=[Required()])
    units = TextField('units', validators=[Required()])
    submit = SubmitField('Submit')

class ProfileForm(Form):
    first_name = TextField('first_name', validators=[Required()])
    last_name = TextField('last_name', validators=[Required()])
    email = TextField('email', validators=[Required(), Email()])

class SettingsForm(Form):
    business_name = TextField('business_name', validators=[Required()])
    abn = TextField('abn')
    email = TextField('email', validators=[Required(), Email()])
    phone = TextField('phone')
    logo = FileField('Your business logo', validators=[FileAllowed(['jpg','jpeg','png','gif'], 'Images only!')])
    bsb = TextField('bsb')
    accountnumber = TextField('accountnumber')
