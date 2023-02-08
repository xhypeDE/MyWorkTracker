"""Minimale Flask Anwendung"""

# Import benötigter Flask-Module
import ast
import mysql.connector
from passlib.hash import pbkdf2_sha256  # pylint: disable=import-error
from flask import Flask, session, render_template, g, request, redirect, url_for
from flask_mail import Mail, Message
from registration_modules import registration_error_check, gen_verification_code, \
    register_group, fetch_o_id_invite, fetch_o_id_create
from time_modules import calc_elapsed, start_tracking, stop_tracking, pause_tracking, \
    resume_tracking, save_tracking_data, seconds_to_string, \
    delete_time_entry, month_list, gen_month_filter
from statistic_modules import predicted_cost, actual_cost, user_counter

# Import der Verbindungsinformationen zur Datenbank:
# Variable DB_HOST: Servername des MySQL-Servers
# Variable DB_USER: Nutzername
# Variable DB_PASSWORD: Passwort
# Variable DB_DATABASE: Datenbankname
from db.db_credentials import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE
from cfg.cfg_hidden import SECRET_KEY, MAIL_SERVER, MAIL_PORT, MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER


app = Flask(__name__)

# Config für den Mailversand
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER
mail = Mail(app)

# Secret Key zur Nutzung von Session erstellt
app.secret_key = SECRET_KEY

# Debug Modus aktiviert
app.debug = True


def send_message(subject, recipient, body):
    """Funktion zum Versand von E-Mails"""
    # Eine Nachricht erstellen mit Titel und Empfänger
    msg = Message(subject, recipients=recipient)
    # Inhalt der Nachricht definieren
    msg.body = body
    # Nachricht als E-Mail versenden
    mail.send(msg)


@app.before_request
def before_request():
    """Datenbankverbindung herstellen"""
    g.con = mysql.connector.connect(host=DB_HOST,  # pylint: disable=assigning-non-slot
                                    user=DB_USER,
                                    password=DB_PASSWORD,
                                    database=DB_DATABASE)


@app.teardown_request
def teardown_request(exception):  # pylint: disable=unused-argument
    """Datenbankverbindung trennen"""
    con = getattr(g, 'con', None)
    if con is not None:
        con.close()


@app.route('/')
def index():
    """Startseite"""
    # Es wird überprüft ob der Nutzer eingeloggt ist um die Navbar Buttons
    # dementsprechend anzupassen.
    access_to_dashboard = False
    if session.get('logged_in'):
        access_to_dashboard = True
    return render_template('index.html', access_to_dashboard=access_to_dashboard)


@app.route('/dashboard')
def user_dashboard():
    """Dashboardseite"""
    # Es wird über die session geprüft ob der Benutzer eingeloggt ist.
    # Falls der Benutzer nicht eingeloggt ist wird er auf
    # die Login Seite weitergeleitet.

    if not session.get('logged_in'):
        return redirect('login')

    admin_level = session['admin_level']
    message = request.args.get('message')
    # Berechnung der Finanzstatistiken für die Gruppe des Admins,
    # damit diese Werte auf der Dashboard Seite angezeigt werden
    if admin_level == 2:
        cost_prediction = predicted_cost(session['o_id'])
        financial_stats = actual_cost(session['o_id'], admin_level)
        realtime_cost = financial_stats['realtime_cost']
        realtime_hours = financial_stats['realtime_hours']
        all_users_count = user_counter(session['o_id'], admin_level, "any")
        active_users_count = user_counter(session['o_id'], admin_level, "active")
    elif admin_level == 3:
        all_users_count = user_counter(session['o_id'], admin_level, "any")
        active_users_count = user_counter(session['o_id'], admin_level, "active")
        cost_prediction = None
        financial_stats = None
        realtime_hours = None
        realtime_cost = None
    else:
        cost_prediction = None
        financial_stats = None
        realtime_hours = None
        realtime_cost = None
        all_users_count = None
        active_users_count = None

    return render_template('dashboard.html', admin_level=admin_level,
                           current_page="dashboard",
                           cost_prediction=cost_prediction,
                           realtime_cost=realtime_cost,
                           realtime_hours=realtime_hours,
                           all_users_count=all_users_count,
                           active_users_count=active_users_count,
                           message=message)


@app.route('/account')
def user_dashboard_account():
    """Accountseite"""
    if not session.get('logged_in'):
        return redirect('login')
    admin_level = session['admin_level']
    fetched_id = session['u_id']
    # Abrufen der aktuellen Daten des Nutzers aus der Datenbank
    cur = g.con.cursor()
    cur.execute("SELECT u_ID, name, surname, phone, email, password, hourly_rate, admin_level, "
                "is_verified, workload FROM users WHERE u_ID = %s", (fetched_id,))
    user_original_data = cur.fetchall()
    cur.close()

    name = user_original_data[0][1]
    surname = user_original_data[0][2]
    phone = user_original_data[0][3]
    email = user_original_data[0][4]
    hourly_rate = user_original_data[0][6]
    workload = user_original_data[0][9]

    return render_template('account_edit.html', admin_level=admin_level,
                           current_page="account", name=name, surname=surname,
                           phone=phone, email=email, id=fetched_id,
                           hourly_rate=hourly_rate, workload=workload)


