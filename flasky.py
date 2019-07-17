import os
from flask_migrate import Migrate
from app import create_app, db
from app.models import User, Post, Group, Join, Message
import json

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Post=Post, Group=Group, Join=Join, Message=Message)

@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

@app.template_filter() # Jinja2 custom filter
def str_to_dic(str):
    return json.loads(str)
