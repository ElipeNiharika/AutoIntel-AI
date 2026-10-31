import sys
import os
import time
import subprocess
import json
import urllib.request
import urllib.parse
import argparse

CLIENT_ID = '178c6fc778ccc68e1d6a'

def get_git_exe():
    mingit_cmd = os.path.expandvars(r'%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe')
    if os.path.exists(mingit_cmd):
        return mingit_cmd
    return 'git'

def push_with_token(token, repo_url='https://github.com/ElipeNiharika/AutoIntel-AI.git'):
    git_exe = get_git_exe()
    env = os.environ.copy()
    env['PATH'] = os.path.expandvars(r'%LOCALAPPDATA%\Programs\MinGit\cmd;%LOCALAPPDATA%\Programs\MinGit\ucrt64\bin;') + env.get('PATH', '')
    
    clean_url = repo_url.replace('https://', '')
    auth_url = f'https://x-access-token:{token}@{clean_url}'
    
    print('\nPushing to GitHub repository...')
    cmd = [git_exe, 'push', '-u', auth_url, 'main']
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    
    if res.returncode == 0:
        print('\nSUCCESS! Everything has been successfully pushed to https://github.com/ElipeNiharika/AutoIntel-AI')
        subprocess.run([git_exe, 'remote', 'set-url', 'origin', repo_url], env=env)
        return True
    else:
        print('\nPush failed:')
        print(res.stderr)
        print(res.stdout)
        return False

def device_flow_login():
    data = urllib.parse.urlencode({
        'client_id': CLIENT_ID,
        'scope': 'repo,read:org'
    }).encode()
    
    req = urllib.request.Request(
        'https://github.com/login/device/code',
        data=data,
        headers={'Accept': 'application/json', 'User-Agent': 'AutoIntelAI-Push'}
    )
    
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
    
    device_code = res['device_code']
    user_code = res['user_code']
    verification_uri = res['verification_uri']
    expires_in = res.get('expires_in', 900)
    interval = res.get('interval', 5)
    
    print('=' * 60)
    print('GITHUB DEVICE AUTHORIZATION REQUIRED')
    print('=' * 60)
    print(f'1. Open your browser to:  {verification_uri}')
    print(f'2. Enter this code:       {user_code}')
    print('=' * 60)
    print('Waiting for authorization (press Ctrl+C to cancel)...')
    
    start_time = time.time()
    while time.time() - start_time < expires_in:
        time.sleep(interval)
        
        poll_data = urllib.parse.urlencode({
            'client_id': CLIENT_ID,
            'device_code': device_code,
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
        }).encode()
        
        poll_req = urllib.request.Request(
            'https://github.com/login/oauth/access_token',
            data=poll_data,
            headers={'Accept': 'application/json', 'User-Agent': 'AutoIntelAI-Push'}
        )
        
        try:
            with urllib.request.urlopen(poll_req) as poll_resp:
                token_res = json.loads(poll_resp.read().decode())
                
                if 'access_token' in token_res:
                    token = token_res['access_token']
                    print('\nGitHub Authorization granted successfully!')
                    return push_with_token(token)
                
                err = token_res.get('error')
                if err == 'authorization_pending':
                    print('.', end='', flush=True)
                    continue
                elif err == 'slow_down':
                    interval += 5
                    continue
                elif err == 'expired_token':
                    print('\nCode expired. Please run the script again.')
                    return False
                elif err == 'access_denied':
                    print('\nAuthorization was cancelled by user.')
                    return False
                else:
                    print(f'\nUnexpected response: {token_res}')
                    return False
        except Exception as e:
            print(f'\nRequest error: {e}')
            time.sleep(2)
            
    print('\nAuthorization timed out.')
    return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Push project to GitHub')
    parser.add_argument('--token', type=str, help='GitHub Personal Access Token (PAT)')
    args = parser.parse_args()
    
    if args.token:
        push_with_token(args.token)
    else:
        device_flow_login()
