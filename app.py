from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            weight INTEGER NOT NULL
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

    # Initialize archived goals database
    conn = sqlite3.connect('archived_goals.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS archived_goals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            weight INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    goals = get_goals()
    decisions = get_decisions()
    return render_template('index.html', goals=goals, decisions=decisions, result=None)

@app.route('/add_goal', methods=['POST'])
def add_goal():
    name = request.form['name']
    weight = request.form['weight']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO goals (name, weight) VALUES (?, ?)', (name, weight))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/edit_goal/<int:goal_id>', methods=['POST'])
def edit_goal(goal_id):
    new_weight = request.form['weight']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('UPDATE goals SET weight = ? WHERE id = ?', (new_weight, goal_id))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/archive_goal/<int:goal_id>', methods=['POST'])
def archive_goal(goal_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT name, weight FROM goals WHERE id = ?', (goal_id,))
    goal = c.fetchone()
    goal_name, goal_weight = goal
    conn.close()

    conn = sqlite3.connect('archived_goals.db')
    c = conn.cursor()
    c.execute('INSERT INTO archived_goals (name, weight) VALUES (?, ?)', (goal_name, goal_weight))
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
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO decisions (name) VALUES (?)', (decision_name,))
    decision_id = c.lastrowid
    for goal_id, score in scores.items():
        c.execute('INSERT INTO ratings (decision_id, goal_id, score) VALUES (?, ?, ?)', (decision_id, goal_id.split('_')[1], score))
    
    c.execute('SELECT MAX(weight) FROM goals')
    max_weight = c.fetchone()[0]
    
    total_score = 0
    for goal_id, score in scores.items():
        c.execute('SELECT weight FROM goals WHERE id = ?', (goal_id.split('_')[1],))
        weight = c.fetchone()[0]

        #Having a positive, negative, or neutral correlation to simplify choosing weight score
        #Because right now I have to choose weight, and score. Having pos, neg, neutral 
        #simplifies bias slightly, and only requires user to choose goal weight, and decision can
        #either bring it closer or further, but undefined for now by how much.
        score_value = {'positive': 1, 'neutral': 0, 'negative': -1}[score]
        total_score += (weight / max_weight) * score_value

        #For choosing a score value for a goal
        #total_score += (weight / max_weight) * score
    
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

def get_decisions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM decisions')
    decisions = c.fetchall()
    conn.close()
    return decisions

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
