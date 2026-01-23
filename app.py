#!/usr/bin/env python3
"""
Project Dashboard - Web GUI for viewing Workhorse2025 projects
"""
import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('DASHBOARD_SECRET_KEY', 'workhorse-dev-key-change-me')

# Authentication credentials
DASHBOARD_USER = os.environ.get('DASHBOARD_USER', 'dragon')
DASHBOARD_PASS = os.environ.get('DASHBOARD_PASS', 'dragon123')

# Project root directory
PROJECT_ROOT = '/home/dragon'


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_projects():
    """Scan the project directory and return information about sub-projects"""
    projects = []

    # Main projects on Workhorse2025
    main_projects = {
        'threat-intel-aggregator': 'Threat Intelligence Aggregator with Discord integration',
        'trading': 'Freqtrade Trading Bot and Strategies',
        'fishtracker': 'Fish Tracking Application',
        'sectop': 'Security Operations Tools',
    }

    # Claude/Tooling areas
    tooling_areas = {
        'claude-git-control': 'Claude Git Workflows and Templates',
        'claude-backups': 'Claude Session Backups',
        'project-dashboard': 'Project Dashboard (This App)',
    }

    for dirname, description in main_projects.items():
        dir_path = os.path.join(PROJECT_ROOT, dirname)
        if os.path.exists(dir_path):
            projects.append({
                'name': dirname,
                'description': description,
                'type': 'project',
                'path': dirname,
                'files_count': count_files(dir_path),
                'last_modified': get_last_modified(dir_path),
                'status': get_project_status(dir_path)
            })

    for dirname, description in tooling_areas.items():
        dir_path = os.path.join(PROJECT_ROOT, dirname)
        if os.path.exists(dir_path):
            projects.append({
                'name': dirname,
                'description': description,
                'type': 'tooling',
                'path': dirname,
                'files_count': count_files(dir_path),
                'last_modified': get_last_modified(dir_path),
                'status': 'active'
            })

    return projects


def get_project_status(directory):
    """Determine project status based on git or recent activity"""
    try:
        git_dir = os.path.join(directory, '.git')
        if os.path.exists(git_dir):
            return 'active'
        return 'active'
    except:
        return 'unknown'


def count_files(directory):
    """Count total files in a directory recursively"""
    count = 0
    try:
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', '.git']]
            count += len(files)
    except (PermissionError, FileNotFoundError):
        pass
    return count


def get_last_modified(directory):
    """Get the last modified time of the most recent file in directory"""
    try:
        latest = 0
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv', '.git']]
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                    if mtime > latest:
                        latest = mtime
                except (PermissionError, FileNotFoundError):
                    continue

        if latest > 0:
            return datetime.fromtimestamp(latest).strftime('%Y-%m-%d %H:%M')
        return 'Unknown'
    except Exception:
        return 'Unknown'


@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/projects')
@login_required
def api_projects():
    """API endpoint to get projects data"""
    projects = get_projects()
    return jsonify(projects)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == DASHBOARD_USER and password == DASHBOARD_PASS:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/browse')
@app.route('/browse/<path:subpath>')
@login_required
def browse(subpath=''):
    """Browse directory contents"""
    return render_template('browse.html', initial_path=subpath)


@app.route('/api/browse')
@app.route('/api/browse/<path:subpath>')
@login_required
def api_browse(subpath=''):
    """API endpoint to browse directory"""
    if '..' in subpath or subpath.startswith('/'):
        return jsonify({'error': 'Invalid path'}), 400

    target_path = os.path.join(PROJECT_ROOT, subpath) if subpath else PROJECT_ROOT

    real_target = os.path.realpath(target_path)
    real_root = os.path.realpath(PROJECT_ROOT)
    if not real_target.startswith(real_root):
        return jsonify({'error': 'Access denied'}), 403

    if not os.path.exists(target_path):
        return jsonify({'error': 'Path not found'}), 404

    if not os.path.isdir(target_path):
        return jsonify({'error': 'Not a directory'}), 400

    try:
        items = []
        entries = sorted(os.listdir(target_path))

        for entry in entries:
            if entry.startswith('.') or entry in ['node_modules', '__pycache__', 'venv']:
                continue

            full_path = os.path.join(target_path, entry)
            rel_path = os.path.join(subpath, entry) if subpath else entry

            try:
                stat = os.stat(full_path)
                is_dir = os.path.isdir(full_path)

                items.append({
                    'name': entry,
                    'path': rel_path,
                    'type': 'directory' if is_dir else 'file',
                    'size': stat.st_size if not is_dir else None,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
            except (PermissionError, FileNotFoundError):
                continue

        directories = [item for item in items if item['type'] == 'directory']
        files = [item for item in items if item['type'] == 'file']

        return jsonify({
            'current_path': subpath,
            'items': directories + files,
            'parent_path': os.path.dirname(subpath) if subpath else None
        })

    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/file/<path:filepath>')
@login_required
def api_read_file(filepath):
    """API endpoint to read file contents"""
    if '..' in filepath or filepath.startswith('/'):
        return jsonify({'error': 'Invalid path'}), 400

    target_path = os.path.join(PROJECT_ROOT, filepath)

    real_target = os.path.realpath(target_path)
    real_root = os.path.realpath(PROJECT_ROOT)
    if not real_target.startswith(real_root):
        return jsonify({'error': 'Access denied'}), 403

    if not os.path.exists(target_path):
        return jsonify({'error': 'File not found'}), 404

    if not os.path.isfile(target_path):
        return jsonify({'error': 'Not a file'}), 400

    try:
        file_size = os.path.getsize(target_path)
        if file_size > 1024 * 1024:
            return jsonify({
                'error': 'File too large',
                'message': f'File size: {file_size / 1024 / 1024:.2f}MB. Maximum: 1MB'
            }), 413

        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return jsonify({
                'name': os.path.basename(filepath),
                'path': filepath,
                'content': content,
                'size': file_size,
                'type': 'text'
            })
        except UnicodeDecodeError:
            return jsonify({
                'error': 'Binary file',
                'message': 'Cannot display binary files',
                'name': os.path.basename(filepath),
                'path': filepath,
                'size': file_size,
                'type': 'binary'
            }), 415

    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Workhorse2025 Project Dashboard...")
    print(f"Credentials - User: {DASHBOARD_USER}")
    print("Access at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
