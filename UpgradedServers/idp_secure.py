from flask import Flask, request, redirect, render_template_string, session
import urllib.parse
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Secure session key for Flask sessions

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


# Login page for user authorization
@app.route('/login')
def login():
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    response_type = request.args.get('response_type')
    state = request.args.get('state')

    if not all([client_id, redirect_uri, response_type, state]):
        return "Missing parameters", 400

    # Security Addition: Validate redirect_uri against registered URIs
    # Purpose: Prevents redirecting to an attacker-controlled URI, fixing the weak redirect URI vulnerability
    if client_id not in CLIENTS or redirect_uri not in CLIENTS[client_id]["redirect_uris"]:
        return "Invalid client or redirect_uri", 400

    # Store parameters in session for secure post-login redirect
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

        # Security Addition: Re-validate redirect_uri before issuing the code
        # Purpose: Ensures no session tampering or bypass allows an invalid redirect_uri
        if client_id not in CLIENTS or redirect_uri not in CLIENTS[client_id][
            "redirect_uris"] or response_type != "code":
            return "Invalid client or redirect_uri", 400

        auth_code = f"code_{secrets.token_hex(8)}"  # Generate unique authorization code
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

    # Security Addition: Validate redirect_uri at the authorization stage
    # Purpose: Blocks malicious redirect_uris early, preventing further processing
    if client_id not in CLIENTS or redirect_uri not in CLIENTS[client_id]["redirect_uris"] or response_type != "code":
        return "Invalid client or redirect_uri", 400

    # Redirect to login page with validated parameters
    return redirect(
        f"/login?client_id={client_id}&redirect_uri={urllib.parse.quote(redirect_uri)}&response_type={response_type}&state={state}")


# Home page with demo
@app.route('/')
def home():
    legitimate_redirect = urllib.parse.quote(CLIENTS["client789"]["redirect_uris"][0])
    return render_template_string("""
        <h1>Secure OAuth IdP</h1>
        <p>This IdP validates redirect URIs to prevent OAuth redirect URI exploits.</p>
        <h2>Legitimate Flow</h2>
        <a href="/oauth/authorize?client_id=client789&redirect_uri={{ legitimate_redirect }}&response_type=code&state=legit123">
            Legitimate Login
        </a>
        <h2>Security Fixes Applied</h2>
        <ul>
            <li>Added redirect_uri validation in /oauth/authorize to reject unregistered URIs early.</li>
            <li>Added redirect_uri validation in /login (GET) to ensure only registered URIs proceed to login.</li>
            <li>Added redirect_uri re-validation in /login (POST) to prevent session tampering.</li>
        </ul>
        <p>Try using a malicious redirect_uri (e.g., via attack.py) to see the validation in action.</p>
    """, legitimate_redirect=legitimate_redirect)


if __name__ == '__main__':
    app.run(port=5002, debug=True)  # Runs on port 5002 to avoid conflicts