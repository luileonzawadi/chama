from flask import Flask, render_template
from dotenv import load_dotenv
import os
from models import db, Member

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__, template_folder='template')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    # Use SQLite instead of PostgreSQL for simplicity
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chama.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the db with the app
    db.init_app(app)
    
    @app.route('/')
    def index():
        members = Member.query.all()
        return render_template('member.html', members=members)
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True)