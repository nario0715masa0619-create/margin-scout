import subprocess

subprocess.run([
    'heroku', 'config:set', 
    'CORS_ORIGINS=["https://margin-scout-staging-frontend-ddc7bb12af5f.herokuapp.com", "https://margin-scout-staging-frontend.herokuapp.com"]', 
    '-a', 'ms-staging-backend-v2'
], shell=True)
