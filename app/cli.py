import click
from app.extensions import db


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("create-admin")
    @click.option("--name", prompt="Full name", default="Super Admin")
    @click.option("--email", prompt="Email")
    @click.option("--password", prompt="Password", hide_input=True, confirmation_prompt=True)
    def create_admin(name, email, password):
        """Create the initial super admin account."""
        from app.models import User

        existing = User.query.filter_by(email=email.lower()).first()
        if existing:
            click.echo(f"User with email {email} already exists.")
            return
        user = User(full_name=name, email=email.lower(), role="admin",
                    status="active", is_super_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Admin account created: {email}")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Seed default settings and an example admin (for first-run convenience)."""
        from app.models import User, SiteSetting

        if not User.query.filter_by(role="admin").first():
            admin = User(full_name="System Administrator", email="admin@citylightsindhisamaj.org",
                         role="admin", status="active", is_super_admin=True, must_change_password=True)
            admin.set_password("Admin@12345")
            db.session.add(admin)
            click.echo("Default admin created: admin@citylightsindhisamaj.org / Admin@12345 "
                        "(CHANGE THIS PASSWORD IMMEDIATELY)")

        defaults = {
            "org_name": "CITYLIGHT SINDHI SAMAJ SURAT",
            "registration_open": "true",
            "auto_approve": "false",
        }
        for k, v in defaults.items():
            if not SiteSetting.query.filter_by(key=k).first():
                db.session.add(SiteSetting(key=k, value=v))

        db.session.commit()
        click.echo("Demo/default settings seeded.")
