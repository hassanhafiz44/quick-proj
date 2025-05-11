import sqlite3

import click
from flask import current_app
from flask import g
from flask.cli import with_appcontext

def levenshtein(s1, s2):
    if not s1 or not s2:
        return max(len(s1), len(s2))

    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def fuzzy_in_text(query, text):
    """
    Returns the minimum Levenshtein distance between `query` and any substring of `text`
    of the same length as `query`. Automatically swaps if query is longer than text.
    """
    query = query.lower()
    text = text.lower()

    # Always search for the shorter inside the longer
    if len(query) > len(text):
        query, text = text, query

    qlen = len(query)
    tlen = len(text)

    min_dist = float('inf')
    for i in range(tlen - qlen + 1):
        window = text[i:i+qlen]
        dist = levenshtein(query, window)
        if dist < min_dist:
            min_dist = dist
    return min_dist


def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.create_function("fuzzy_in_text", 2, fuzzy_in_text)
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """Clear existing data and create new tables."""
    db = get_db()

    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
