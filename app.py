from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY,
            decision_id INTEGER,
            goal_id INTEGER,
            score INTEGER,
            FOREIGN KEY (decision_id) REFERENCES decisions (id),
            FOREIGN KEY (goal_id) REFERENCES goals (id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM goals')
    goals = c.fetchall()
    c.execute('SELECT * FROM decisions')
    decisions = c.fetchall()
    conn.close()
    return render_template('index.html', goals=goals, decisions=decisions)

@app.route('/add_goal', methods=['POST'])
def add_goal():
    name = request.form['name']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO goals (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_decision', methods=['POST'])
def add_decision():
    name = request.form['name']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO decisions (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/rate_decision', methods=['POST'])
def rate_decision():
    decision_id = request.form['decision_id']
    goal_id = request.form['goal_id']
    score = request.form['score']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO ratings (decision_id, goal_id, score) VALUES (?, ?, ?)', (decision_id, goal_id, score))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
