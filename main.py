from flask import Flask, request, redirect, render_template_string, make_response
import sqlite3
import os
import base64

app = Flask(__name__)

used_tokens = set()  # Simulate improper token handling (replay attack)


# --- Create or reset the database ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
    c.execute("INSERT INTO users (name) VALUES ('admin'), ('guest'), ('bob'), ('flag{s0qu3ry_1nj3ct0r_007}')")
    conn.commit()

    c.execute("DROP TABLE IF EXISTS comments")
    c.execute("CREATE TABLE comments (id INTEGER PRIMARY KEY, content TEXT)")
    conn.commit()
    conn.close()

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
    resp = make_response('''
        <h2>🔐 Mini CTF Challenge</h2>
            <li><a href="/search">Query Me This</a></li>
            <li><a href="/comment">Flag Alert!</a></li>
            <li><a href="/admin-panel?role=user">Climbing the Ranks</a></li>
            <li><a href="/files?name=files/about.txt">Secrets</a> <small>(Can you find something more... secret?)</small></li>
            <li><a href="/login">Trust Issues</a></li>
            <li><a href="/replay-redeem?token=figureItOut">Back in Session</a></li>
            <li><a href="/leftovers">Hansel and Gretel</a></li>
            <li><a href="/vm1">Out of the Box</a></li>
        </ul>
    ''')
    resp.set_cookie("crumb", "cookie_crumb")
    return resp


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
        # Only reward the flag if the query is injected (more than 1 user or contains flag entry)
        if any('flag' in row[1] for row in result):
            return f"<p>User(s) found: {result}</p><p>🎉 flag{{s0qu3ry_1nj3ct0r_007}}</p>"
        elif result:
            return f"<p>User(s) found: {result}</p><p>Nice try, but that’s not the flag.</p>"
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
        if "secret/flag.txt" in filename:
            contents += "\n🎉 flag{tr4v3rs4l_succ3ss}"
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


# --- Replay Attack Challenge ---
@app.route('/replay-redeem')
def replay_redeem():
    token = request.args.get('token', '')
    if token == 'abc123':
        return "<h2>Token Redeemed</h2><p>🎉 flag{r3p3at_4tt4ck}</p><p><a href='/'>Back to Home</a></p>"
    elif token == 'figureItOut':
        encoded = base64.b64encode(b'abc123').decode()
        return f"<h2>🚨 Intercepted Token</h2><p>Looks like someone’s token leaked: <code>{encoded}</code></p><p>Decode it and reuse it... if you dare.</p><p><a href='/'>Back</a></p>"
    else:
        return "<h2>Invalid token</h2><p><a href='/'>Back</a></p>"


# --- Resource Reuse Challenge ---
@app.route('/leftovers', methods=['GET', 'POST'])
def leftovers():
    message = ""
    if request.method == 'POST':
        crumb = request.form.get('crumb_input')
        if crumb == request.cookies.get("crumb"):
            message = "<p>🎉 flag{y0u_8_th3_l3ft0v3rs}</p>"
        else:
            message = "<p>❌ That’s not the leftover you're looking for.</p>"
    return f'''
        <h2>🍽️ Leftovers</h2>
        <p>When systems don’t clean up after use, leftover data can be accessed by someone else — this is called <strong>resource reuse</strong>.</p>
        <p>Did anyone leave any crumbs behind?</p>
        <form method="POST">
            Enter the value of the leftover: <input name="crumb_input">
            <input type="submit" value="Submit">
        </form>
        {message}
        <p><a href='/'>Back</a></p>
    '''

# --- Simulated VM Escape Challenge ---
def vm_interface(vm_name):
    files = os.listdir(vm_name)
    files_list = "<ul>" + "".join(f"<li>{f}</li>" for f in files) + "</ul>"
    has_input = vm_name in ['vm1', 'vm2']

    form_html = f'''
        <form method="get">
            Enter filename: <input name="filename">
            <input type="submit" value="View File">
        </form>
    ''' if has_input else "<p>This VM is locked. You cannot view files here.</p>"

    filename = request.args.get('filename')
    content = ""
    if filename:
        if filename.strip() == "../vm3/flag.txt":
            content = "<p>🎉 flag{v1rtu4l_w4ll_h0pp3r}</p>"
        else:
            try:
                safe_path = os.path.normpath(os.path.join(vm_name, filename))
                with open(safe_path, 'r') as f:
                    file_content = f.read()
                    content = f"<pre>{file_content}</pre>"
            except Exception as e:
                content = f"<p>Error opening file: {e}</p>"

    return f'''
        <h2>🧠 {vm_name.upper()} Interface</h2>
        <p>Files available in this VM:</p>
        {files_list}
        {form_html}
        {content}
        <p><a href="/">Back to Home</a></p>
    '''

@app.route('/vm1')
def vm1():
    return vm_interface('vm1')

@app.route('/vm2')
def vm2():
    return vm_interface('vm2')

@app.route('/vm3')
def vm3():
    return vm_interface('vm3')


# --- Run the App ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
