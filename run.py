from app import create_app, db, User

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email="user@example.com").first():
            u = User(email="user@example.com")
            u.set_password("old_password")
            db.session.add(u)
            db.session.commit()
    app.run(debug=True)
