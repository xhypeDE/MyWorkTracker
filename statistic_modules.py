"""Funktionen für Statistiken"""

from flask import g, session
from time_modules import gen_month_filter


def predicted_cost(o_id):
    """Berechnet die Personalkosten des Monats"""
    cur = g.con.cursor()
    cur.execute("SELECT workload, hourly_rate "
                "FROM users WHERE o_ID=%s", (o_id,))
    o_costs = cur.fetchall()
    cur.close()

    prediction = 0
    for workload, hourly_rate in o_costs:
        if workload is not None and hourly_rate is not None\
                and workload != "" and hourly_rate != ""\
                and workload != "NULL" and hourly_rate != "NULL":
            workload_month = float(workload) * 4
            cache = float(workload_month) * float(hourly_rate)
            prediction += float(cache)
    prediction = round(prediction, 2)
    prediction = format(prediction, '.2f')

    return prediction


def actual_cost(o_id, admin_level):
    """Berechnet die derzeitige Personalkosten für den Monat"""
    filter_dict = gen_month_filter()
    cur = g.con.cursor()
    if admin_level == 3:
        cur.execute("SELECT actual_diff_time, u_ID FROM "
                    "time_entries WHERE "
                    "tracking=0 AND tracking_pause=0 "
                    "AND date_a >= %s AND "
                    "date_a < %s", (filter_dict['query_start'], filter_dict['query_end'],))
    elif admin_level == 2:
        cur.execute("SELECT actual_diff_time, u_ID FROM "
                    "time_entries WHERE o_ID = %s AND "
                    "tracking=0 AND tracking_pause=0 "
                    "AND date_a >= %s AND "
                    "date_a < %s", (o_id,
                                    filter_dict['query_start'], filter_dict['query_end'],))
    else:
        cur.execute("SELECT actual_diff_time, u_ID FROM "
                    "time_entries WHERE u_ID = %s AND "
                    "tracking=0 AND tracking_pause=0 "
                    "AND date_a >= %s AND "
                    "date_a < %s", (session['u_id'],
                                    filter_dict['query_start'], filter_dict['query_end'],))

    o_costs = cur.fetchall()
    cur.close()

    cur = g.con.cursor()
    if admin_level == 3:
        cur.execute("SELECT u_ID, hourly_rate FROM users")
    else:
        cur.execute("SELECT u_ID, hourly_rate "
                    "FROM users WHERE o_ID=%s", (o_id,))
    user_financial = {}

    for row in cur:
        user_financial[row[0]] = row[1]
        if user_financial[row[0]] is None or user_financial[row[0]] == ""\
                or user_financial[row[0]] == "NULL":
            user_financial[row[0]] = 0

    cur.close()
    calculated_cost = 0
    accumulated_hours = 0

    for actual_diff_time, u_id in o_costs:
        time_in_hours = actual_diff_time / 3600
        accumulated_hours += float(time_in_hours)
        calculated_cost += float(time_in_hours) * float(user_financial[u_id])

    calculated_cost = round(calculated_cost, 2)
    accumulated_hours = round(accumulated_hours, 2)
    calculated_cost = format(calculated_cost, '.2f')
    accumulated_hours = format(float(accumulated_hours), '.2f')

    financial_stats = {
        'realtime_cost': calculated_cost,
        'realtime_hours': accumulated_hours
    }
    return financial_stats


def user_counter(o_id, admin_level, status):
    """Zählt die Anzahl der Nutzer"""
    cur = g.con.cursor()
    if status == "active":
        if admin_level == 3:
            cur.execute("SELECT u_ID FROM "
                        "users WHERE (status=%s or status=%s)",
                        ("online", "tracking",))
        elif admin_level == 2:
            cur.execute("SELECT u_ID FROM "
                        "users WHERE o_ID = %s "
                        "and (status=%s or status=%s)",
                        (o_id, "online", "tracking",))
    else:
        if admin_level == 3:
            cur.execute("SELECT u_ID FROM users")
        elif admin_level == 2:
            cur.execute("SELECT u_ID FROM "
                        "users WHERE o_ID = %s",
                        (o_id,))

    user_count = 0

    for row in cur:
        user_count += 1
    cur.close()
    return user_count
