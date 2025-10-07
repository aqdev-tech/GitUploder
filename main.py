
import os
import tempfile
import zipfile
import base64
import requests
import shutil
import pathspec
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_session import Session
from flask_socketio import SocketIO, emit

# Load environment variables from .env file
load_dotenv()

# --- App Initialization ---
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
socketio = SocketIO(app, manage_session=False)

# --- GitHub OAuth Configuration ---
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"

class GitHubUploader:
    """Handles GitHub API operations for repository creation and file uploads."""
    
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def get_user_info(self):
        """Get authenticated user information."""
        response = requests.get(f'{GITHUB_API_URL}/user', headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_repository(self, repo_name, private=False):
        """Create a new GitHub repository."""
        url = f'{GITHUB_API_URL}/user/repos'
        data = {'name': repo_name, 'private': private}
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 422:
            raise Exception(f"Repository '{repo_name}' already exists or name is invalid.")
        response.raise_for_status()
        return response.json()

    def get_branch(self, repo_owner, repo_name, branch):
        """Get a branch from the repository."""
        url = f'{GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/branches/{branch}'
        response = requests.get(url, headers=self.headers)
        return response.json() if response.status_code == 200 else None

    def create_branch(self, repo_owner, repo_name, new_branch, base_branch='main'):
        """Create a new branch in the repository."""
        base_branch_info = self.get_branch(repo_owner, repo_name, base_branch)
        if not base_branch_info:
             # If the main branch does not exist, create the first commit to create it.
            self.upload_file(repo_owner, repo_name, '.placeholder', 'Initial commit', b'init', base_branch)
            base_branch_info = self.get_branch(repo_owner, repo_name, base_branch)

        sha = base_branch_info['commit']['sha']
        url = f'{GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/git/refs'
        data = {'ref': f'refs/heads/{new_branch}', 'sha': sha}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()


    def upload_file(self, repo_owner, repo_name, file_path, message, content, branch):
        """Upload a single file to GitHub repository."""
        url = f'{GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/contents/{file_path}'
        encoded_content = base64.b64encode(content).decode('utf-8')
        data = {'message': message, 'content': encoded_content, 'branch': branch}
        response = requests.put(url, headers=self.headers, json=data)
        response.raise_for_status()

    def upload_directory(self, repo_owner, repo_name, directory_path, branch, commit_message):
        """Recursively upload all files in a directory to GitHub, respecting .gitignore."""

        # Find and parse .gitignore if it exists
        gitignore_path = os.path.join(directory_path, '.gitignore')
        spec = None
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                spec = pathspec.PathSpec.from_lines('gitwildmatch', f)

        # Get a list of all files to be uploaded
        all_files = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory_path).replace('\\', '/')
                
                if spec and spec.match_file(relative_path):
                    continue
                if relative_path == '.gitignore' and spec:
                    continue
                all_files.append((file_path, relative_path))
        
        total_files = len(all_files)
        uploaded_files_count = 0

        for i, (file_path, relative_path) in enumerate(all_files):
            progress = int(((i + 1) / total_files) * 100) if total_files > 0 else 0
            socketio.emit('progress', {'data': f'Uploading: {relative_path}', 'progress': progress})
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                self.upload_file(repo_owner, repo_name, relative_path, commit_message, content, branch)
                uploaded_files_count += 1
            except Exception as e:
                socketio.emit('error', {'data': f"Error uploading {relative_path}: {e}"})
        
        return uploaded_files_count

# --- Helper Functions ---
def sanitize_repo_name(name):
    sanitized = ''.join(c if c.isalnum() or c in ['-', '_', '.'] else '-' for c in name)
    return '-'.join(filter(None, sanitized.split('-')))

def extract_zip_file(zip_file_path, extract_to):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

# --- Flask Routes ---
@app.route('/')
def index():
    if 'github_token' in session:
        user_info = session.get('user_info', {})
        return render_template('index.html', logged_in=True, user=user_info, current_year=datetime.now().year)
    return render_template('index.html', logged_in=False, current_year=datetime.now().year)

@app.route('/login')
def login():
    scope = "repo,user"
    return redirect(f"{GITHUB_AUTHORIZE_URL}?client_id={GITHUB_CLIENT_ID}&scope={scope}")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/github/callback')
def github_callback():
    code = request.args.get('code')
    if not code:
        return "Error: No code provided.", 400
    
    headers = {'Accept': 'application/json'}
    data = {
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': code
    }
    
    token_response = requests.post(GITHUB_TOKEN_URL, headers=headers, data=data)
    token_json = token_response.json()
    
    access_token = token_json.get('access_token')
    if not access_token:
        return "Error: Could not retrieve access token.", 400
        
    session['github_token'] = access_token
    
    # Get user info and store it in session
    uploader = GitHubUploader(access_token)
    try:
        user_info = uploader.get_user_info()
        session['user_info'] = {
            'login': user_info.get('login'),
            'avatar_url': user_info.get('avatar_url'),
            'html_url': user_info.get('html_url')
        }
    except Exception:
        # Handle case where user info can't be fetched
        session['user_info'] = {}

    return redirect(url_for('index'))

# --- Socket.IO Event Handlers ---
@socketio.on('upload_project')
def handle_upload_event(json_data):
    if 'github_token' not in session:
        emit('error', {'data': 'Authentication error. Please log in again.'})
        return

    temp_dir = tempfile.mkdtemp()
    
    try:
        # Extract data from the client
        zip_file_b64 = json_data['file']
        repo_name = sanitize_repo_name(json_data['repo_name'])
        visibility = json_data['visibility']
        branch = json_data.get('branch', 'main').strip()
        commit_message = json_data.get('commit_message', 'Initial commit')
        
        if not repo_name:
            emit('error', {'data': 'Repository name is required.'})
            return

        # Decode and save the zip file
        zip_data = base64.b64decode(zip_file_b64)
        zip_path = os.path.join(temp_dir, 'uploaded.zip')
        with open(zip_path, 'wb') as f:
            f.write(zip_data)
        
        extract_path = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_path)
        extract_zip_file(zip_path, extract_path)
        
        uploader = GitHubUploader(session['github_token'])
        user_info = session['user_info']
        repo_owner = user_info['login']
        
        emit('progress', {'data': f"Creating repository '{repo_name}'..."})
        repo_info = uploader.create_repository(repo_name, visibility == 'private')
        
        # If a custom branch is specified, create it
        if branch != 'main':
            emit('progress', {'data': f"Creating branch '{branch}'..."})
            uploader.create_branch(repo_owner, repo_name, branch)

        emit('progress', {'data': 'Starting file upload...'})
        uploaded_count = uploader.upload_directory(repo_owner, repo_name, extract_path, branch, commit_message)
        
        result = {
            'data': f'Success! Uploaded {uploaded_count} files to the "{branch}" branch.',
            'repo_url': repo_info['html_url']
        }
        emit('success', result)

    except Exception as e:
        emit('error', {'data': str(e)})
    finally:
        shutil.rmtree(temp_dir)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