@app.route('/users', methods=['POST', 'GET'])
def users():
    """Benutzerverwaltungsseite"""
    admin_level = session.get('admin_level')
    if not session.get('logged_in') or admin_level < 2:
        return redirect('login')

    message = request.args.get('message')
    cur = g.con.cursor()
    current_page = "users"
    o_id = request.form.get('o_id')
    unternehmensname = request.form.get('unternehmensname')
    viewing_group = False
    if admin_level == 3:
        # Abrufen aller Nutzer in der Datenbank falls der Nutzer ein Masteradmin ist
        if request.method == 'POST':
            cur.execute("SELECT u_ID, name, surname, phone, email,"
                        "hourly_rate, admin_level, is_verified, "
                        "workload, status FROM"
                        " users WHERE u_ID != %s "
                        "AND o_ID = %s", (session['u_id'], request.form['o_id'],))
            current_page = "groups"
            viewing_group = True
        else:
            cur.execute("SELECT u_ID, name, surname, phone, email,"
                        "hourly_rate, admin_level, is_verified, "
                        "workload, status FROM "
                        "users WHERE u_ID != %s", (session['u_id'],))
    elif admin_level == 2:
        # Abrufen der Nutzer in der Gruppe des Admins aus der Datenbank
        cur.execute("SELECT u_ID, name, surname, phone, email,"
                    "hourly_rate, admin_level, is_verified, "
                    "workload, status FROM "
                    "users WHERE o_ID = %s AND u_ID != %s", (session['o_id'], session['u_id']))
    all_users = cur.fetchall()
    cur.close()
    user_count = len(all_users)

    return render_template('users.html', admin_level=admin_level, current_page=current_page,
                           user_count=user_count, all_users=all_users, message=message,
                           viewing_group=viewing_group, o_id=o_id,
                           unternehmensname=unternehmensname)


@app.route('/user_edit', methods=['POST', 'GET'])
def user_edit():
    """Einzelnen Nutzer verwalten"""
    if not session.get('logged_in'):
        return redirect('login')

    admin_level = session['admin_level']
    fetched_id = request.form['id']
    # Abfrage der aktuellen Daten des Nutzers von der Datenbank
    cur = g.con.cursor()
    cur.execute("SELECT u_ID, name, surname, phone, email, "
                "password, hourly_rate, admin_level, "
                "is_verified FROM users WHERE u_ID = %s", (fetched_id,))
    user_original_data = cur.fetchall()
    cur.close()

    if request.method == "POST" and request.form is not None:
        fetched_id = request.form['id']
        name = request.form['name']
        surname = request.form['surname']
        phone = request.form['phone']
        email = request.form['email']
        hourly_rate = request.form.get('hourly_rate', "NULL")
        workload = request.form.get('workload', "NULL")
        return render_template('user_edit.html', admin_level=admin_level,
                               current_page="users",
                               id=fetched_id, name=name, surname=surname, phone=phone,
                               email=email, admin_level_user=user_original_data[0][7],
                               hourly_rate=hourly_rate, workload=workload,
                               original_name=user_original_data[0][1],
                               original_surname=user_original_data[0][2])
    return None


