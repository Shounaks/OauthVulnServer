from flask import Flask, request, redirect, render_template_string, session
import urllib.parse
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Secure session key

# Simulated client registry
CLIENTS = {
    "client789": {
        "client_secret": "secret789",
        "redirect_uris": ["http://localhost:5000/callback"],
    }
}

# Simulated user database
USERS = {
    "user3": {"password": "pass123", "name": "OAuth User"}
}

# Simulated attacker server
ATTACKER_SERVER = "http://localhost:5000/attacker"


# Login page for user authorization
@app.route('/login')
def login():
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    response_type = request.args.get('response_type')
    state = request.args.get('state')

    if not all([client_id, redirect_uri, response_type, state]):
        return "Missing parameters", 400

    # Store parameters in session for post-login redirect
    session['auth_params'] = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': response_type,
        'state': state
    }

    return render_template_string("""
        <h1>IdP Login</h1>
        <form method="post" action="/login">
            <input type="hidden" name="client_id" value="{{ client_id }}">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <input type="submit" value="Login">
        </form>
    """, client_id=client_id)


# Handle login and issue authorization code
@app.route('/login', methods=['POST'])
def handle_login():
    username = request.form.get('username')
    password = request.form.get('password')
    auth_params = session.get('auth_params', {})

    if not auth_params:
        return "Session expired", 400

    if username in USERS and USERS[username]['password'] == password:
        client_id = auth_params['client_id']
        redirect_uri = auth_params['redirect_uri']
        response_type = auth_params['response_type']
        state = auth_params['state']

        # Vulnerability: No validation of redirect_uri against registered URIs
        if client_id not in CLIENTS or response_type != "code":
            return "Invalid client or response_type", 400

        auth_code = f"code_{secrets.token_hex(8)}"  # Generate unique auth code
        redirect_url = f"{redirect_uri}?code={auth_code}&state={state}"
        return redirect(redirect_url)

    return "Invalid credentials", 401


# OAuth authorization endpoint
@app.route('/oauth/authorize')
def authorize():
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    response_type = request.args.get('response_type')
    state = request.args.get('state')

    if not all([client_id, redirect_uri, response_type, state]):
        return "Missing parameters", 400

    if client_id not in CLIENTS or response_type != "code":
        return "Invalid client or response_type", 400

    # Redirect to login page
    return redirect(
        f"/login?client_id={client_id}&redirect_uri={urllib.parse.quote(redirect_uri)}&response_type={response_type}&state={state}")


# Home page with demo
@app.route('/')
def home():
    legitimate_redirect = urllib.parse.quote(CLIENTS["client789"]["redirect_uris"][0])
    malicious_redirect = urllib.parse.quote(ATTACKER_SERVER)
    return render_template_string("""
        <h1>OAuth IdP Simulator</h1>
        <p>This server simulates a vulnerable OAuth IdP with weak redirect URI validation.</p>
        <h2>Legitimate Flow</h2>
        <a href="/oauth/authorize?client_id=client789&redirect_uri={{ legitimate_redirect }}&response_type=code&state=legit123">
            Legitimate Login
        </a>
        <h2>Malicious Flow (Exploit)</h2>
        <a href="/oauth/authorize?client_id=client789&redirect_uri={{ malicious_redirect }}&response_type=code&state=malicious123">
            Malicious Login
        </a>
        <h2>Vulnerability Details</h2>
        <ul>
            <li><b>Issue:</b> The IdP does not validate redirect_uri against registered URIs.</li>
            <li><b>Exploit:</b> Attackers can use any redirect_uri to steal auth codes.</li>
            <li><b>Fix:</b> Check redirect_uri against CLIENTS[client_id]["redirect_uris"].</li>
        </ul>
        <p>Run with app.py (port 5000) and use attack.py to automate the exploit.</p>
    """, legitimate_redirect=legitimate_redirect, malicious_redirect=malicious_redirect)


if __name__ == '__main__':
    app.run(port=5001, debug=True)