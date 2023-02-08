"""Funktionen für die Zeiterfassung"""
import ast
from datetime import datetime
from flask import session, g, request


def calc_elapsed(date_a, tracking_type):
    """Berechnet die vergangene Zeit aus einem Zeiteintrag"""
    current_time = datetime.now()
    passed_time = current_time - date_a
    calc_seconds = int(passed_time.total_seconds())
    days, hours = divmod(calc_seconds, 86400)
    hours, remainder = divmod(hours, 3600)
    minutes = remainder // 60

    if days > 0:
        if days == 1:
            time_info_passed = f"Seit dem Beginn der {tracking_type} ist " \
                               f"1 Tag {hours} Stunden und" \
                               f" {minutes} Minuten vergangen."
        else:
            time_info_passed = f"Seit dem Beginn der {tracking_type} sind {days} " \
                               f"Tage {hours} Stunden und" \
                               f" {minutes} Minuten vergangen."
    elif hours > 0:
        if hours == 1:
            time_info_passed = f"Seit dem Beginn der {tracking_type} ist 1 " \
                               f"Stunde und" \
                               f" {minutes} Minuten vergangen."
        else:
            time_info_passed = f"Seit dem Beginn der {tracking_type} sind {hours} " \
                               f"Stunden und {minutes} Minuten vergangen."
    elif minutes > 0:
        if minutes == 1:
            time_info_passed = f"Seit dem Beginn der {tracking_type} " \
                               "ist eine Minute vergangen."
        else:
            time_info_passed = f"Seit dem Beginn der {tracking_type} " \
                               f"sind {minutes} Minuten vergangen."
    else:
        time_info_passed = f"Sie haben die {tracking_type} gerade gestartet."

    return time_info_passed


def start_tracking():
    """Startet die Zeiterfassung mit einem entsprechenden Datenbank Eintrag"""
    message = None
    current_time = datetime.now()
    current_time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
    cur = g.con.cursor()
    cur.execute("INSERT INTO time_entries (date_a, tracking, u_ID, o_ID)"
                " VALUES (%s, %s, %s, %s)",
                (current_time_string, "1", session['u_id'], session['o_id']))
    g.con.commit()
    cur.close()
    return message


def stop_tracking(t_id, action):
    """Stoppt die Zeiterfassung und speichert in der Datenbank."""
    current_time = datetime.now()
    current_time_string = current_time.strftime("%Y-%m-%d %H:%M:%S")
    cur = g.con.cursor()
    cur.execute("SELECT date_a, pause, pause_date_a FROM time_entries "
                "WHERE t_id=%s", (t_id,))
    time_entry = cur.fetchall()
    if action == "stop_during_pause":
        date_b = time_entry[0][2]
        diff_time = date_b - time_entry[0][0]
        diff_time = int(diff_time.total_seconds())
    else:
        date_b = current_time_string
        diff_time = current_time - time_entry[0][0]
        diff_time = int(diff_time.total_seconds())
    if time_entry[0][1] is None:
        actual_diff_time = diff_time
    else:
        actual_diff_time = diff_time - time_entry[0][1]
    cur.execute("UPDATE time_entries SET date_b=%s, diff_time=%s, "
                "tracking=0, tracking_pause=0, actual_diff_time=%s "
                "WHERE t_ID=%s", (date_b, diff_time, actual_diff_time, t_id,))
    g.con.commit()
    cur.close()
    message = "Zeiterfassung erfolgreich gestoppt."
    return message


def pause_tracking(t_id):
    """Pausiert die Zeiterfassung"""
    current_time = datetime.now()
    pause_date_a = current_time.strftime("%Y-%m-%d %H:%M:%S")
    cur = g.con.cursor()
    cur.execute("UPDATE time_entries SET pause_date_a=%s, "
                "tracking_pause=1, tracking=0 WHERE t_ID=%s", (pause_date_a, t_id))
    g.con.commit()
    cur.close()
    message = "Zeiterfassung pausiert."
    return message


def resume_tracking(t_id):
    """Startet die Zeiterfassung nach einer Pause"""
    cur = g.con.cursor()
    cur.execute("SELECT date_a, pause, pause_date_a FROM "
                "time_entries WHERE t_id=%s", (t_id,))
    time_entry = cur.fetchall()
    current_time = datetime.now()
    pause_date_b = current_time.strftime("%Y-%m-%d %H:%M:%S")
    stop_pause_date_a = time_entry[0][2]
    pause_diff = current_time - stop_pause_date_a
    pause_diff = int(pause_diff.total_seconds())
    if time_entry[0][1] is not None:
        pause_diff += time_entry[0][1]
    cur.execute("UPDATE time_entries SET pause_date_b=%s, pause=%s,"
                "tracking_pause=0, tracking=1 "
                "WHERE t_ID=%s", (pause_date_b, pause_diff, t_id))
    g.con.commit()
    cur.close()
    message = "Zeiterfassung wieder aufgenommen."
    return message


