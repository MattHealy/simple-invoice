from flask import render_template, flash, redirect, session, url_for, request, g, current_app, Response, abort, send_from_directory
from flask.ext.login import login_user, logout_user, current_user, login_required
from werkzeug import secure_filename
from datetime import datetime, timedelta
from decimal import Decimal
from . import main
from ..models import User, Client, Invoice, LineItem, Business
from .. import db, lm
from .forms import LoginForm, ClientForm, InvoiceForm, LineItemForm, ProfileForm, SettingsForm
import os

@main.route('/', methods=['GET'])
@login_required
def index():

    outstandinginvoices = Invoice.query.filter(Invoice.paid == False).filter(Invoice.duedate >= datetime.now())
    overdueinvoices = Invoice.query.filter(Invoice.paid == False).filter(Invoice.duedate < datetime.now())
    paidinvoices = Invoice.query.filter(Invoice.paid == True).filter(Invoice.invoicedate > (datetime.today() - timedelta(days=30)).date())

    outstanding = 0
    for invoice in outstandinginvoices:
        for lineitem in invoice.lineitems:
            outstanding+=(lineitem.units * lineitem.priceperunit)

    overdue = 0
    for invoice in overdueinvoices:
        for lineitem in invoice.lineitems:
            overdue+=(lineitem.units * lineitem.priceperunit)

    paid = 0
    for invoice in paidinvoices:
        for lineitem in invoice.lineitems:
            paid+=(lineitem.units * lineitem.priceperunit)

    return render_template("index.html",title='Home',outstanding=outstanding, overdue=overdue, paid=paid, \
                           overdueinvoices=overdueinvoices,outstandinginvoices=outstandinginvoices,paidinvoices=paidinvoices)

@main.route('/client/list', methods=['GET'])
@login_required
def clients():

    clients = Client.query.order_by(Client.insertdate.desc()).all()

    return render_template("clients.html",title='Clients',clients=clients)

@main.route('/client/add', methods=['GET','POST'])
@login_required
def add_client():

    form = ClientForm()

    if form.validate_on_submit():

        client = Client(name=form.name.data, contact_firstname = form.contact_firstname.data,
                        contact_lastname = form.contact_lastname.data,
                        contact_email = form.contact_email.data,
                        insertdate = datetime.utcnow(), website = form.website.data,
                        address_line1 = form.address_line1.data,
                        address_line2 = form.address_line2.data,
                        eftref = form.eftref.data,
                        abn = form.abn.data)

        db.session.add(client)
        db.session.commit()

        flash('Client added.')
        return redirect(url_for('main.view_client', client_id = client.id))

    return render_template("edit_client.html",title='Add Client',form=form)

@main.route('/client/<int:client_id>/edit', methods=['GET','POST'])
@login_required
def edit_client(client_id):

    form = ClientForm()

    if form.validate_on_submit():

        client = Client.query.filter_by(id = client_id).first_or_404()

        client.name = form.name.data
        client.contact_firstname = form.contact_firstname.data
        client.contact_lastname = form.contact_lastname.data
        client.contact_email = form.contact_email.data
        client.website = form.website.data
        client.address_line1 = form.address_line1.data
        client.address_line2 = form.address_line2.data
        client.eftref = form.eftref.data
        client.abn = form.abn.data

        db.session.add(client)
        db.session.commit()

        flash('Client updated.')

        return redirect(url_for('main.view_client', client_id = client.id))

    client = Client.query.filter_by(id = client_id).first_or_404()

    form.name.data = client.name
    form.contact_firstname.data = client.contact_firstname
    form.contact_lastname.data = client.contact_lastname
    form.contact_email.data = client.contact_email
    form.website.data = client.website
    form.client_id.data = client.id
    form.address_line1.data = client.address_line1
    form.address_line2.data = client.address_line2
    form.eftref.data = client.eftref
    form.abn.data = client.abn

    return render_template("edit_client.html",title='Edit Client',client=client,form=form)