@app.route('/push_user_edit', methods=['POST', 'GET'])
def push_user_edit():
    """Ausführen der Änderungen am Benutzer"""
    if not session.get('logged_in'):
        return redirect('login')
    admin_level = session['admin_level']
    fetched_id = request.form['id']
    user_data = {}

    if request.form['action'] == 'Konto schließen':
        cur = g.con.cursor()
        cur.execute("DELETE FROM users WHERE u_ID = %s", (fetched_id,))
        g.con.commit()
        cur.close()
        if request.form['origin'] == "self_update":
            return redirect(url_for('logout'))
        if request.form['origin'] == "foreign_update":
            return redirect(url_for('users', message="Benutzer erfolgreich gelöscht."))

    cur = g.con.cursor()
    cur.execute("SELECT u_ID, name, surname, phone, email, password, "
                "hourly_rate, admin_level, is_verified, workload FROM users "
                "WHERE u_ID = %s", (fetched_id,))
    user_original_data = cur.fetchall()
    cur.close()

    if request.form['origin'] == "self_update":
        user_admin_level = user_original_data[0][7]
        target_redirect = "account_edit.html"
        target_current_page = "account"
    else:
        target_redirect = "user_edit.html"
        user_admin_level = request.form['admin_level']
        target_current_page = "users"

    if admin_level == 1:
        user_hourly_rate = user_original_data[0][6]
        user_workload = user_original_data[0][9]
    else:
        user_hourly_rate = None
        user_workload = None

    if request.form.get('password') != "":
        # Speichert die Daten im Formular in einem Dictionary mit verändertem Passwort
        hashed_password = pbkdf2_sha256.hash(request.form['password'])
        user_data = {'name': request.form['name'],
                     'surname': request.form['surname'],
                     'phone': request.form['phone'],
                     'email': request.form['email'],
                     'hourly_rate': request.form.get('hourly_rate', user_hourly_rate),
                     'workload': request.form.get('workload', user_workload),
                     'pw_changed': True,
                     'password': request.form['password'],
                     'password_verify': request.form['password_verify'],
                     'hashed_password': hashed_password,
                     'admin_level': user_admin_level}
    elif request.form.get('password') == "":
        # Speichert die Daten im Formular in einem Dictionary ohne verändertes Passwort
        user_data = {'name': request.form['name'],
                     'surname': request.form['surname'],
                     'phone': request.form['phone'],
                     'email': request.form['email'],
                     'hourly_rate': request.form.get('hourly_rate', user_hourly_rate),
                     'workload': request.form.get('workload', user_workload),
                     'pw_changed': False,
                     'admin_level': user_admin_level}
    errors = registration_error_check(user_data, False)
    if errors[2] is True:
        cur = g.con.cursor()
        # Die Veränderungen an den Daten des Nutzers werden
        # in der Datenbank gespeichert.
        if user_data['pw_changed'] is True:
            cur.execute("UPDATE users SET name=%s, surname=%s, phone=%s, email=%s,"
                        "password=%s, admin_level=%s, hourly_rate=%s, "
                        "workload=%s WHERE u_ID=%s",
                        (user_data['name'], user_data['surname'], user_data['phone'],
                         user_data['email'], user_data['hashed_password'],
                         user_data['admin_level'], user_data['hourly_rate'],
                         user_data['workload'], fetched_id))
        else:
            cur.execute("UPDATE users SET name=%s, surname=%s, phone=%s, email=%s,"
                        "admin_level=%s, hourly_rate=%s, "
                        "workload=%s WHERE u_ID=%s",
                        (user_data['name'], user_data['surname'], user_data['phone'],
                         user_data['email'], user_data['admin_level'],
                         user_data['hourly_rate'], user_data['workload'], fetched_id))
        g.con.commit()
        cur.close()
        success_message = "Nutzerdaten erfolgreich aktualisiert."
        return render_template(target_redirect, admin_level=admin_level,
                               current_page=target_current_page,
                               name=user_data['name'], surname=user_data['surname'],
                               phone=user_data['phone'], id=fetched_id,
                               email=user_data['email'], workload=user_data['workload'],
                               hourly_rate=user_data['hourly_rate'],
                               admin_level_user=user_data['admin_level'],
                               success_message=success_message,
                               original_name=user_original_data[0][1],
                               original_surname=user_original_data[0][2])

    if errors[2] is not True:
        # Ausgabe der Fehlermeldung
        success_message = None
        return render_template(target_redirect, admin_level=admin_level,
                               current_page=target_current_page, name=user_data['name'],
                               surname=user_data['surname'], phone=user_data['phone'],
                               email=user_data['email'],
                               admin_level_user=user_data['admin_level'],
                               error_messages=errors[0], error_types=errors[1],
                               id=fetched_id, success_message=success_message,
                               original_name=user_original_data[0][1],
                               original_surname=user_original_data[0][2])
    return None


@app.route('/groups', methods=['POST', 'GET'])
def groups():
    """Gruppenverwaltungsseite"""
    admin_level = session['admin_level']
    if not session.get('logged_in') or admin_level < 2:
        return redirect('login')

    message = request.args.get('message')
    cur = g.con.cursor()
    if admin_level == 3:
        cur.execute("SELECT o_ID, o_name FROM o_groups")
    all_groups = cur.fetchall()
    cur.close()
    group_count = len(all_groups)

    return render_template('groups.html', admin_level=admin_level,
                           current_page="groups", all_groups=all_groups,
                           group_count=group_count, message=message)


@app.route('/delete_group', methods=['POST', 'GET'])
def delete_group():
    """Gruppe löschen"""
    admin_level = session['admin_level']
    if not session.get('logged_in') or admin_level < 2:
        return redirect('login')

    if request.method == "POST" and request.form is not None:
        cur = g.con.cursor()
        cur.execute("DELETE FROM o_groups WHERE o_ID=%s", (request.form['o_id'],))
        g.con.commit()
        cur.close()
        message = "Gruppe erfolgreich gelöscht!"
        return redirect(url_for('groups', message=message))

    return redirect(url_for('groups'))


@app.route('/invite')
def invite_page():
    """Einladungsseite"""
    admin_level = session['admin_level']
    if not session.get('logged_in') or admin_level < 2:
        return redirect('login')

    message_generate = request.args.get('message_generate')
    message_delete = request.args.get('message_delete')
    invite_code = request.args.get('invite_code')
    cur = g.con.cursor()
    cur.execute("SELECT invite_id, invite_code, invader_name, status, admin_level FROM "
                "o_invites WHERE invite_o_id = %s", (session['o_id'],))
    all_invites = cur.fetchall()
    cur.close()
    invite_count = len(all_invites)

    return render_template('invites.html', admin_level=admin_level,
                           current_page="invite_page",
                           message_generate=message_generate,
                           message_delete=message_delete,
                           invite_code=invite_code,
                           all_invites=all_invites, invite_count=invite_count)


