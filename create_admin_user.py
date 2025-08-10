
from app import app, db, UserAccount

def create_admin():
    username = "pobakara"
    email = "pobakara@gmail.com"
    password = "poba123"

    if UserAccount.query.filter_by(username=username).first():
        print("User already exists.")
        return

    user = UserAccount(username=username, email=email, role='admin')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    print(f"Admin user '{username}' created.")

if __name__ == "__main__":
    with app.app_context():
        create_admin()
