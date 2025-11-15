from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import re
from functools import wraps
import io
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///polling_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Ensure upload folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'polls'), exist_ok=True)


# -------------------- DATABASE MODELS --------------------
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    profile_picture = db.Column(db.String(200), default='default.png')
    name_changed = db.Column(db.Boolean, default=False)
    anonymous_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

    polls = db.relationship('Poll', backref='creator', lazy=True)
    votes = db.relationship('Vote', backref='voter', lazy=True)
    comments = db.relationship('Comment', backref='commenter', lazy=True)
    reactions = db.relationship('Reaction', backref='user', lazy=True)
    badges = db.relationship('Badge', backref='user', lazy=True)


class Poll(db.Model):
    __tablename__ = 'polls'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='General')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_masked = db.Column(db.Boolean, default=False)
    is_anonymous_voting = db.Column(db.Boolean, default=False)
    scheduled_for = db.Column(db.DateTime, nullable=True)
    image = db.Column(db.String(200), nullable=True)

    options = db.relationship('Option', backref='poll', lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='poll', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='poll', lazy=True, cascade='all, delete-orphan')
    reactions = db.relationship('Reaction', backref='poll', lazy=True, cascade='all, delete-orphan')


class Option(db.Model):
    __tablename__ = 'options'
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'), nullable=False)
    option_text = db.Column(db.String(300), nullable=False)
    image = db.Column(db.String(200), nullable=True)
    votes = db.relationship('Vote', backref='option', lazy=True, cascade='all, delete-orphan')