def save_tracking_data(start_time, stop_time, pause, **kwargs):
    """Speichert einen manuellen Zeiterfassungseintrag in der Datenbank"""
    action = kwargs.get('action', None)
    u_id = kwargs.get('u_id', None)
    o_id = kwargs.get('o_id', None)
    t_id = kwargs.get('t_id', None)

    if pause == "":
        pause = 0
    else:
        pause = int(pause)
        pause *= 60
    start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
    stop_time = datetime.strptime(stop_time, '%Y-%m-%dT%H:%M')
    diff_time = stop_time - start_time
    diff_time = int(diff_time.total_seconds())
    actual_diff_time = diff_time - pause
    cur = g.con.cursor()
    if action == "create":
        cur.execute("INSERT INTO time_entries (date_a, date_b, pause, "
                    "tracking, tracking_pause, actual_diff_time, "
                    "diff_time, u_ID, o_ID) VALUES (%s, %s, %s, %s, %s,"
                    " %s, %s, %s, %s)",
                    (start_time, stop_time,
                     pause, 0, 0, actual_diff_time,
                     diff_time, session['u_id'], session['o_id']))
        message = "Zeiteintrag erfolgreich hinzugefügt."
    else:
        cur.execute("UPDATE time_entries SET date_a=%s, date_b=%s, pause=%s, "
                    "tracking=0, tracking_pause=0,  actual_diff_time=%s,"
                    "diff_time=%s, u_ID=%s, o_ID=%s WHERE t_ID=%s",
                    (start_time, stop_time, pause,
                     actual_diff_time, diff_time,
                     u_id, o_id, t_id))
        message = "Zeiteintrag erfolgreich gespeichert."
    g.con.commit()
    cur.close()

    return message


def delete_time_entry(t_id):
    """Löscht einen Zeiteintrag aus der Datenbank"""
    cur = g.con.cursor()
    cur.execute("DELETE FROM time_entries WHERE t_ID = %s", (t_id,))
    message = "Zeiteintrag erfolgreich gelöscht."
    g.con.commit()
    cur.close()
    return message


def seconds_to_string(time_in_seconds):
    """Konvertiert Sekunden aus Datenbank Einträgen in Stunden und Minuten"""
    if time_in_seconds is not None:
        time_in_seconds //= 60
        hours, remainder = divmod(time_in_seconds, 60)
        if hours == 0:
            time_string = f"{remainder} Minuten"
        else:
            time_string = f"{hours} Stunden und {remainder} Minuten"
    else:
        time_string = "keine Pause"
    return time_string


def month_list():
    """Erstellt die Auswahl für das Dropdown Menü der Monatsauswahl für Zeiteinträge"""

    # Dictionary mit allen Monaten
    months = {1: "Januar", 2: "Februar", 3: "März",
              4: "April", 5: "Mai", 6: "Juni",
              7: "Juli", 8: "August", 10: "Oktober",
              9: "September", 11: "November", 12: "Dezember"}

    # Erstellen der leeren Liste, dem aktuellen Monat und Jahr und einem Counter für
    # die While-Schleife
    available_month_options = []
    month_state = datetime.now().month
    year_state = datetime.now().year
    counter = 0

    # Die While-Schleife durchläuft 12 Iterationen in denen die Auswahlmöglichkeiten
    # für das Dropdown Menü für die Zeiteintrag Seite generiert werden. Außerdem wird
    # gleichzeitig für jede Auswahlmöglichkeit der entsprechende SQL Filter generiert.
    # Die Ausgabe wird in einer Liste gespeichert, welche ausgegeben wird.
    while counter <= 12:
        if month_state == 0:
            month_state = 12
            year_state -= 1

        if month_state < 10:
            converted_month_state = f"0{month_state}"
        else:
            converted_month_state = month_state

        date_a = f"{year_state}-{converted_month_state}-01 00:00:00"

        if month_state == 12:
            next_year = year_state + 1
            next_month = 1
            if next_month < 10:
                converted_month_state = f"0{next_month}"
            else:
                converted_month_state = next_month
            date_b = f"{next_year}-{converted_month_state}-01 00:00:00"
        else:
            next_month = month_state + 1
            if next_month < 10:
                converted_month_state = f"0{next_month}"
            else:
                converted_month_state = next_month
            date_b = f"{year_state}-{converted_month_state}-01 00:00:00"

        year_month_string = f"{months[month_state]} {year_state}"
        month_state -= 1
        cache = [year_month_string,
                 date_a,
                 date_b]

        available_month_options.insert(counter, cache)
        counter += 1

    return available_month_options


def gen_month_filter():
    """Generates the SQL datetime filter and other used data"""
    month_option = month_list()
    if request.form.get('month'):
        fetched_list = request.form['month']
        fetched_list = ast.literal_eval(fetched_list)
        month_gen = {
            'month_option': month_option,
            'fetched_list': fetched_list,
            'selected_month': fetched_list[0],
            'query_start': fetched_list[1],
            'query_end': fetched_list[2],
        }
    else:
        month_gen = {
            'month_option': month_option,
            'selected_month': month_option[0][0],
            'query_start': month_option[0][1],
            'query_end': month_option[0][2],
        }
    return month_gen
