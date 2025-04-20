from flask import Flask, request, redirect, url_for

app = Flask(__name__)

# Assume IdP is reachable via target_ip:5001
target_ip = 'localhost'
IDP_AUTH_URL = f"http://${target_ip}:5001/auth"  # Replace <target_ip>
CLIENT_ID = "my_client"


@app.route('/')
def home():
    # Link includes the vulnerable parameter
    login_url = url_for('login', return_to='http://attacker.com:8000', _external=True)  #
    # Example attacker URL
    return f''' 
    <html><body> 
    <h1>Vulnerable Client App</h1> 
    <a href="{url_for('login', _external=True)}">Login with OAuth (Safe Redirect)</a><br> 
    <a href="{login_url}">Login with OAuth (Malicious Redirect Link - Click Me!)</a> 
    </body></html> 
    '''


@app.route('/login')
def login():
    # **Vulnerability Source**: Attacker crafts initial link including return_to
    # Or user clicks a link like the malicious one above.
    return_to = request.args.get('return_to', url_for('safe_landing', _external=True))  #
    # Default to safe landing page
    # Construct callback URI including the potentially malicious return_to
    # This parameter will be passed back from the IdP and misused later
    callback_uri = url_for('callback', return_to=return_to, _external=True)
    # Redirect to IdP
    auth_url = f"{IDP_AUTH_URL.replace(target_ip, request.host.split(':'))}?client_id={CLIENT_ID}&redirect_uri={callback_uri}"
    return redirect(auth_url, code=302)


@app.route('/callback')
def callback():
    # **Vulnerability Sink**: Unsafe redirect using return_to param AFTER IdP redirect
    return_to = request.args.get('return_to', url_for('safe_landing', _external=True))
    auth_code = request.args.get('code')  # Code received from IdP (simplified)
    # Normally, exchange code for token here. We skip for simplicity.
    # **INSECURE**: Redirect immediately to return_to without validation
    # This leaks the auth_code in the Referer header to the return_to site
    print(f"Callback received code: {auth_code}. Redirecting to: {return_to}")  # Server log
    return redirect(return_to, code=302)


@app.route('/safe_landing')
def safe_landing():
    return "Login successful! Welcome to the safe landing page."


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)  # Use 0.0.0.0 to be accessible

## HOW TO FIX =======================================================================================
# @app.route('/callback')
# def callback():
#     auth_code = request.args.get('code') # Code received from IdP
#     # **FIX**: Validate the 'state' parameter here in a real app
#     # **FIX**: Perform code-for-token exchange securely here
#     # **FIX**: IGNORE return_to parameter. Redirect ONLY to a known safe location.
#     safe_landing_url = url_for('safe_landing', _external=True)
#     print(f"Callback received code: {auth_code}. Redirecting securely to: {safe_landing_url}") #
#     # Server log
#     return redirect(safe_landing_url, code=302)
#
# @app.route('/safe_landing')
# def safe_landing():
#     # Display user info or dashboard after successful login
#     return "Login successful! Welcome to the safe landing page."
