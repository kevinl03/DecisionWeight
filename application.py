from flask import Flask, render_template, request, redirect, url_for,flash
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS template_goals (
            id INTEGER PRIMARY KEY,
            template_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            weight INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (template_id) REFERENCES templates (id)
        )
    ''')
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
    last_decision = get_decisions()  # This fetches only the most recent decision
    templates = get_templates()
    if last_decision:
        result = last_decision[3]  # Assuming the score is in the fourth column
    else:
        result = None
    return render_template('index.html', goals=goals, last_decision=last_decision, templates=templates, result=result)

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
    weight = request.form['weight']  # This captures the integer value from the slider
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
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # First, fetch and archive the current state of the goal
    c.execute('SELECT name, weight, timestamp FROM goals WHERE id = ?', (goal_id,))
    goal_data = c.fetchone()
    if goal_data:
        c.execute('INSERT INTO archived_goals (name, weight, timestamp) VALUES (?, ?, ?)', (goal_data[0], goal_data[1], goal_data[2]))
    
    # Update the goal with the new weight
    c.execute('UPDATE goals SET weight = ?, timestamp = ? WHERE id = ?', (new_weight, timestamp, goal_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/archive_goal/<int:goal_id>', methods=['POST'])
def archive_goal(goal_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    try:
        c.execute('SELECT name, weight, timestamp FROM goals WHERE id = ?', (goal_id,))
        goal = c.fetchone()
        if goal:
            c.execute('INSERT INTO archived_goals (name, weight, timestamp) VALUES (?, ?, ?)', goal)
            c.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
            conn.commit()
        else:
            flash('Goal not found')
    except Exception as e:
        conn.rollback()
        flash('Error archiving the goal')
        print(e)  # Or log the error appropriately
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/add_decision', methods=['POST'])
def add_decision():
    decision_name = request.form['name']
    scores = {key: value for key, value in request.form.items() if key.startswith('score_')}
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT id, name, weight FROM goals')
    goals = c.fetchall()
    max_weight = max(goal[2] for goal in goals) if goals else 1
    
    total_score = 0
    goal_impacts = []
    for goal_id, score in scores.items():
        goal_name = next((goal[1] for goal in goals if str(goal[0]) == goal_id.split('_')[1]), "Unknown Goal")
        weight = next((goal[2] for goal in goals if str(goal[0]) == goal_id.split('_')[1]), 0)
        score_value = float(score)  # since score is a numeric value between -1 and 1
        impact_score = weight * score_value
        total_score += impact_score
        goal_impacts.append((goal_name, impact_score))

    c.execute('INSERT INTO decisions (name, timestamp, total_score) VALUES (?, ?, ?)', (decision_name, timestamp, total_score))
    conn.commit()
    conn.close()
    
    # Redirect to a new template that will display the chart and decision confirmation
    return render_template('decision_chart.html', decision_name=decision_name, timestamp=timestamp, goal_impacts=goal_impacts, total_score=total_score)



@app.route('/save_template', methods=['POST'])
def save_template():
    template_name = request.form['template_name']
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('INSERT INTO templates (name) VALUES (?)', (template_name,))
    template_id = c.lastrowid

    goals = get_goals()
    for goal in goals:
        c.execute('INSERT INTO template_goals (template_id, name, weight, timestamp) VALUES (?, ?, ?, ?)', 
                  (template_id, goal[1], goal[2], goal[3]))

    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/load_template/<int:template_id>', methods=['POST'])
def load_template(template_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Clear current goals
    c.execute('DELETE FROM goals')

    # Load goals from the template
    c.execute('SELECT name, weight, timestamp FROM template_goals WHERE template_id = ?', (template_id,))
    template_goals = c.fetchall()
    for goal in template_goals:
        c.execute('INSERT INTO goals (name, weight, timestamp) VALUES (?, ?, ?)', (goal[0], goal[1], goal[2]))

    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/remove_template/<int:template_id>', methods=['POST'])
def remove_template(template_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('DELETE FROM templates WHERE id = ?', (template_id,))
    c.execute('DELETE FROM template_goals WHERE template_id = ?', (template_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

def get_goals():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM goals')

    goals = c.fetchall()
    conn.close()
    return goals

def get_archived_goals():
    conn = sqlite3.connect('database.db')  # Connect to the main database
    c = conn.cursor()
    c.execute('SELECT * FROM archived_goals')  # Make sure 'archived_goals' is the correct table name
    archived_goals = c.fetchall()
    conn.close()
    return archived_goals

def get_decisions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 1')  # Get the most recent decision
    decision = c.fetchone()
    conn.close()
    return decision  # Return only the most recent decision

def get_previous_decisions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT name, timestamp, total_score FROM decisions')
    decisions = c.fetchall()
    conn.close()
    return decisions

def get_templates():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('SELECT * FROM templates')
    templates = c.fetchall()
    conn.close()
    return templates

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