class Vote(db.Model):
    __tablename__ = 'votes'
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('options.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_anonymous = db.Column(db.Boolean, default=False)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    sentiment_score = db.Column(db.Float, default=0.0)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_reported = db.Column(db.Boolean, default=False)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)


class Reaction(db.Model):
    __tablename__ = 'reactions'
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey('polls.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Now nullable for guest users
    email = db.Column(db.String(120), nullable=True)  # Added for guest users
    reaction_type = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Badge(db.Model):
    __tablename__ = 'badges'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    badge_type = db.Column(db.String(50), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------- LOGIN MANAGER --------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------- HELPERS --------------------
def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Valid password"


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


def check_and_award_badges(user):
    vote_count = Vote.query.filter_by(user_id=user.id).count()
    if vote_count >= 10 and not Badge.query.filter_by(user_id=user.id, badge_type='Active Voter').first():
        db.session.add(Badge(user_id=user.id, badge_type='Active Voter'))
    poll_count = Poll.query.filter_by(created_by=user.id).count()
    if poll_count >= 5 and not Badge.query.filter_by(user_id=user.id, badge_type='Poll Creator').first():
        db.session.add(Badge(user_id=user.id, badge_type='Poll Creator'))
    comment_count = Comment.query.filter_by(user_id=user.id).count()
    if comment_count >= 20 and not Badge.query.filter_by(user_id=user.id, badge_type='Top Commenter').first():
        db.session.add(Badge(user_id=user.id, badge_type='Top Commenter'))
    db.session.commit()


# -------------------- ROUTES --------------------
@app.route('/')
def index():
    search_query = request.args.get('search', '')
    category = request.args.get('category', '')
    sort_by = request.args.get('sort', 'trending')
    now = datetime.utcnow()

    query = Poll.query.filter(db.or_(Poll.scheduled_for == None, Poll.scheduled_for <= now))

    if search_query:
        query = query.filter(db.or_(Poll.title.contains(search_query), Poll.description.contains(search_query)))
    if category:
        query = query.filter_by(category=category)

    if sort_by == 'trending':
        polls = query.all()
        polls_with_votes = [(p, Vote.query.filter_by(poll_id=p.id).count()) for p in polls]
        polls_with_votes.sort(key=lambda x: x[1], reverse=True)
        polls = [p[0] for p in polls_with_votes]
    elif sort_by == 'recent':
        polls = query.order_by(Poll.created_at.desc()).all()
    else:
        polls = query.all()

    categories = ['General', 'Politics', 'Sports', 'Technology', 'Entertainment', 'Health', 'Education', 'Business']

    total_polls = len(polls)
    total_votes = Vote.query.count()
    total_comments = Comment.query.count()

    return render_template('index.html', polls=polls, categories=categories,
                           current_category=category, search_query=search_query, now=now,
                           total_polls=total_polls, total_votes=total_votes, total_comments=total_comments)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for('register'))

        valid, message = validate_password(password)
        if not valid:
            flash(message, "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for('register'))

        new_user = User(name=name, email=email, phone=phone, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_name':
            if current_user.name_changed:
                flash('You can only change your name once', 'warning')
            else:
                new_name = request.form.get('name')
                if new_name:
                    current_user.name = new_name
                    current_user.name_changed = True
                    db.session.commit()
                    flash('Name updated successfully', 'success')
        elif action == 'upload_picture':
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file.filename:
                    filename = secure_filename(f"user_{current_user.id}_{file.filename}")
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'profiles', filename)
                    file.save(filepath)
                    current_user.profile_picture = filename
                    db.session.commit()
                    flash('Profile picture updated', 'success')
        return redirect(url_for('profile'))

    user_polls = Poll.query.filter_by(created_by=current_user.id).all()
    user_votes = Vote.query.filter_by(user_id=current_user.id).count()
    user_comments = Comment.query.filter_by(user_id=current_user.id).count()
    user_badges = Badge.query.filter_by(user_id=current_user.id).all()
    now = datetime.utcnow()

    return render_template('profile.html', user_polls=user_polls, user_votes=user_votes,
                           user_comments=user_comments, user_badges=user_badges, now=now)


@app.route('/create_poll', methods=['GET', 'POST'])
@login_required
def create_poll():
    categories = ['General', 'Politics', 'Sports', 'Technology', 'Entertainment', 'Health', 'Education', 'Business']

    if request.method == 'POST':
        title = (request.form.get('title') or '').strip()
        description = (request.form.get('description') or '').strip()
        category = request.form.get('category') or 'General'
        is_masked = bool(request.form.get('is_masked'))
        is_anonymous_voting = bool(request.form.get('is_anonymous_voting'))

        options_text = request.form.getlist('options[]')
        options_text = [opt.strip() for opt in options_text if opt and opt.strip()]
        option_images = request.files.getlist('option_images[]')

        if not title or len(options_text) < 2:
            flash("Poll title and at least two options are required.", "danger")
            return redirect(url_for('create_poll'))

        poll_image_file = request.files.get('poll_image')
        poll_image_filename = None
        if poll_image_file and poll_image_file.filename:
            poll_image_filename = secure_filename(f"{datetime.utcnow().timestamp()}_{poll_image_file.filename}")
            poll_image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'polls', poll_image_filename))

        expiration = request.form.get('expiration')
        expires_at = None
        if expiration and expiration != 'never':
            if expiration == 'custom':
                hours = request.form.get('custom_hours', type=int)
                if hours and hours > 0:
                    expires_at = datetime.utcnow() + timedelta(hours=hours)
            else:
                try:
                    expires_at = datetime.utcnow() + timedelta(hours=int(expiration))
                except Exception:
                    expires_at = None

        scheduled_date = request.form.get('scheduled_date')
        scheduled_for = None
        if scheduled_date:
            try:
                scheduled_for = datetime.strptime(scheduled_date, '%Y-%m-%dT%H:%M')
            except Exception:
                scheduled_for = None

        poll = Poll(
            title=title,
            description=description,
            category=category,
            created_by=current_user.id,
            is_masked=is_masked,
            is_anonymous_voting=is_anonymous_voting,
            expires_at=expires_at,
            scheduled_for=scheduled_for,
            image=poll_image_filename
        )
        db.session.add(poll)
        db.session.commit()

        for i, opt_text in enumerate(options_text):
            opt_image_file = option_images[i] if i < len(option_images) else None
            opt_image_filename = None
            if opt_image_file and getattr(opt_image_file, 'filename', None):
                opt_image_filename = secure_filename(f"{datetime.utcnow().timestamp()}_{opt_image_file.filename}")
                opt_image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'polls', opt_image_filename))

            option = Option(poll_id=poll.id, option_text=opt_text, image=opt_image_filename)
            db.session.add(option)

        db.session.commit()
        check_and_award_badges(current_user)
        flash("Poll created successfully!", "success")
        return redirect(url_for('view_poll', poll_id=poll.id))

    return render_template('create_poll.html', categories=categories)