@app.route('/create_invite', methods=['POST', 'GET'])
def create_invite():
    """Einladung erstellen"""
    admin_level = session['admin_level']
    if not session.get('logged_in') or admin_level < 2:
        return redirect('login')
    # Der Einladungscode wird generiert, gespeichert und dann ausgegeben
    if request.method == "POST" and request.form is not None:
        invite_code = gen_verification_code()
        invader = f"{session['name']} {session['surname']}"
        set_level = request.form['inv_type']

        cur = g.con.cursor()
        cur.execute("INSERT INTO o_invites (invite_code, invader_name, "
                    "status, admin_level, invite_o_id)"
                    " VALUES (%s, %s, %s, %s, %s)",
                    (invite_code, invader, 1,
                     set_level, session['o_id']))
        g.con.commit()
        cur.close()

        # Der Admin Level der Einladung wird anhand des gedrückten Buttons eingestellt
        if int(set_level) == 3:
            set_level_string = "Masteradmin"
        elif int(set_level) == 2:
            set_level_string = "Admin"
        else:
            set_level_string = "Mitarbeiter"

        message = f"Der Einladungscode lautet: {invite_code}. " \
                  f"Die Einladung ist nun aktiv mit Accesslevel: " \
                  f"{set_level_string}"
        return redirect(url_for('invite_page', message_generate=message,
                                invite_code=invite_code))

    return redirect(url_for('invite_page'))


@app.route('/delete_invite', methods=['POST', 'GET'])
def delete_invite():
    """Einladung löschen"""
    admin_level = session['admin_level']
    if not session.get('logged_in') or admin_level < 2:
        return redirect('login')

    if request.method == "POST" and request.form is not None:
        cur = g.con.cursor()
        cur.execute("DELETE FROM o_invites WHERE invite_id=%s",
                    (request.form['invite_id'],))
        g.con.commit()
        cur.close()
        message = "Einladung erfolgreich gelöscht!"
        return redirect(url_for('invite_page', message_delete=message, ))

    return redirect(url_for('invite_page'))


@app.route('/time', methods=['POST', 'GET'])
def working_time():
    """Zeiterfassungsseite"""

    if not session.get('logged_in'):
        return redirect('login')
    admin_level = session['admin_level']
    cur = g.con.cursor()
    # Es wird überprüft ob aktuell eine Zeiterfassung schon läuft
    cur.execute("SELECT date_a, pause, tracking, "
                "tracking_pause, pause_date_a, t_ID FROM time_entries "
                "WHERE (tracking=1 OR tracking_pause=1) AND u_ID=%s", (session['u_id'],))
    time_entry = cur.fetchall()
    cur.close()
    if time_entry:
        # Falls eine Zeiterfassung läuft werden hier die entsprechenden Daten
        # passend formatiert und in einem dictionary gespeichert.
        # Außerdem werden passende Aussagen zur aktuellen
        # Zeiterfassung erstellt und ausgegeben.
        if time_entry[0][0] is not None:
            converted_time = time_entry[0][0].strftime("%H:%M")
        else:
            converted_time = None
        if time_entry[0][4] is not None:
            converted_pause_time = time_entry[0][4].strftime("%H:%M")
        else:
            converted_pause_time = None
        fetched_time = {'t_id': time_entry[0][5],
                        'tracking': time_entry[0][2],
                        'tracking_pause': time_entry[0][3],
                        'converted_time': converted_time,
                        'converted_pause_time': converted_pause_time,
                        'date_a': time_entry[0][0],
                        'pause': time_entry[0][1],
                        'pause_date_a': time_entry[0][4],
                        }
        if fetched_time['tracking_pause']:
            time_pause_info = f"Sie haben die Pause " \
                              f"um {fetched_time['converted_pause_time']} gestartet."
            time_pause_passed = calc_elapsed(fetched_time['pause_date_a'], "Pause")
        else:
            time_pause_info = None
            time_pause_passed = None
        information = {'time_info': f"Sie haben die Zeiterfassung "
                                    f"um {fetched_time['converted_time']} gestartet.",
                       'time_track_passed': calc_elapsed(fetched_time['date_a'], "Zeiterfassung"),
                       'time_pause_info': time_pause_info,
                       'time_pause_passed': time_pause_passed}
    else:
        fetched_time = {}
        information = {}

    return render_template('time_track.html', admin_level=admin_level,
                           current_page="time_track",
                           time_entry=time_entry, information=information,
                           fetched_time=fetched_time, message=request.args.get('message'),
                           message_save=request.args.get('message_save'))


@app.route('/tracktime', methods=['POST', 'GET'])
def track_time():
    """Zeiterfassungsfunktion"""
    if not session.get('logged_in'):
        return redirect('login')

    message = None
    message_save = None
    if request.method == "POST" and request.form is not None:
        if request.form['action'] == "start":
            message = start_tracking()
            set_status("tracking", session['u_id'])
        if request.form['action'] == "stop" or request.form['action'] == "stop_during_pause":
            message = stop_tracking(request.form['t_id'], request.form['action'])
            set_status("online", session['u_id'])
        if request.form['action'] == "pause":
            message = pause_tracking(request.form['t_id'])
            set_status("pause", session['u_id'])
        if request.form['action'] == "resume":
            message = resume_tracking(request.form['t_id'])
            set_status("tracking", session['u_id'])
        if request.form['action'] == "save_input":
            message_save = save_tracking_data(request.form['start_time'],
                                              request.form['stop_time'],
                                              request.form['pause'],
                                              action="create")
    return redirect(url_for('working_time', message=message, message_save=message_save))


