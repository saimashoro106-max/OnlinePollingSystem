"""
Database Initialization Script
Run this script to create database tables and add sample data
"""

from app import app, db, User, Poll, Option, Vote, Comment, Reaction, Badge
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random


def create_tables():
    """Create all database tables"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")


def create_admin_user():
    """Create default admin user"""
    with app.app_context():
        admin = User.query.filter_by(email='admin@polls.com').first()
        if not admin:
            print("Creating admin user...")
            admin = User(
                name='Admin',
                email='admin@polls.com',
                password_hash=generate_password_hash('Admin@123'),
                is_admin=True,
                created_at=datetime.utcnow()
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin user created!")
            print("  Email: admin@polls.com")
            print("  Password: Admin@123")
        else:
            print("✓ Admin user already exists")


def create_sample_users():
    """Create sample users for testing"""
    with app.app_context():
        sample_users = [
            {'name': 'John Doe', 'email': 'john@example.com', 'phone': '1234567890'},
            {'name': 'Jane Smith', 'email': 'jane@example.com', 'phone': '0987654321'},
            {'name': 'Bob Johnson', 'email': 'bob@example.com', 'phone': '1122334455'},
            {'name': 'Alice Williams', 'email': 'alice@example.com', 'phone': '5566778899'},
            {'name': 'Charlie Brown', 'email': 'charlie@example.com', 'phone': '9988776655'}
        ]

        print("Creating sample users...")
        for user_data in sample_users:
            existing = User.query.filter_by(email=user_data['email']).first()
            if not existing:
                user = User(
                    name=user_data['name'],
                    email=user_data['email'],
                    phone=user_data['phone'],
                    password_hash=generate_password_hash('Test@123'),
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                )
                db.session.add(user)

        db.session.commit()
        print("✓ Sample users created! (Password for all: Test@123)")


def create_sample_polls():
    """Create sample polls with options"""
    with app.app_context():
        users = User.query.all()
        if not users:
            print("! No users found. Create users first.")
            return

        sample_polls = [
            {
                'title': 'What is your favorite programming language?',
                'description': 'Help us understand which programming language developers prefer the most in 2024.',
                'category': 'Technology',
                'options': ['Python', 'JavaScript', 'Java', 'C++', 'Go', 'Rust']
            },
            {
                'title': 'Best time for exercise?',
                'description': 'When do you prefer to work out?',
                'category': 'Health',
                'options': ['Morning', 'Afternoon', 'Evening', 'Night']
            },
            {
                'title': 'Remote work or Office?',
                'description': 'What is your preferred work environment?',
                'category': 'Business',
                'options': ['Fully Remote', 'Hybrid', 'Full-time Office', 'Flexible']
            },
            {
                'title': 'Favorite streaming platform?',
                'description': 'Which streaming service do you use the most?',
                'category': 'Entertainment',
                'options': ['Netflix', 'Amazon Prime', 'Disney+', 'HBO Max', 'Hulu']
            },
            {
                'title': 'Best way to learn?',
                'description': 'How do you prefer to learn new skills?',
                'category': 'Education',
                'options': ['Online Courses', 'Books', 'Video Tutorials', 'Practice Projects', 'Mentorship']
            },
            {
                'title': 'Favorite sport to watch?',
                'description': 'Which sport do you enjoy watching the most?',
                'category': 'Sports',
                'options': ['Football', 'Basketball', 'Cricket', 'Tennis', 'Baseball']
            },
            {
                'title': 'Should voting be mandatory?',
                'description': 'Do you think voting should be compulsory in elections?',
                'category': 'Politics',
                'options': ['Yes, it should be mandatory', 'No, it should be optional', 'Undecided']
            },
            {
                'title': 'Coffee or Tea?',
                'description': 'The eternal debate - what is your preferred hot beverage?',
                'category': 'General',
                'options': ['Coffee', 'Tea', 'Both', 'Neither']
            }
        ]

        print("Creating sample polls...")
        for poll_data in sample_polls:
            existing = Poll.query.filter_by(title=poll_data['title']).first()
            if not existing:
                creator = random.choice(users)
                poll = Poll(
                    title=poll_data['title'],
                    description=poll_data['description'],
                    category=poll_data['category'],
                    created_by=creator.id,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 10)),
                    expires_at=datetime.utcnow() + timedelta(days=random.randint(7, 30))
                )
                db.session.add(poll)
                db.session.flush()

                # Add options
                for option_text in poll_data['options']:
                    option = Option(poll_id=poll.id, option_text=option_text)
                    db.session.add(option)

        db.session.commit()
        print("✓ Sample polls created!")


def create_sample_votes():
    """Create sample votes"""
    with app.app_context():
        users = User.query.all()
        polls = Poll.query.all()

        if not users or not polls:
            print("! Need users and polls to create votes")
            return

        print("Creating sample votes...")
        vote_count = 0
        for poll in polls:
            # Random number of votes per poll
            num_votes = random.randint(5, len(users))
            voters = random.sample(users, min(num_votes, len(users)))

            for voter in voters:
                # Check if already voted
                existing_vote = Vote.query.filter_by(poll_id=poll.id, user_id=voter.id).first()
                if not existing_vote:
                    option = random.choice(poll.options)
                    vote = Vote(
                        poll_id=poll.id,
                        option_id=option.id,
                        user_id=voter.id,
                        timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 7))
                    )
                    db.session.add(vote)
                    vote_count += 1

        db.session.commit()
        print(f"✓ Created {vote_count} sample votes!")


def create_sample_comments():
    """Create sample comments"""
    with app.app_context():
        users = User.query.all()
        polls = Poll.query.all()

        if not users or not polls:
            print("! Need users and polls to create comments")
            return

        sample_comments = [
            "Great poll! Very interesting results.",
            "I completely agree with this.",
            "This is a tough choice!",
            "Interesting perspective on this topic.",
            "Thanks for creating this poll!",
            "The results are surprising.",
            "I have a different opinion on this.",
            "This poll made me think!",
            "Very relevant topic.",
            "Looking forward to the final results."
        ]

        print("Creating sample comments...")
        comment_count = 0
        for poll in polls[:5]:  # Add comments to first 5 polls
            num_comments = random.randint(2, 5)
            for _ in range(num_comments):
                user = random.choice(users)
                comment = Comment(
                    poll_id=poll.id,
                    user_id=user.id,
                    comment_text=random.choice(sample_comments),
                    sentiment_score=random.uniform(-0.3, 0.3),
                    timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 5))
                )
                db.session.add(comment)
                comment_count += 1

        db.session.commit()
        print(f"✓ Created {comment_count} sample comments!")


def create_sample_reactions():
    """Create sample reactions"""
    with app.app_context():
        users = User.query.all()
        polls = Poll.query.all()

        if not users or not polls:
            print("! Need users and polls to create reactions")
            return

        reaction_types = ['like', 'love', 'wow', 'sad', 'angry']

        print("Creating sample reactions...")
        reaction_count = 0
        for poll in polls:
            num_reactions = random.randint(3, len(users) // 2)
            reactors = random.sample(users, min(num_reactions, len(users)))

            for reactor in reactors:
                existing = Reaction.query.filter_by(poll_id=poll.id, user_id=reactor.id).first()
                if not existing:
                    reaction = Reaction(
                        poll_id=poll.id,
                        user_id=reactor.id,
                        reaction_type=random.choice(reaction_types),
                        timestamp=datetime.utcnow() - timedelta(days=random.randint(0, 7))
                    )
                    db.session.add(reaction)
                    reaction_count += 1

        db.session.commit()
        print(f"✓ Created {reaction_count} sample reactions!")


def initialize_database(with_sample_data=False):
    """Initialize database with optional sample data"""
    print("\n" + "=" * 50)
    print("DATABASE INITIALIZATION")
    print("=" * 50 + "\n")

    create_tables()
    create_admin_user()

    if with_sample_data:
        print("\nAdding sample data...")
        create_sample_users()
        create_sample_polls()
        create_sample_votes()
        create_sample_comments()
        create_sample_reactions()

    print("\n" + "=" * 50)
    print("✓ DATABASE INITIALIZATION COMPLETE!")
    print("=" * 50)
    print("\nYou can now run the application:")
    print("  python app.py")
    print("\nDefault Admin Credentials:")
    print("  Email: admin@polls.com")
    print("  Password: Admin@123")
    if with_sample_data:
        print("\nSample User Credentials:")
        print("  Email: john@example.com (or any other sample user)")
        print("  Password: Test@123")
    print("\n")


if __name__ == '__main__':
    import sys

    # Check if user wants sample data
    with_samples = False
    if len(sys.argv) > 1 and sys.argv[1] == '--with-samples':
        with_samples = True

    initialize_database(with_sample_data=with_samples)