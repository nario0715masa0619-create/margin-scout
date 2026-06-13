#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eBay Sandbox OAuth Authorization Flow"""
import os, sys, json, webbrowser
from urllib.parse import urlencode, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from datetime import datetime

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code = None
    def do_GET(self):
        if 'code=' in self.path:
            query = parse_qs(self.path.split('?')[1])
            OAuthCallbackHandler.auth_code = query.get('code', [None])[0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """<html><body style='text-align:center;margin-top:50px'><h2 style='color:green'>Authorization Successful</h2><p>Close this window and return to terminal</p></body></html>"""
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, format, *args):
        pass

def load_oauth_config():
    env_path = os.path.expanduser('~/.marginscount/.env')
    config = {
        'client_id': None,
        'client_secret': None,
        'redirect_uri': 'http://localhost:8080/callback',
        'auth_url': 'https://auth.sandbox.ebay.com/oauth2/authorize',
        'token_url': 'https://api.sandbox.ebay.com/identity/v1/oauth2/token',
    }
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key == 'EBAY_CLIENT_ID':
                        config['client_id'] = value
                    elif key == 'EBAY_CLIENT_SECRET':
                        config['client_secret'] = value
                    elif key == 'EBAY_REDIRECT_URI':
                        config['redirect_uri'] = value
    return config

def validate_config(config):
    if not config['client_id'] or config['client_id'].startswith('your_'):
        print("ERROR: EBAY_CLIENT_ID not set in .env")
        return False
    if not config['client_secret'] or config['client_secret'].startswith('your_'):
        print("ERROR: EBAY_CLIENT_SECRET not set in .env")
        return False
    return True

def step1_initiate_auth(config):
    print("\n" + "="*70)
    print("eBay Sandbox OAuth Authorization Flow")
    print("="*70)
    print(f"\n[Step 1] Client ID: {config['client_id'][:20]}...")
    auth_params = {
        'client_id': config['client_id'],
        'response_type': 'code',
        'redirect_uri': config['redirect_uri'],
        'scope': 'https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account',
        'state': 'marginscout_oauth',
    }
    auth_url = f"{config['auth_url']}?{urlencode(auth_params)}"
    print(f"[Step 2] Starting callback server on {config['redirect_uri']}...")
    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server.timeout = 120
    print(f"[Step 3] Opening browser for authorization...")
    try:
        webbrowser.open(auth_url)
    except:
        print(f"Please manually visit: {auth_url}")
    print(f"[Step 4] Waiting for callback (120s)...")
    server.handle_request()
    if not OAuthCallbackHandler.auth_code:
        print("\nERROR: Authorization failed - no callback received")
        return None
    print(f"\nOK: Authorization code received!")
    return OAuthCallbackHandler.auth_code

def step2_exchange_code(config, auth_code):
    print(f"\n[Step 5] Exchanging code for tokens...")
    token_payload = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': config['redirect_uri'],
    }
    try:
        response = requests.post(
            config['token_url'],
            auth=(config['client_id'], config['client_secret']),
            data=token_payload,
            timeout=30,
        )
        if response.status_code != 200:
            print(f"ERROR: Token exchange failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
        token_data = response.json()
        refresh_token = token_data.get('refresh_token')
        if not refresh_token:
            print(f"ERROR: No refresh token in response")
            return None
        print(f"\nOK: Token exchange successful!")
        print(f"Refresh Token: {refresh_token[:40]}...")
        return {'refresh_token': refresh_token, 'timestamp': datetime.now().isoformat()}
    except requests.RequestException as e:
        print(f"ERROR: Request failed: {e}")
        return None

def save_refresh_token(refresh_token):
    env_path = os.path.expanduser('~/.marginscount/.env')
    print(f"\n[Step 6] Saving refresh token to .env...")
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    env_vars['EBAY_REFRESH_TOKEN'] = refresh_token
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(f"# Updated: {datetime.now().isoformat()}\n")
        f.write("# DO NOT COMMIT THIS FILE\n\n")
        for key in sorted(env_vars.keys()):
            f.write(f'{key}={env_vars[key]}\n')
    print(f"OK: Refresh token saved to .env!")
    return True

def main():
    config = load_oauth_config()
    if not validate_config(config):
        sys.exit(1)
    auth_code = step1_initiate_auth(config)
    if not auth_code:
        sys.exit(1)
    token_result = step2_exchange_code(config, auth_code)
    if not token_result:
        sys.exit(1)
    if not save_refresh_token(token_result['refresh_token']):
        sys.exit(1)
    print("\n" + "="*70)
    print("OK: OAuth Authorization Complete!")
    print("="*70)
    print(f"\nNext step: python sandbox_connection_test.py\n")

if __name__ == '__main__':
    main()
