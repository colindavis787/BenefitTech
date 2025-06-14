from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
import yaml
from yaml.loader import SafeLoader
import bcrypt
import os
import logging
import webbrowser
import argparse

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv('FLASK_SECRET_KEY', '2f0782073d00457d2c4ed7576e6771c8')

# Load credentials
try:
    logger.debug("Attempting to load credentials.yaml")
    credentials_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'credentials.yaml')
    with open(credentials_path) as file:
        config = yaml.load(file, Loader=SafeLoader)
    users = config['credentials']['usernames']
    logger.debug("Credentials loaded successfully")
except Exception as e:
    logger.error(f"Failed to load credentials.yaml: {str(e)}")
    users = {}

@app.route('/')
def index():
    try:
        logger.debug("Attempting to render index.html")
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'templates', 'index.html')):
            logger.error("index.html not found in templates directory")
            return Response("Template index.html not found", status=500)
        result = render_template('index.html')
        logger.debug("Successfully rendered index.html")
        return result
    except Exception as e:
        logger.error(f"Error rendering homepage: {str(e)}")
        return Response(f"Error rendering homepage: {str(e)}", status=500)

@app.route('/test')
def test():
    try:
        logger.debug("Accessing test route")
        return Response("Test route working", status=200)
    except Exception as e:
        logger.error(f"Error in test route: {str(e)}")
        return Response(f"Error in test: {str(e)}", status=500)

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        logger.debug("Accessing login route")
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'templates', 'login.html')):
            logger.error("login.html not found in templates directory")
            return Response("Template login.html not found", status=500)
        if not users:
            logger.error("No users loaded from credentials.yaml")
            flash('Authentication system is unavailable. Please contact support.', 'error')
            return render_template('login.html')
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            logger.debug(f"Login attempt for username: {username}")
            if not username or not password:
                logger.warning("Missing username or password")
                flash('Username and password required', 'error')
                return render_template('login.html')
            if len(username) > 50 or len(password) > 50:
                logger.warning("Login input too long")
                flash('Input too long', 'error')
                return render_template('login.html')
            if username not in users:
                logger.warning(f"Username {username} not found")
                flash('Invalid username or password', 'error')
                return render_template('login.html')
            stored_password = users[username]['password']
            logger.debug(f"Stored password hash: {stored_password}")
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                session['authentication_status'] = True
                session['username'] = username
                session['name'] = users[username]['name']
                logger.info(f"Successful login for {username}")
                return redirect(url_for('dashboard'))
            else:
                logger.warning("Invalid password")
                flash('Invalid username or password', 'error')
                return render_template('login.html')
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        flash(f'Login error: {str(e)}', 'error')
        return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    try:
        logger.debug("Accessing dashboard route")
        if not os.path.exists(os.path.join(os.path.dirname(__file__), 'templates', 'dashboard.html')):
            logger.error("dashboard.html not found in templates directory")
            return Response("Template dashboard.html not found", status=500)
        if session.get('authentication_status'):
            streamlit_url = os.getenv('STREAMLIT_URL', 'https://benefittech.streamlit.app/?embedded=true')
            try:
                import requests
                response = requests.head(streamlit_url, timeout=5)
                if response.status_code != 200:
                    logger.warning(f"Streamlit app unavailable at {streamlit_url}, status code: {response.status_code}")
                    flash('Streamlit app is currently unavailable. Please try again later.', 'error')
            except requests.RequestException as e:
                logger.error(f"Failed to reach Streamlit app: {str(e)}")
                flash('Streamlit app is currently unavailable. Please try again later.', 'error')
            return render_template('dashboard.html', username=session['username'], streamlit_url=streamlit_url)
        logger.warning("Unauthorized dashboard access, redirecting to login")
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}")
        return Response(f"Error in dashboard: {str(e)}", status=500)

@app.route('/logout', methods=['POST'])
def logout():
    try:
        logger.debug("Logging out")
        session.pop('authentication_status', None)
        session.pop('username', None)
        session.pop('name', None)
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Error in logout route: {str(e)}")
        return Response(f"Error in logout: {str(e)}", status=500)

@app.route('/streamlit')
def streamlit_app():
    try:
        logger.debug("Accessing streamlit route")
        if session.get('authentication_status'):
            streamlit_url = os.getenv('STREAMLIT_URL', 'https://benefittech.streamlit.app/?embedded=true')
            return redirect(streamlit_url)
        logger.warning("Unauthorized streamlit access, redirecting to login")
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error in streamlit route: {str(e)}")
        flash(f'Streamlit error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Flask app')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the app on')
    args = parser.parse_args()
    logger.debug(f"Starting Flask app on port {args.port}")
    webbrowser.open(f'http://localhost:{args.port}')
    app.run(debug=True, port=args.port)