@app.route('/time_list', methods=['POST', 'GET'])
def time_list():
    """Verwaltung der eigenen Zeiteinträge"""
    if not session.get('logged_in'):
        return redirect('login')

    admin_level = session['admin_level']
    message = request.args.get('message', None)
    # Ein dictionary mit den letzten 12 Monaten und den entsprechenden
    # Filtern für die SQL Abfrage wird durch die Funktion generiert und
    # gespeichert
    filter_dict = gen_month_filter()
    cur = g.con.cursor()
    cur.execute("SELECT t_ID, date_a, date_b, pause, diff_time, actual_diff_time FROM "
                "time_entries WHERE u_ID = %s AND "
                "tracking=0 AND tracking_pause=0 "
                "AND date_a >= %s AND "
                "date_a < %s", (session['u_id'],
                                filter_dict['query_start'], filter_dict['query_end'],))

    db_time_entries = cur.fetchall()
    cur.close()
    entry_count = len(db_time_entries)
    output_entries = []

    # Die erfassten Zeiteinträge werden passend formatiert
    # und sequenziell in einer Liste gespeichert
    for i in range(entry_count):
        if db_time_entries[i][3] is not None:
            pause_in_minutes = db_time_entries[i][3] / 60
            pause_in_minutes = int(pause_in_minutes)
        else:
            pause_in_minutes = 0
        cache = [db_time_entries[i][0],
                 f"{db_time_entries[i][0]}XU{session['u_id']}XG{session['o_id']}",
                 db_time_entries[i][1].strftime("%d.%m.%Y %H:%M"),
                 db_time_entries[i][2].strftime("%d.%m.%Y %H:%M"),
                 seconds_to_string(db_time_entries[i][3]),
                 seconds_to_string(db_time_entries[i][4]),
                 seconds_to_string(db_time_entries[i][5]),
                 pause_in_minutes]
        output_entries.insert(i, cache)

    return render_template('time_list.html', admin_level=admin_level, current_page="time_list",
                           entry_count=entry_count, output_entries=output_entries,
                           message=message, month_option=filter_dict['month_option'],
                           selected_month=filter_dict['selected_month'])


@app.route('/time_list_group', methods=['POST', 'GET'])
def time_list_group():
    """Verwaltung der Zeiteinträge der gesamten Gruppe"""
    admin_level = session['admin_level']
    if not session.get('logged_in'):
        return redirect('login')

    message = request.args.get('message', None)
    filter_dict = gen_month_filter()
    month_option = month_list()
    selected_user = request.form.get('selected_user', 'all')

    cur = g.con.cursor()
    cur.execute("SELECT u_ID, name, surname FROM users WHERE o_ID=%s", (session['o_id'],))
    fetched_users = cur.fetchall()
    user_count = len(fetched_users)
    cur.close()
    cur = g.con.cursor()
    if selected_user == "all":
        cur.execute("SELECT t_ID, date_a, date_b, pause, diff_time, actual_diff_time, u_ID FROM "
                    "time_entries WHERE o_ID = %s AND "
                    "tracking=0 AND tracking_pause=0 "
                    "AND date_a >= %s AND "
                    "date_a < %s", (session['o_id'],
                                    filter_dict['query_start'], filter_dict['query_end'],))
    else:
        selected_user = int(selected_user)
        cur.execute("SELECT t_ID, date_a, date_b, pause, diff_time, actual_diff_time, u_ID FROM "
                    "time_entries WHERE u_ID = %s AND "
                    "tracking=0 AND tracking_pause=0 "
                    "AND date_a >= %s AND "
                    "date_a < %s", (selected_user,
                                    filter_dict['query_start'], filter_dict['query_end'],))

    db_time_entries = cur.fetchall()
    cur.close()
    entry_count = len(db_time_entries)
    output_entries = []

    for i in range(entry_count):
        if db_time_entries[i][3] is not None:
            pause_in_minutes = db_time_entries[i][3] / 60
            pause_in_minutes = int(pause_in_minutes)
        else:
            pause_in_minutes = 0

        cache = [db_time_entries[i][0],
                 f"{db_time_entries[i][0]}XU{db_time_entries[i][6]}XG{session['o_id']}",
                 db_time_entries[i][1].strftime("%d.%m.%Y %H:%M"),
                 db_time_entries[i][2].strftime("%d.%m.%Y %H:%M"),
                 seconds_to_string(db_time_entries[i][3]),
                 seconds_to_string(db_time_entries[i][4]),
                 seconds_to_string(db_time_entries[i][5]),
                 pause_in_minutes]
        output_entries.insert(i, cache)

    return render_template('time_list_group.html', admin_level=admin_level,
                           current_page='time_list_group',
                           entry_count=entry_count, output_entries=output_entries,
                           message=message, month_option=month_option,
                           selected_month=filter_dict['selected_month'],
                           user_count=user_count, fetched_users=fetched_users,
                           selected_user=selected_user)


