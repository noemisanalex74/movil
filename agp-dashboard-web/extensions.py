from flask_apscheduler import APScheduler
from flask_babel import Babel
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy


class MockScheduler:
    def init_app(self, app):
        pass

    def start(self):
        pass

    def shutdown(self):
        pass

    @property
    def running(self):
        return False

db = SQLAlchemy()
socketio = SocketIO()
scheduler = None # Initialize to None or a placeholder
migrate = Migrate()
babel = Babel()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    from models import User

    return User.query.get(int(user_id))


def init_app(app):
    """
    Initialize Flask extensions.
    """
    global scheduler  # Declare intent to modify global scheduler
    db.init_app(app)
    socketio.init_app(app)
    babel.init_app(app)
    login_manager.init_app(app)
    if not app.config.get("TESTING"):
        scheduler = APScheduler() # Initialize real scheduler
        scheduler.init_app(app)
        # Start the scheduler if it's not already running
        if not scheduler.running:
            with app.app_context():
                scheduler.start()
    else:
        scheduler = MockScheduler() # Initialize mock scheduler
