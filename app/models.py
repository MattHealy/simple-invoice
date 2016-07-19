from app import db
from flask import url_for, current_app, request
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime 

class Business(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(64))
    abn = db.Column(db.String(64))
    email = db.Column(db.String(64))
    phone = db.Column(db.String(64))
    logo = db.Column(db.String(255))
    bsb = db.Column(db.String(64))
    accountnumber = db.Column(db.String(64))
    users = db.relationship('User', lazy='dynamic', backref='business')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('business.id'))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    email = db.Column(db.String(64), index = True)
    password_hash = db.Column(db.String(128))

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return True

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r %r>' % (self.first_name, self.last_name)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    contact_firstname = db.Column(db.String(128))
    contact_lastname = db.Column(db.String(128))
    contact_email = db.Column(db.String(128))
    website = db.Column(db.String(255))
    insertdate = db.Column(db.DateTime)
    invoices = db.relationship('Invoice', lazy='dynamic', backref='client')
    address_line1 = db.Column(db.String(128))
    address_line2 = db.Column(db.String(128))
    eftref = db.Column(db.String(20))
    abn = db.Column(db.String(64))

    def __repr__(self):
        return '<Client %r>' % (self.name)

    @property
    def last_invoice_date(self):
        invoice = Invoice.query.filter_by(clientid = self.id).order_by(Invoice.invoicedate.desc()).first()
        if invoice:
            return invoice.invoicedate
        else:
            return None

    @property
    def status(self):

        for invoice in self.invoices:
            if not invoice.paid and invoice.duedate < datetime.now() and invoice.status=='final':
                return "Overdue"
            elif not invoice.paid and invoice.status=='final':
                return "Outstanding"

        return "Fully Paid"

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clientid = db.Column(db.Integer, db.ForeignKey('client.id'))
    number = db.Column(db.String(64), unique=True)
    invoicedate = db.Column(db.DateTime)
    duedate = db.Column(db.DateTime)
    status = db.Column(db.String(20))
    paid = db.Column(db.Boolean)
    lineitems = db.relationship('LineItem', lazy='joined')

    def sum_total(self):
        total=0
        for lineitem in self.lineitems:
            total+=(lineitem.priceperunit * lineitem.units)
        return total

class LineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoiceid = db.Column(db.Integer, db.ForeignKey('invoice.id'))
    name = db.Column(db.String(128))
    units = db.Column(db.Integer)
    priceperunit = db.Column(db.Float)