@app.route('/time_edit', methods=['POST', 'GET'])
def time_edit():
    """Einzelnen Zeiteintrag verwalten"""
    if not session.get('logged_in'):
        return redirect('login')

    if request.method == "POST" and request.form is not None:

        cur = g.con.cursor()
        cur.execute("SELECT t_ID, date_a, date_b, u_id, o_id FROM "
                    "time_entries WHERE t_ID = %s", (request.form['db_id'],))
        called_entry = cur.fetchall()

        origin = request.form.get('origin')
        if origin == "group":
            current_page = "time_list_group"
        else:
            current_page = "time_list"
        fetched_id = request.form['id']
        db_id = request.form['db_id']
        admin_level = session['admin_level']
        start = called_entry[0][1].strftime("%Y-%m-%dT%H:%M")
        stop = called_entry[0][2].strftime("%Y-%m-%dT%H:%M")
        start_string = called_entry[0][1].strftime("%d.%m.%Y %H:%M")
        stop_string = called_entry[0][2].strftime("%d.%m.%Y %H:%M")
        pause = request.form['pause']
        pause_raw = request.form['pause_raw']
        arbeitszeit = request.form['arbeitszeit']
        netto_arbeitszeit = request.form['netto_arbeitszeit']
        return render_template('time_edit_single.html', admin_level=admin_level,
                               current_page=current_page,
                               origin=origin,
                               id=fetched_id,
                               u_id=called_entry[0][3],
                               o_id=called_entry[0][4],
                               db_id=db_id,
                               start=start, stop=stop,
                               start_string=start_string,
                               stop_string=stop_string,
                               pause=pause, pause_raw=pause_raw,
                               arbeitszeit=arbeitszeit,
                               netto_arbeitszeit=netto_arbeitszeit)
    return None


@app.route('/time_entry_edit', methods=['POST', 'GET'])
def time_entry_edit():
    """Änderungen am Zeiteintrag an der Datenbank vornehmen"""
    if not session.get('logged_in'):
        return redirect('login')
    message = None

    if request.method == "POST" and request.form is not None:
        if request.form['action'] == "save_input":
            message = save_tracking_data(request.form['start_time'],
                                         request.form['stop_time'],
                                         request.form['pause'],
                                         u_id=request.form['u_id'],
                                         o_id=request.form['o_id'],
                                         t_id=request.form['db_id'],
                                         action="update",)

        if request.form['action'] == "delete_entry":
            message = delete_time_entry(request.form['db_id'])

        if request.form.get('origin') == "group":
            return redirect(url_for('time_list_group', message=message))
        return redirect(url_for('time_list', message=message))

    return None


@app.route('/payroll', methods=['POST', 'GET'])
def payroll():
    """Seite für die Lohnabrechnungen"""
    if not session.get('logged_in'):
        return redirect('login')
    admin_level = session['admin_level']
    month_option = month_list()
    current_page = "payroll"
    message = request.args.get('message')

    return render_template('payroll_list.html', month_option=month_option,
                           current_page=current_page, admin_level=admin_level,
                           message=message)


@app.route('/payroll_group', methods=['POST', 'GET'])
def payroll_group():
    """Seite für die Lohnabrechnungen in der Gruppenansicht"""
    if not session.get('logged_in'):
        return redirect('login')
    admin_level = session['admin_level']
    month_option = month_list()
    current_page = "payroll_list_group"
    message = request.args.get('message')
    selected_user = request.form.get('selected_user', 'self')
    cur = g.con.cursor()
    cur.execute("SELECT u_ID, name, surname FROM users WHERE o_ID=%s", (session['o_id'],))
    fetched_users = cur.fetchall()
    cur.close()
    user_count = len(fetched_users)
    for entry in fetched_users:
        if entry[0] == session['u_id']:
            selected_user = entry[0]

    return render_template('payroll_list_group.html', month_option=month_option,
                           current_page=current_page, admin_level=admin_level,
                           message=message, fetched_users=fetched_users,
                           user_count=user_count, selected_user=selected_user)