@main.route('/client/<int:client_id>', methods=['GET'])
@login_required
def view_client(client_id):

    client = Client.query.get_or_404(client_id)

    return render_template("view_client.html",client=client,title=client.name)

@main.route('/client/<int:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):

    client = Client.query.get_or_404(client_id)

    if client.invoices.count() > 0:
        flash('Cannot delete client with invoices.')
        return redirect(url_for('main.edit_client', client_id = client.id))

    db.session.delete(client)
    db.session.commit()

    flash('Client removed.')
    return redirect(url_for('main.clients'))

@main.route('/invoice/<int:invoice_id>', methods=['GET'])
@login_required
def invoice(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)

    return render_template("invoice.html",title='Invoice #' + invoice.number, invoice=invoice, user=g.user)

@main.route('/client/<int:client_id>/invoice/add', methods=['GET','POST'])
@login_required
def add_invoice(client_id):

    client = Client.query.get_or_404(client_id)

    form = InvoiceForm()

    if form.validate_on_submit():

        invoicedate = datetime.strptime(form.invoicedate.data, "%d/%m/%Y").date()
        duedate = datetime.strptime(form.duedate.data, "%d/%m/%Y").date()

        invoice = Invoice(clientid=client.id, number = form.number.data, paid = False,
                        invoicedate = invoicedate, status = 'draft', duedate = duedate)

        db.session.add(invoice)
        db.session.commit()

        flash('Invoice added.')
        return redirect(url_for('main.edit_invoice', invoice_id = invoice.id))

    return render_template("add_invoice.html",title='Add Invoice',form=form, client=client)

@main.route('/invoice/<int:invoice_id>/finalise', methods=['POST'])
@login_required
def finalise_invoice(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.status = 'final'

    db.session.add(invoice)
    db.session.commit()

    flash('Invoice finalised.')
    return redirect(url_for('main.edit_invoice', invoice_id = invoice.id))

@main.route('/invoice/<int:invoice_id>/paid', methods=['POST'])
@login_required
def invoice_paid(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)
    invoice.paid = True

    db.session.add(invoice)
    db.session.commit()

    flash('Invoice marked as paid.')
    return redirect(url_for('main.edit_invoice', invoice_id = invoice.id))

@main.route('/invoice/<int:invoice_id>/lineitem/add', methods=['GET','POST'])
@login_required
def add_lineitem(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)

    form = LineItemForm()

    if form.validate_on_submit():

        priceperunit = Decimal(form.priceperunit.data.strip('$'))
        lineitem = LineItem(invoiceid = invoice.id, name = form.name.data,
                        priceperunit = priceperunit,
                        units = form.units.data)

        db.session.add(lineitem)
        db.session.commit()

        flash('Line Item added.')
        return redirect(url_for('main.edit_invoice', invoice_id = invoice.id))

    return render_template("add_lineitem.html",title='Add Line Item',form=form,invoice=invoice,client=invoice.client)

@main.route('/invoice/<int:invoice_id>/lineitem/<int:lineitem_id>/delete', methods=['POST'])
@login_required
def delete_lineitem(invoice_id,lineitem_id):

    invoice = Invoice.query.get_or_404(invoice_id)
    lineitem = LineItem.query.get_or_404(lineitem_id)

    if invoice.status == 'final':
        flash('Cannot remove item from finalised invoice.')
        return redirect(url_for('main.edit_invoice', invoice_id = invoice.id))

    db.session.delete(lineitem)
    db.session.commit()

    flash('Line Item removed.')
    return redirect(url_for('main.edit_invoice', invoice_id = invoice.id))

@main.route('/invoice/<int:invoice_id>/delete', methods=['POST'])
@login_required
def delete_invoice(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)
    client_id = invoice.client.id

    if invoice.status == 'final':
        flash('Cannot delete finalised invoices.')
        return redirect(url_for('main.edit_invoice', invoice_id = invoice.id))

    if invoice.lineitems:
        flash('Cannot delete invoices with line items.')
        return redirect(url_for('main.edit_invoice', invoice_id = invoice.id))

    db.session.delete(invoice)
    db.session.commit()

    flash('Invoice deleted.')
    return redirect(url_for('main.view_client', client_id = client_id))

@main.route('/invoice/<int:invoice_id>/edit', methods=['GET','POST'])
@login_required
def edit_invoice(invoice_id):

    invoice = Invoice.query.get_or_404(invoice_id)

    form = InvoiceForm()

    return render_template("edit_invoice.html",title='Invoice #' + invoice.number ,form=form, invoice=invoice,client=invoice.client)

@main.route('/invoices/all', methods=['GET'])
@login_required
def invoices():

    invoices = Invoice.query.order_by(Invoice.invoicedate.desc())

    return render_template("invoices.html",title='All Invoices',invoices=invoices)

@main.route('/invoices/outstanding', methods=['GET'])
@login_required
def outstanding_invoices():

    invoices = Invoice.query.filter(Invoice.paid == False).filter(Invoice.duedate>=datetime.now()).order_by(Invoice.invoicedate.desc())

    return render_template("invoices.html",title='Outstanding Invoices',invoices=invoices)

@main.route('/invoices/overdue', methods=['GET'])
@login_required
def overdue_invoices():

    invoices = Invoice.query.filter(Invoice.paid == False).filter(Invoice.duedate<datetime.now()).order_by(Invoice.invoicedate.desc())

    return render_template("invoices.html",title='Overdue Invoices',invoices=invoices)

@main.route('/invoices/paid', methods=['GET'])
@login_required
def paid_invoices():

    invoices = Invoice.query.filter(Invoice.paid == True).filter(Invoice.invoicedate > (datetime.today() - timedelta(days=30)).date())

    return render_template("invoices.html",title='Paid Invoices (last 30 days)',invoices=invoices)

@main.route('/profile/edit', methods=['GET','POST'])
@login_required
def edit_profile():

    user = g.user

    form = ProfileForm()

    if form.validate_on_submit():

        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.email = form.email.data

        db.session.add(user)
        db.session.commit()

        flash('Profile updated.')

        return redirect(url_for('main.index'))

    form.first_name.data = user.first_name
    form.last_name.data = user.last_name
    form.email.data = user.email

    return render_template("edit_profile.html",title='Edit Profile',user=user,form=form)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in current_app.config['ALLOWED_EXTENSIONS']

@main.route('/settings', methods=['GET','POST'])
@login_required
def settings():

    business = g.user.business

    form = SettingsForm()

    if form.validate_on_submit():

        if form.logo.data.filename:
            filename = secure_filename(form.logo.data.filename)
            form.logo.data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            business.logo = filename

        business.business_name = form.business_name.data
        business.abn = form.abn.data
        business.email = form.email.data
        business.phone = form.phone.data
        business.bsb = form.bsb.data
        business.accountnumber = form.accountnumber.data

        db.session.add(business)
        db.session.commit()

        flash('Settings updated.')

        return redirect(url_for('main.index'))

    form.business_name.data = business.business_name
    form.abn.data = business.abn
    form.email.data = business.email
    form.phone.data = business.phone
    form.bsb.data = business.bsb
    form.accountnumber.data = business.accountnumber

    return render_template("settings.html",title='Settings',business=business,form=form)

@main.route('/uploads/<filename>')
def show_upload(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'],filename)

@main.route('/login', methods=['GET','POST'])
def login():

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')

    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('main.index'))

    if request.args.get('next'):
        session['next_url'] = request.args.get('next')

    return render_template('login.html', form=form, title='Log In')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@main.route('/forgot', methods=['GET','POST'])
def forgot():
    return "Forgot"

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@main.before_request
def before_request():
    g.user = current_user