@app.route('/poll/<int:poll_id>')
def view_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)

    if poll.scheduled_for and poll.scheduled_for > datetime.utcnow():
        if not current_user.is_authenticated or current_user.id != poll.created_by:
            flash('This poll is scheduled for future', 'info')
            return redirect(url_for('index'))

    is_expired = bool(poll.expires_at and poll.expires_at < datetime.utcnow())

    total_votes = Vote.query.filter_by(poll_id=poll_id).count()
    option_votes = {}
    for option in poll.options:
        c = Vote.query.filter_by(option_id=option.id).count()
        option_votes[option.id] = {
            'count': c,
            'percentage': (c / total_votes * 100) if total_votes > 0 else 0
        }

    user_voted = False
    if current_user.is_authenticated:
        user_voted = Vote.query.filter_by(poll_id=poll_id, user_id=current_user.id).first() is not None

    comments = Comment.query.filter_by(poll_id=poll_id, parent_id=None).order_by(Comment.timestamp.desc()).all()

    reactions = {}
    for rt in ['like', 'love', 'wow', 'sad', 'angry']:
        reactions[rt] = Reaction.query.filter_by(poll_id=poll_id, reaction_type=rt).count()

    user_reaction = None
    if current_user.is_authenticated:
        r = Reaction.query.filter_by(poll_id=poll_id, user_id=current_user.id).first()
        if r:
            user_reaction = r.reaction_type

    return render_template('view_poll.html', poll=poll, option_votes=option_votes,
                           total_votes=total_votes, user_voted=user_voted,
                           is_expired=is_expired, comments=comments,
                           reactions=reactions, user_reaction=user_reaction)


@app.route('/vote/<int:poll_id>', methods=['POST'])
def vote(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    option_id = request.form.get('option_id', type=int)

    if not option_id:
        flash('Please select an option', 'warning')
        return redirect(url_for('view_poll', poll_id=poll_id))

    if poll.expires_at and poll.expires_at < datetime.utcnow():
        flash('This poll has expired', 'danger')
        return redirect(url_for('view_poll', poll_id=poll_id))

    if poll.scheduled_for and poll.scheduled_for > datetime.utcnow():
        if not current_user.is_authenticated or current_user.id != poll.created_by:
            flash('This poll is scheduled for future', 'info')
            return redirect(url_for('index'))

    if current_user.is_authenticated:
        existing_vote = Vote.query.filter_by(poll_id=poll_id, user_id=current_user.id).first()
        if existing_vote:
            flash('You have already voted on this poll', 'warning')
            return redirect(url_for('view_poll', poll_id=poll_id))

        vote = Vote(poll_id=poll_id, option_id=option_id, user_id=current_user.id,
                    is_anonymous=poll.is_anonymous_voting)
        db.session.add(vote)
        db.session.commit()
        check_and_award_badges(current_user)
    else:
        email = request.form.get('email')
        if not email:
            flash('Email is required for voting', 'warning')
            return redirect(url_for('view_poll', poll_id=poll_id))

        existing_vote = Vote.query.filter_by(poll_id=poll_id, email=email).first()
        if existing_vote:
            flash('This email has already voted on this poll', 'warning')
            return redirect(url_for('view_poll', poll_id=poll_id))

        vote = Vote(poll_id=poll_id, option_id=option_id, email=email)
        db.session.add(vote)
        db.session.commit()

    flash('Vote recorded successfully!', 'success')
    return redirect(url_for('view_poll', poll_id=poll_id))


@app.route('/comment/<int:poll_id>', methods=['POST'])
@login_required
def add_comment(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    comment_text = request.form.get('comment')
    parent_id = request.form.get('parent_id', type=int)

    if not comment_text or not comment_text.strip():
        flash('Comment cannot be empty', 'warning')
        return redirect(url_for('view_poll', poll_id=poll_id))

    user_comments_count = Comment.query.filter_by(poll_id=poll_id, user_id=current_user.id).count()
    if user_comments_count >= 5:
        flash('Maximum 5 comments per poll allowed', 'warning')
        return redirect(url_for('view_poll', poll_id=poll_id))

    sentiment_score = 0.0
    positive_words = ['good', 'great', 'excellent', 'awesome', 'love', 'best', 'amazing']
    negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'poor']
    txt = comment_text.lower()
    for w in positive_words:
        if w in txt:
            sentiment_score += 0.1
    for w in negative_words:
        if w in txt:
            sentiment_score -= 0.1

    comment = Comment(poll_id=poll_id, user_id=current_user.id, comment_text=comment_text,
                      sentiment_score=sentiment_score, parent_id=parent_id)
    db.session.add(comment)
    db.session.commit()

    check_and_award_badges(current_user)
    flash('Comment added successfully!', 'success')
    return redirect(url_for('view_poll', poll_id=poll_id))


@app.route('/react/<int:poll_id>', methods=['POST'])
def add_reaction(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    reaction_type = request.form.get('reaction_type')

    if reaction_type not in ['like', 'love', 'wow', 'sad', 'angry']:
        return jsonify({'success': False, 'message': 'Invalid reaction type'})

    if current_user.is_authenticated:
        existing = Reaction.query.filter_by(poll_id=poll_id, user_id=current_user.id).first()

        if existing:
            if existing.reaction_type == reaction_type:
                db.session.delete(existing)
                db.session.commit()
                return jsonify({'success': True, 'action': 'removed'})
            else:
                existing.reaction_type = reaction_type
                db.session.commit()
                return jsonify({'success': True, 'action': 'updated'})
        else:
            r = Reaction(poll_id=poll_id, user_id=current_user.id, reaction_type=reaction_type)
            db.session.add(r)
            db.session.commit()
            return jsonify({'success': True, 'action': 'added'})
    else:
        email = request.form.get('email')

        if not email or not email.strip():
            return jsonify({'success': False, 'message': 'Email is required for reactions', 'require_email': True})

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'success': False, 'message': 'Invalid email format', 'require_email': True})

        existing = Reaction.query.filter_by(poll_id=poll_id, email=email).first()

        if existing:
            if existing.reaction_type == reaction_type:
                db.session.delete(existing)
                db.session.commit()
                return jsonify({'success': True, 'action': 'removed', 'message': 'Reaction removed'})
            else:
                existing.reaction_type = reaction_type
                db.session.commit()
                return jsonify({'success': True, 'action': 'updated', 'message': 'Reaction updated'})
        else:
            r = Reaction(poll_id=poll_id, email=email, reaction_type=reaction_type)
            db.session.add(r)
            db.session.commit()
            return jsonify({'success': True, 'action': 'added', 'message': 'Reaction added successfully'})


