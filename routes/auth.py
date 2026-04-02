from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from extensions import db, login_manager, limiter, mail
from models import User
from forms import RegistrationForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm
from flask_mail import Message

auth_bp = Blueprint("auth", __name__)
logger = logging.getLogger(__name__)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data),
            )
            db.session.add(user)
            db.session.commit()

            logger.info(f"New user registered: {user.username}")
            flash("Account created successfully! Please log in.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {e}")
            flash(
                "An error occurred during registration. Please try again.",
                "danger",
            )

    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()

            if user and check_password_hash(user.password, form.password.data):
                if not user.is_active:
                    flash("This account has been deactivated.", "danger")
                    return render_template("login.html", form=form)

                login_user(user)
                logger.info(f"User logged in: {user.username}")
                return redirect(url_for("user.dashboard"))

            logger.warning(
                f"Failed login attempt for email: {form.email.data}"
            )
            flash("Invalid email or password.", "danger")
        except Exception as e:
            logger.error(f"Login error: {e}")
            flash(
                "An error occurred during login. Please try again.", "danger"
            )

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.landing"))


def send_password_reset_email(user):
    token = user.get_reset_token()
    msg = Message(
        "Password Reset Request",
        recipients=[user.email]
    )
    msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_password', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    try:
        mail.send(msg)
        logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        logger.error(f"Error sending email to {user.email}: {e}")
        # flash("We encountered an error sending the recovery email. In a real app this would go out.", "warning")


@auth_bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        # Always tell user to check email whether exists or not (security)
        flash("Check your email for the instructions to reset your password", "info")
        return redirect(url_for("auth.login"))
    return render_template("reset_password_request.html", form=form)


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("user.dashboard"))
    user = User.verify_reset_token(token)
    if not user:
        flash("That is an invalid or expired token.", "danger")
        return redirect(url_for("auth.reset_password_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = generate_password_hash(form.password.data)
        db.session.commit()
        flash("Your password has been updated! You are now able to log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("reset_password.html", form=form)
