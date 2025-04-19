from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/auth')
def auth():
    client_id = request.args.get('client_id')
    redirect_uri = request.args.get('redirect_uri')
    # In real OAuth, validate client_id and that redirect_uri starts with a registered base URI
    # For this CTF, we assume basic validation passed or is flawed.
    # Simulate IdP login page
    return render_template_string(''' 
        <html><body> 
        <h2>Simulated IdP Login</h2> 
        <p>Login to grant access to Client App.</p> 
        <form action="/grant" method="post"> 
        <input type="hidden" name="redirect_uri" value="{{redirect_uri | e}}"> 
        <input type="submit" value="Grant Access"> 
        </form> 
        </body></html> 
    ''', redirect_uri=redirect_uri)


@app.route('/grant')
def grant():
    redirect_uri = request.form.get('redirect_uri')
    auth_code = "flag{n0t_s0_s3cur3_0auth_c0d3}"  # The flag is the code
    # Redirect back to the client's requested redirect_uri with code in fragment
    # Using fragment (#) is common, but harder to leak via Referer.
    # For CTF simplicity, let's put it in query param (less realistic but easier leak)
    # return redirect(f"{redirect_uri}#code={auth_code}", code=302) # Realistic
    return redirect(f"{redirect_uri}?code={auth_code}", code=302)  # Simplified for CTF leak


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)  # Use 0.0.0.0 to be accessible
