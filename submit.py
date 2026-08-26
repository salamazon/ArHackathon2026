#!/usr/bin/env python3
import os
import re
import json
import random
import requests

SUCCESS_MESSAGES = [
    "the pods are in your hands now.",
    "somewhere, a pod just got its hopes up.",
    "your drive units have entered the chat.",
    "beep boop.",
]
from urllib.parse import urlsplit, parse_qsl

def main():
    with open('team.json', 'r') as f:
        team_data = json.load(f)

    submit_url = team_data.get('submit_url', '')
    if not submit_url.startswith('https://'):
        print("Error: no submit URL configured.")
        print('team.json ships with the submission URL pre-filled as "submit_url" -')
        print("restore it from the repo if it was edited away.")
        return

    team = team_name(team_data)
    if not team:
        print('Error: put your team name in team.json as "name", e.g.:')
        print('  {"name": "team-rocket", ...}')
        return

    routing_file = "ar_hackathon/api/routing.py"
    if not os.path.exists(routing_file):
        print(f"Error: {routing_file} not found")
        return

    try:
        with open(routing_file, 'rb') as f:
            payload = team_info_header(team_data) + f.read()

        parts = urlsplit(submit_url)
        fields = dict(parse_qsl(parts.query))
        if 'policy' in fields:
            endpoint = f"{parts.scheme}://{parts.netloc}{parts.path}"
            fields['key'] = f"2026/{team}_routing.py"
            response = requests.post(endpoint, data=fields,
                                     files={'file': ('routing.py', payload)})
        else:
            response = requests.put(submit_url, data=payload)

        if response.status_code in (200, 201, 204):
            print(f"Successfully uploaded routing.py for team '{team}' - "
                  f"{random.choice(SUCCESS_MESSAGES)}")
        elif response.status_code == 403:
            print("Upload rejected (403). The submission URL may have expired -")
            print("pull the latest version of the repo or ask the organizers.")
        else:
            print(f"Upload failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Upload failed: {e}")

def team_name(team_data):
    raw = str(team_data.get('name', '')).strip()
    if not raw or raw.startswith('<'):
        return None
    return re.sub(r'[^A-Za-z0-9._-]', '_', raw)[:64]

def team_info_header(team_data):
    def clean(s):
        return str(s).replace('\n', ' ').replace('\r', ' ')

    emails = [clean(e) for e in team_data.get('emails', [])
              if isinstance(e, str) and '@' in e and not e.startswith('<')]
    if not emails:
        print('Reminder: add your team members\' emails to team.json as "emails": [...]')
        return b''

    name = clean(team_data.get('name', ''))
    return f"# team: {name}\n# emails: {', '.join(emails)}\n".encode()

if __name__ == "__main__":
    main()
