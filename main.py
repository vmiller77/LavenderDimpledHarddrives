from flask import Flask, request, redirect, render_template_string
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

    # Create simulated VM folders and only put real flag in VM3
    for i in range(1, 4):
        vm_path = f"vm{i}"
        os.makedirs(vm_path, exist_ok=True)
        with open(os.path.join(vm_path, "readme.txt"), "w") as f:
            f.write(f"Welcome to VM{i}\n")
        if i in [1, 2]:
            with open(os.path.join(vm_path, "flag.txt"), "w") as f:
                f.write("Gotcha! Flag is not here!")
    with open("vm3/flag.txt", "w") as f:
        f.write("flag{v1rtu4l_w4ll_h0pp3r}")


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
            <li><a href="/replay-redeem?token=figureItOut">Back in Session</a></li>
            <li><a href="/vm1">Out of the Box</a></li>
        </ul>
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
