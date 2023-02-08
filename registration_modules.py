"""Funktionen für den Registrierungsprozess"""
import re
import random
import string
from flask import g


def has_numbers(input_string):
    """Überprüft String auf Zahlen"""
    return bool(re.search(r'\d', input_string))


def has_special_characters(input_string):
    """Überprüft String auf Sonderzeichen"""
    return bool(re.search(r'^[a-zA-Z0-9.,\- äüöÄÖÜ]*$', input_string))


def contains_hyphen_only(input_string):
    """Überprüft ob der String nur aus Bindestrichen besteht"""
    counter = 0
    for i in input_string:
        if i == "-":
            counter += 1
    if counter == len(input_string):
        return True
    return False


def check_names(name, name_for_error):
    """Überprüft auf Formfehler bei Personen Namen"""
    error_message = ""
    if name == "" or contains_hyphen_only(name) is True:
        error_message = f"Bitte geben Sie einen {name_for_error} ein."
    elif has_special_characters(name) is False:
        error_message = f"Ihr {name_for_error} enthält ungültige Zeichen."
    elif has_numbers(name) is True:
        name_in_sentence = name_for_error + "n"
        error_message = f"Bitte überprüfen Sie ihren {name_in_sentence}. Zahlen sind nicht erlaubt."
    elif len(name) < 2:
        error_message = f"Ihr {name_for_error} ist zu kurz."
    elif len(name) > 32:
        error_message = f"Ihr {name_for_error} ist zu lang"
    if error_message != "":
        return error_message
    return False


def check_phone(phone_number):
    """Überprüft auf Formfehler bei Telefonnummern"""
    error_message = ""
    if phone_number == "":
        error_message = "Bitte geben Sie eine gültige Telefonnummer ein."
    elif not bool(re.search(r"^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s/0-9]*$", phone_number)):
        error_message = "Bitte geben Sie eine gültige Telefonnummer ein."
    elif len(phone_number) >= 19:
        error_message = "Bitte überprüfen Sie ihre Telefonnummer. Ihre Telefonnummer ist zu lang."
    elif len(phone_number) <= 5:
        error_message = "Bitte überprüfen Sie ihre Telefonnummer. Ihre Telefonnummer ist zu kurz."
    if error_message != "":
        return error_message
    return False


def check_mail(mail):
    """Überprüft auf Formfehler bei E-Mails"""
    error_message = ""
    if mail == "":
        error_message = "Bitte geben Sie Ihre E-Mail ein."
    elif not bool(re.search(r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]"
                            r"+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|.\""
                            r"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]"
                            r"|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*.\")"
                            r"@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9]"
                            r"(?:[a-z0-9-]*[a-z0-9])?"
                            r"|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
                            r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:"
                            r"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]"
                            r"|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)])",
                            mail)):
        error_message = "Bitte überprüfen Sie ihre E-Mail Adresse."
    if error_message != "":
        return error_message
    return False


def check_pw(user_password, user_password_verify):
    """Überprüft auf Formfehler bei Passwörtern"""
    error_message = []
    if user_password == "":
        error_message = "Bitte geben Sie ein Passwort ein."
    elif len(user_password) < 5:
        error_message = "Ihr Passwort ist zu kurz! Bitte geben Sie ein längeres Passwort ein."
    elif len(user_password) > 128:
        error_message = "Ihr Passwort ist zu lang! Bitte geben Sie ein kürzeres Passwort ein"
    if user_password != user_password_verify:
        error_message = "Die Passwörter stimmen nicht überein."
    if error_message != "":
        return error_message
    return False


def check_comp_name(company_name):
    """Überprüft auf Formfehler bei Firmennamen"""
    error_message = ""
    if company_name == "" or contains_hyphen_only(company_name):
        error_message = "Bitte geben Sie ein Unternehmensnamen ein. " \
                        "Falls Sie einer Gruppe beitreten wählen Sie diese" \
                        " Option unten aus."
    elif len(company_name) < 3:
        error_message = "Ihr Unternehmensname ist zu kurz."
    elif len(company_name) > 40:
        error_message = "Ihr Unternehmensname ist zu lang."
    if error_message != "":
        return error_message
    return False


def check_invite_code(user_data):
    """Überprüft Einladungscodes"""
    if user_data['create_group'] == "join":
        cur = g.con.cursor()
        cur.execute("SELECT invite_code "
                    "FROM o_invites WHERE invite_code = %s",
                    (user_data['invite_code'],))
        invite = cur.fetchall()
        cur.close()
        if user_data.get('invite_code') is None:
            error_message = "Bitte geben Sie einen Einladungscode ein."
            return error_message
        if len(invite) == 0:
            error_message = "Ihr Einladungscode ist ungültig oder abgelaufen."
            return error_message
    return False