@app.route('/payroll_generate', methods=['POST', 'GET'])
def payroll_generate():
    """Seite für die Lohnabrechnungen"""
    if not session.get('logged_in'):
        return redirect('login')

    if request.method == "POST" and request.form is not None:

        # Abrufen des SQL Filters für den ausgewählten Monat
        # Umwandlung in eine Python Liste mit ast.literal_eval
        payroll_query = request.form['query']
        payroll_query = ast.literal_eval(payroll_query)
        cur = g.con.cursor()
        # Differenzieren zwischen des Aufrufs der Lohnabrechnung
        # durch den Nutzer selber oder durch einen anderen Nutzer
        if request.form.get('origin') == "group":
            cur.execute("SELECT actual_diff_time FROM "
                        "time_entries WHERE u_ID = %s AND "
                        "tracking=0 AND tracking_pause=0 "
                        "AND date_a >= %s AND "
                        "date_a < %s", (request.form['selected_user'],
                                        payroll_query[1], payroll_query[2],))
            user_time_entries = cur.fetchall()
            cur.close()
            user_name = request.form['selected_user_name']
            cur = g.con.cursor()
            cur.execute("SELECT hourly_rate FROM users "
                        "WHERE u_ID=%s AND coalesce(hourly_rate, '') <>''", (request.form['selected_user'],))
            user_hourly_rate = cur.fetchone()
            cur.close()
            redirect_target = "payroll_group"
        else:
            cur.execute("SELECT actual_diff_time FROM "
                        "time_entries WHERE u_ID = %s AND "
                        "tracking=0 AND tracking_pause=0 "
                        "AND date_a >= %s AND "
                        "date_a < %s", (session['u_id'], payroll_query[1], payroll_query[2],))
            user_name = f"{session['name']} {session['surname']}"
            user_time_entries = cur.fetchall()
            cur.close()
            cur = g.con.cursor()
            cur.execute("SELECT hourly_rate FROM users "
                        "WHERE u_ID=%s AND coalesce(hourly_rate, '') <>''", (session['u_id'],))
            user_hourly_rate = cur.fetchone()
            cur.close()
            redirect_target = "payroll"

        # Ausgabe einer Fehlermeldung, falls kein Zeiteintrag besteht
        if len(user_time_entries) == 0:
            return redirect(url_for(redirect_target,
                                    message="Für diesen Monat wurde keine Zeit erfasst"))
        # Ausgabe einer Fehlermeldung, falls kein Stundensatz eingestellt wurde
        if user_hourly_rate is None:
            return redirect(url_for(redirect_target,
                                    message="Sie müssen einen Stundensatz festlegen!"))

        total_working_seconds = 0

        # Berechnung der Arbeitszeit und des Gehalts anhand des Stundensatzes
        for entry in user_time_entries:
            total_working_seconds += int(entry[0])

        total_working_hours = total_working_seconds / 3600
        total_working_hours = round(total_working_hours, 3)
        hourly_rate = user_hourly_rate[0]
        months_pay = float(hourly_rate) * total_working_hours
        months_pay = round(months_pay, 2)
        months_pay = str(months_pay).replace(".", ",")

        payroll_param = {
            "month_info": payroll_query[0],
            "user_name": user_name,
            "company_name": session['o_name'],
            "work_time": total_working_hours,
            "hourly_rate": user_hourly_rate[0],
            "months_pay": months_pay
        }

        return render_template('payroll_file.html', payroll_param=payroll_param)
    return redirect(url_for('payroll'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    """Registrierungsseite"""
    # Es wird geprüft ob eine request als POST erfasst wurde daraufhin werden
    # die Variablen aus dem Formular einzelnen Variablen zugewiesen.

    if request.method == "POST" and request.form is not None:
        user_data = {'name': request.form['name'],
                     'surname': request.form['surname'],
                     'phone': request.form['phone'],
                     'email': request.form['email'],
                     'password': request.form['password'],
                     'password_verify': request.form['password_verify'],
                     'invite_code': request.form.get('invite_code'),
                     'create_group': request.form.get('create_group'),
                     'hourly_rate': request.form.get('hourly_rate', None),
                     'workload': request.form.get('workload', None),
                     'tos': request.form.get('tos'),
                     'company_name': request.form.get('company_name')}

        # Die Variablen aus dem Formular werden über
        # die Funktion 'registration_error_check' auf Richtigkeit
        # und Formfehler überprüft.
        errors = registration_error_check(user_data, True)

        # Die eingegebene E-Mail wird mit der Datenbank abgeglichen
        # um zu überprüfen ob schon ein Account mit der eingegebenen E-Mail existiert.
        cur = g.con.cursor()
        cur.execute("SELECT u_ID FROM users WHERE email = %s", (user_data['email'],))
        users_exist = cur.fetchall()
        cur.close()

        # Prüfen auf bestehenden Benutzer und auf Fehler
        # Generieren eines Codes zur E-Mail Bestätigung
        # Passwortverschlüsselung
        if not users_exist:
            if errors[2]:
                hashed_password = pbkdf2_sha256.hash(user_data['password'])
                verification_code = gen_verification_code()

                # Anlegen des Nutzers in der Datenbank
                if user_data['create_group'] == "join":
                    invite_info = fetch_o_id_invite(user_data['invite_code'])
                    admin_level = invite_info['admin_level']
                    o_id = invite_info['o_id']
                elif user_data['create_group'] == "create":
                    register_group(user_data['company_name'])
                    o_id = fetch_o_id_create(user_data['company_name'])
                    admin_level = 2
                else:
                    return redirect(url_for('error'))

                cur = g.con.cursor()
                cur.execute("INSERT INTO users (name, surname, phone, email, "
                            "password, admin_level, is_verified, verification_code, o_ID, "
                            "hourly_rate, workload) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (user_data['name'], user_data['surname'],
                             user_data['phone'], user_data['email'],
                             hashed_password, admin_level,
                             "0", verification_code, o_id, user_data['hourly_rate'],
                             user_data['workload'],))
                g.con.commit()
                cur.close()

                subject = f"E-Mail für myWorkTracker verifizieren. {verification_code}"
                recipient = [user_data['email']]
                body = f"Vielen dank, dass Sie den MyWorkTracker nutzen! Bitte bestätigen " \
                       f"Sie Ihre E-Mail mit diesem Verifikations-Code: {verification_code}"
                try:
                    send_message(subject, recipient, body)
                except UnicodeEncodeError:
                    message = "Erfolgreich registriert. Bestätigungsmail konnte " \
                              "wegen Umlauten nicht verschickt werden!"
                else:
                    message = "Erfolgreich registriert"
                return redirect(url_for('login', message=message))

            if errors[2] is False:
                return render_template('register.html',
                                       error_messages=errors[0], error_types=errors[1],
                                       name=user_data['name'], surname=user_data['surname'],
                                       phone=user_data['phone'], email=user_data['email'],
                                       company_name=user_data['company_name'])
        else:
            errors[0].append("Es existiert bereits ein Account mit dieser E-Mail Adresse")
            errors[1].append("email")
            return render_template('register.html', error_messages=errors[0], error_types=errors[1],
                                   name=user_data['name'], surname=user_data['surname'],
                                   phone=user_data['phone'], email=user_data['email'],)
    return render_template('register.html')


@app.route('/verify', methods=['POST', 'GET'])
def verify_mail():
    """Seite zur Bestätigung der E-Mail"""
    if not session.get('logged_in'):
        return redirect('login')
    admin_level = session['admin_level']
    u_id = session['u_id']
    success = request.args.get('success')

    return render_template('verify_mail.html', admin_level=admin_level,
                           u_id=u_id, success=success)


@app.route('/verifying', methods=['POST', 'GET'])
def verify_mail_eval():
    """Überprüfung der E-Mail mit dem Eintrag in der Datenbank"""
    if not session.get('logged_in'):
        return redirect('login')
    admin_level = session['admin_level']

    if request.method == 'POST':
        u_id = request.form['u_id']
        cur = g.con.cursor()
        cur.execute("SELECT verification_code FROM "
                    "users WHERE u_ID = %s", (u_id,))
        db_verification_code = cur.fetchall()
        cur.close()
        if request.form['ver_code'] == db_verification_code[0][0]:
            cur = g.con.cursor()
            cur.execute("UPDATE users SET is_verified=1 "
                        "WHERE u_ID=%s", (u_id,))
            g.con.commit()
            cur.close()
            message = "E-Mail erfolgreich bestätigt"
            session['is_verified'] = 1
            return redirect(url_for('user_dashboard', message=message))
        error_state = 1
        return render_template('verify_mail.html', admin_level=admin_level,
                               u_id=u_id, error_state=error_state)
    return None


@app.route('/resend')
def resend_mail():
    """Erneuter Versand der Mail mit dem Verifikationscode"""
    if not session.get('logged_in'):
        return redirect('login')

    u_id = session['u_id']
    cur = g.con.cursor()
    cur.execute("SELECT verification_code, email FROM "
                "users WHERE u_ID = %s", (u_id,))
    db_verification_data = cur.fetchall()
    cur.close()
    subject = f"E-Mail für myWorkTracker verifizieren. {db_verification_data[0][0]}"
    recipient = [db_verification_data[0][1]]
    body = f"Vielen dank, dass Sie den MyWorkTracker nutzen! Bitte bestätigen " \
           f"Sie Ihre E-Mail mit diesem Verifikations-Code: {db_verification_data[0][0]}"
    send_message(subject, recipient, body)
    success = 1
    return redirect(url_for('verify_mail', success=success))


@app.route('/login', methods=['POST', 'GET'])
def login():
    """Loginseite"""
    if session.get('logged_in'):
        return redirect(url_for('user_dashboard'))
    message = request.args.get('message')
    # Abgleich mit Datenbank und Weiterleitung auf Dashboard bei Erfolg
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cur = g.con.cursor()
        cur.execute("SELECT u_ID, name, surname, phone, email, "
                    "password, hourly_rate, admin_level, is_verified, o_ID"
                    " FROM users WHERE email = %s", (email,))
        account = cur.fetchall()
        cur.close()
        if account:
            if pbkdf2_sha256.verify(password, account[0][5]):
                session['logged_in'] = True
                session['u_id'] = account[0][0]
                session['name'] = account[0][1]
                session['surname'] = account[0][2]
                session['phone'] = account[0][3]
                session['email'] = account[0][4]
                session['hourly_rate'] = account[0][6]
                session['admin_level'] = account[0][7]
                session['is_verified'] = account[0][8]
                set_status("online", session['u_id'])
                # Der Unternehmensname wird durch die o_ID des Nutzers abgefragt and
                # anschließend in der Session gespeichert.
                o_id = account[0][9]
                cur = g.con.cursor()
                cur.execute("SELECT o_ID, o_name FROM o_groups WHERE o_ID = %s", (o_id,))
                company = cur.fetchall()
                cur.close()
                session['o_id'] = company[0][0]
                session['o_name'] = company[0][1]
                return redirect(url_for('user_dashboard'))
            if not pbkdf2_sha256.verify(password, account[0][5]):
                error_message = "Bitte überprüfen Sie ihr Passwort."
                error_type = "password"
                return render_template('login.html', error_message=error_message,
                                       error_type=error_type, email=email)
        else:
            error_message = "Bitte überprüfen Sie ihre E-Mail."
            error_type = "email"
            return render_template('login.html', error_message=error_message,
                                   error_type=error_type,
                                   email=email,
                                   message=message)
    return render_template('login.html', message=message)


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    """Logoutseite. Die Session Variable wird geleert."""
    set_status("offline", session['u_id'])
    session.clear()
    return render_template('logout.html')


def set_status(status, u_id):
    """Ändert den Nutzerstatus in der Datenbank"""
    cur = g.con.cursor()
    cur.execute("UPDATE users SET status=%s WHERE u_id=%s", (status, u_id))
    g.con.commit()
    cur.close()


# Start der Flask-Anwendung
if __name__ == '__main__':
    app.run(debug=True)
