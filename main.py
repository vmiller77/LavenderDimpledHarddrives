from flask import Flask, request, redirect, render_template_string
import sqlite3
import os

app = Flask(__name__)


# --- Create or reset the database ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    c.execute("INSERT INTO users (name) VALUES ('admin'), ('guest'), ('bob')")
    conn.commit()

    c.execute("DROP TABLE IF EXISTS comments")
    c.execute("CREATE TABLE comments (id INTEGER PRIMARY KEY, content TEXT)")
    conn.commit()
    conn.close()

    # Create directory and files for traversal challenge
    os.makedirs("files", exist_ok=True)
    with open("files/about.txt", "w") as f:
        f.write("This is a public file.")

    os.makedirs("secret", exist_ok=True)
    with open("secret/flag.txt", "w") as f:
        f.write("flag{tr4v3rs4l_succ3ss}")


# --- Home Page ---
@app.route('/')
def index():
    init_db()
    return '''
        <h2>🔐 Mini CTF Challenge</h2>
        <ul>
            <li><a href="/search">Query Me This</a></li>
            <li><a href="/comment">Flag Alert!</a></li>
            <li><a href="/admin-panel?role=user">Climbing the Ranks</a></li>
            <li><a href="/files?name=files/about.txt">Dot Dot Flag</a> <small>(Can you find something more... secret?)</small></li>
            <li><a href="/login">Trust Issues</a></li>
        </ul>
    '''


# --- SQL Injection Challenge ---
@app.route('/search')
def search():
    name = request.args.get('name', '')
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        query = f"SELECT * FROM users WHERE name = '{name}'"
        c.execute(query)
        result = c.fetchall()
        if result:
            return f"<p>User(s) found: {result}</p><p>🎉 flag{{sql_injection_master}}</p>"
        else:
            return '''
                <p>No user found.</p>
                <form action="/search" method="get">
                    Try again: <input name="name">
                    <input type="submit" value="Search">
                </form>
            '''
    except Exception as e:
        return f"<p>Error: {e}</p>"


# --- XSS Challenge ---
@app.route('/comment', methods=['GET', 'POST'])
def comment():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    if request.method == 'POST':
        content = request.form.get('content')
        c.execute("INSERT INTO comments (content) VALUES (?)", (content, ))
        conn.commit()

    c.execute("SELECT content FROM comments")
    all_comments = c.fetchall()
    conn.close()

    comments_html = "<br>".join([row[0] for row in all_comments])

    if "<script" in comments_html.lower():
        flag = "<p>🎉 flag{xss_script_slayer}</p>"
    else:
        flag = ""

    return f'''
        <h2>📝 XSS Challenge</h2>
        <form method="POST">
            Comment: <input name="content">
            <input type="submit" value="Post">
        </form>
        <h3>All Comments</h3>
        {comments_html}
        {flag}
        <p><a href="/">Back to Home</a></p>
    '''


# --- Privilege Escalation Challenge ---
@app.route('/admin-panel')
def admin_panel():
    role = request.args.get('role', 'user')
    if role == 'admin':
        return "<h2>Welcome, admin!</h2><p>🎉 flag{pr1v1l3g3_escalated}</p>"
    else:
        return "<h2>Access Denied. You are a regular user.</h2><p>Hint: Look at the URL.</p>"


# --- Directory Traversal Challenge ---
@app.route('/files')
def file_viewer():
    filename = request.args.get('name', 'files/about.txt')
    try:
        with open(filename, 'r') as f:
            contents = f.read()
        return f"<h2>File Viewer</h2><pre>{contents}</pre><p><a href='/'>Back</a></p>"
    except Exception as e:
        return f"<p>Error opening file: {e}</p><p><a href='/'>Back</a></p>"


# --- Misconfiguration Challenge ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Hardcoded credentials (misconfiguration!)
        if username == 'guest' and password == 'guest':
            return "<h2>Welcome, guest!</h2><p>🎉 flag{m1sc0nf1gur3d_acc3ss}</p>"
        else:
            message = "<p style='color:red;'>Invalid credentials</p>"

    return f'''
        <h2>🔓 Misconfiguration Login</h2>
        <form method="POST">
            Username: <input name="username"><br>
            Password: <input name="password" type="password"><br>
            <input type="submit" value="Login">
        </form>
        {message}
        <p><a href='/'>Back to Home</a></p>
    '''


# --- Run the App ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