def check_hourly_rate(hourly_rate):
    """Überprüft den Stundensatz auf Formfehler"""
    if hourly_rate != "" and hourly_rate is not None:
        if (bool(re.search(r"^[1-9]\d*(\.\d+)?$", hourly_rate))
            and has_special_characters(hourly_rate))\
                or hourly_rate == "NULL":
            return False
        error_message = "Der eingegebene Stundensatz ist ungültig"
        return error_message
    return False


def check_workload(workload):
    """Überprüft die Wochenstunden auf Formfehler"""
    if workload != "" and workload is not None:
        if (bool(re.search(r"^[1-9]\d*(\.\d+)?$", workload))
            and has_special_characters(workload))\
                or workload == "NULL":
            return False
        error_message = "Die eingegebenen Wochenstunden sind ungültig"
        return error_message
    return False


def registration_error_check(user_data, fresh_register):
    """Führt alle notwendigen Checks zur Registrierung durch"""
    error_messages = []
    error_types = []
    no_error = True
    if check_names(user_data['name'], "Vorname"):
        error_messages.append(check_names(user_data['name'], "Vorname"))
        error_types.append("name")
        no_error = False
    if check_names(user_data['surname'], "Nachname"):
        error_messages.append(check_names(user_data['surname'], "Nachname"))
        error_types.append("surname")
        no_error = False
    if check_phone(user_data['phone']):
        error_messages.append(check_phone(user_data['phone']))
        error_types.append("phone")
        no_error = False
    if check_mail(user_data['email']):
        error_messages.append(check_mail(user_data['email']))
        error_types.append("email")
        no_error = False
    if check_hourly_rate(user_data['hourly_rate']):
        error_messages.append(check_hourly_rate(user_data['hourly_rate']))
        error_types.append("hourly_rate")
        no_error = False
    if check_workload(user_data['workload']):
        error_messages.append(check_workload(user_data['workload']))
        error_types.append("workload")
        no_error = False
    if fresh_register is True or user_data['pw_changed'] is True:
        if check_pw(user_data['password'], user_data['password_verify']):
            error_messages.append(check_pw(user_data['password'], user_data['password_verify']))
            error_types.append("password")
            no_error = False
    if fresh_register is True:
        if user_data['create_group'] == "create" and check_comp_name(user_data['company_name']):
            error_messages.append(check_comp_name(user_data['company_name']))
            error_types.append("comp_name")
            no_error = False
        if user_data['tos'] != "checked":
            error_messages.append("Bitte stimmen Sie der Datenschutzerklärung und den AGB's zu.")
            error_types.append("tos")
            no_error = False
        if check_invite_code(user_data):
            error_messages.append(check_invite_code(user_data))
            error_types.append("invite")
            no_error = False

    return [error_messages, error_types, no_error]


def gen_verification_code(chars=string.ascii_uppercase + string.digits, code_length=8):
    """Generiert einen zufälligen String zur E-Mail Verifikation"""
    return ''.join(random.choice(chars) for _ in range(code_length))


def register_group(company_name):
    """Registriert eine neue Gruppe für den Benutzer"""
    cur = g.con.cursor()
    # Die Variablen o_package und o_restricted sind für spätere Features
    # gedacht und werden vorerst mit '0' gesendet.
    cur.execute("INSERT INTO o_groups (o_name, o_package, o_restricted)"
                " VALUES (%s, %s, %s)", (company_name, "0", "0"))
    g.con.commit()
    cur.close()


def fetch_o_id_invite(invite_code):
    """Erfasst die mit dem Einladungscode zusammenhängende Gruppen ID"""
    cur = g.con.cursor()
    cur.execute("SELECT invite_id, invite_code, invite_o_id, admin_level"
                " FROM o_invites WHERE invite_code = %s",
                (invite_code, ))
    invite = cur.fetchall()
    cur.close()
    o_id_info = {
        'o_id': invite[0][2],
        'admin_level': invite[0][3]
    }
    cur = g.con.cursor()
    cur.execute("DELETE FROM o_invites WHERE invite_id=%s", (invite[0][0],))
    g.con.commit()
    cur.close()
    return o_id_info


def fetch_o_id_create(company_name):
    """Erfasst die ID für die erstellte Gruppe"""
    cur = g.con.cursor()
    cur.execute("SELECT o_id"
                " FROM o_groups WHERE o_name = %s",
                (company_name,))
    created_o_id = cur.fetchall()
    g.con.commit()
    cur.close()
    return created_o_id[0][0]