@app.route('/export_results/<int:poll_id>')
def export_results(poll_id):
    poll = Poll.query.get_or_404(poll_id)

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Poll Results: {poll.title}")

    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, f"Category: {poll.category}")
    p.drawString(50, height - 100, f"Created: {poll.created_at.strftime('%Y-%m-%d %H:%M')}")

    total_votes = Vote.query.filter_by(poll_id=poll_id).count()
    p.drawString(50, height - 130, f"Total Votes: {total_votes}")

    y_position = height - 170
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y_position, "Results:")
    y_position -= 30

    p.setFont("Helvetica", 11)
    for option in poll.options:
        count = Vote.query.filter_by(option_id=option.id).count()
        percentage = (count / total_votes * 100) if total_votes > 0 else 0
        p.drawString(60, y_position, f"{option.option_text}: {count} votes ({percentage:.1f}%)")
        y_position -= 20
        if y_position < 100:
            p.showPage()
            y_position = height - 50

    p.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f'poll_{poll_id}_results.pdf',
                     mimetype='application/pdf')


@app.route('/leaderboard')
def leaderboard():
    top_voters = db.session.query(User, db.func.count(Vote.id).label('vote_count')) \
        .join(Vote).group_by(User.id).order_by(db.desc('vote_count')).limit(10).all()

    top_creators = db.session.query(User, db.func.count(Poll.id).label('poll_count')) \
        .join(Poll, Poll.created_by == User.id).group_by(User.id).order_by(db.desc('poll_count')).limit(10).all()

    top_commenters = db.session.query(User, db.func.count(Comment.id).label('comment_count')) \
        .join(Comment).group_by(User.id).order_by(db.desc('comment_count')).limit(10).all()

    polls = Poll.query.all()
    polls_with_votes = [(p, Vote.query.filter_by(poll_id=p.id).count()) for p in polls]
    polls_with_votes.sort(key=lambda x: x[1], reverse=True)
    trending_polls = polls_with_votes[:10]

    return render_template('leaderboard.html', top_voters=top_voters,
                           top_creators=top_creators, top_commenters=top_commenters,
                           trending_polls=trending_polls)


@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_users = User.query.count()
    total_polls = Poll.query.count()
    total_votes = Vote.query.count()
    total_comments = Comment.query.count()
    reported_comments = Comment.query.filter_by(is_reported=True).all()

    recent_polls = Poll.query.order_by(Poll.created_at.desc()).limit(5).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    return render_template('admin_dashboard.html', total_users=total_users,
                           total_polls=total_polls, total_votes=total_votes,
                           total_comments=total_comments, reported_comments=reported_comments,
                           recent_polls=recent_polls, recent_users=recent_users)


@app.route('/admin/delete_poll/<int:poll_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    db.session.delete(poll)
    db.session.commit()
    flash('Poll deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/report_comment/<int:comment_id>', methods=['POST'])
@login_required
def report_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.is_reported = True
    db.session.commit()
    flash('Comment reported to admin', 'success')
    return redirect(url_for('view_poll', poll_id=comment.poll_id))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(email='admin@polls.com').first()
        if not admin:
            admin = User(name='Admin', email='admin@polls.com',
                         password_hash=generate_password_hash('Admin@123'),
                         is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin@polls.com / Admin@123")
    app.run(debug=True, host='0.0.0.0', port=5000)