from flask import Flask, request, render_template_string
import urllib.parse

app = Flask(__name__)

# Simulated OAuth client configuration
CLIENT_ID = "client789"
IDP_AUTH_URL = "http://localhost:5001/oauth/authorize"

# Home page with login options
@app.route('/')
def home():
    legitimate_redirect = "http://localhost:5000/callback"
    return render_template_string("""
        <h1>OAuth Client App</h1>
        <p>Simulates a client application using the vulnerable IdP at localhost:5001.</p>
        <h2>Legitimate Login</h2>
        <a href="{{ idp_auth_url }}?client_id={{ client_id }}&redirect_uri={{ legitimate_redirect }}&response_type=code&state=xyz">
            Login with IdP
        </a>
        <h2>Test the Attack</h2>
        <p>Use the attack.py script or visit the IdP's malicious link to see the exploit.</p>
    """, idp_auth_url=IDP_AUTH_URL, client_id=CLIENT_ID, legitimate_redirect=urllib.parse.quote(legitimate_redirect))

# Legitimate callback endpoint
@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    return render_template_string("""
        <h1>Legitimate Callback</h1>
        <p>Authorization Code: {{ code }}</p>
        <p>State: {{ state }}</p>
        <p>This is the legitimate client callback.</p>
    """, code=code, state=state)

# Attacker-controlled endpoint
@app.route('/attacker')
def attacker():
    code = request.args.get('code')
    state = request.args.get('state')
    return render_template_string("""
        <h1>Attacker Server</h1>
        <p>Stolen Authorization Code: {{ code }}</p>
        <p>State: {{ state }}</p>
        <p>The attacker has captured the code!</p>
    """, code=code, state=state)

if __name__ == '__main__':
    app.run(port=5000, debug=True)