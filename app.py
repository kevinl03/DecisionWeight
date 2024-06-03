from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

def init_db():
    # Initialize main database
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            weight INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            total_score REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

    # Initialize archived goals database
    conn = sqlite3.connect('archived_goals.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS archived_goals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            weight INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    goals = get_goals()
    decisions = get_decisions()
    return render_template('index.html', goals=goals, decisions=decisions, result=None)

@app.route('/archived')
def archived():
    archived_goals = get_archived_goals()
    return render_template('archived.html', archived_goals=archived_goals)

@app.route('/previous_decisions')
def previous_decisions():
    decisions = get_previous_decisions()
    return render_template('previous_decisions.html', decisions=decisions)

@app.route('/add_goal', methods=['POST'])
def add_goal():
    name = request.form['name']
    weight = request.form['weight']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO goals (name, weight, timestamp) VALUES (?, ?, ?)', (name, weight, timestamp))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit_goal/<int:goal_id>', methods=['POST'])
def edit_goal(goal_id):
    new_weight = request.form['weight']
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Archive the current state of the goal
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT name, weight, timestamp FROM goals WHERE id = ?', (goal_id,))
    goal = c.fetchone()
    goal_name, goal_weight, goal_timestamp = goal
    conn.close()

    conn = sqlite3.connect('archived_goals.db')
    c = conn.cursor()
    c.execute('INSERT INTO archived_goals (name, weight, timestamp) VALUES (?, ?, ?)', (goal_name, goal_weight, goal_timestamp))
    conn.commit()
    conn.close()

    # Update the goal with the new weight and timestamp
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('UPDATE goals SET weight = ?, timestamp = ? WHERE id = ?', (new_weight, timestamp, goal_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/archive_goal/<int:goal_id>', methods=['POST'])
def archive_goal(goal_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT name, weight, timestamp FROM goals WHERE id = ?', (goal_id,))
    goal = c.fetchone()
    goal_name, goal_weight, goal_timestamp = goal
    conn.close()

    conn = sqlite3.connect('archived_goals.db')
    c = conn.cursor()
    c.execute('INSERT INTO archived_goals (name, weight, timestamp) VALUES (?, ?, ?)', (goal_name, goal_weight, goal_timestamp))
    conn.commit()
    conn.close()

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))

@app.route('/add_decision', methods=['POST'])
def add_decision():
    decision_name = request.form['name']
    scores = {key: value for key, value in request.form.items() if key.startswith('score_')}
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT MAX(weight) FROM goals')
    max_weight = c.fetchone()[0]
    
    total_score = 0
    for goal_id, score in scores.items():
        c.execute('SELECT weight FROM goals WHERE id = ?', (goal_id.split('_')[1],))
        weight = c.fetchone()[0]
        score_value = {'positive': 1, 'neutral': 0, 'negative': -1}[score]
        total_score += (weight / max_weight) * score_value
    
    c.execute('INSERT INTO decisions (name, timestamp, total_score) VALUES (?, ?, ?)', (decision_name, timestamp, total_score))
    conn.commit()
    conn.close()
    
    return render_template('index.html', goals=get_goals(), decisions=get_decisions(), result=total_score)

def get_goals():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM goals')
    goals = c.fetchall()
    conn.close()
    return goals

def get_archived_goals():
    conn = sqlite3.connect('archived_goals.db')
    c = conn.cursor()
    c.execute('SELECT * FROM archived_goals')
    archived_goals = c.fetchall()
    conn.close()
    return archived_goals

def get_decisions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM decisions')
    decisions = c.fetchall()
    conn.close()
    return decisions

def get_previous_decisions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT name, timestamp, total_score FROM decisions')
    decisions = c.fetchall()
    conn.close()
    return decisions

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
