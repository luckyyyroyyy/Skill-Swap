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
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    msg = Message(
        "🔐 Password Reset — SkillSwap Pro",
        sender=("SkillSwap Pro", current_app.config['MAIL_DEFAULT_SENDER']),
        recipients=[user.email]
    )
    msg.body = f'''Hi {user.username},

We received a request to reset your password. Click the link below:

{reset_url}

This link will expire in 30 minutes.

If you did not request this, please ignore this email.

— The SkillSwap Team
'''
    msg.html = f'''
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0f0f1a; border-radius: 16px; overflow: hidden; border: 1px solid #1e1e3a;">
      <!-- Header -->
      <div style="background: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7); padding: 40px 30px; text-align: center;">
        <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">🔄 SkillSwap Pro</h1>
        <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 14px;">Password Reset Request</p>
      </div>

      <!-- Body -->
      <div style="padding: 40px 30px;">
        <p style="color: #e2e8f0; font-size: 16px; margin: 0 0 20px; line-height: 1.6;">
          Hi <strong style="color: #a78bfa;">{user.username}</strong>,
        </p>
        <p style="color: #94a3b8; font-size: 15px; margin: 0 0 30px; line-height: 1.6;">
          We received a request to reset your password. Click the button below to create a new password. This link will expire in <strong style="color: #e2e8f0;">30 minutes</strong>.
        </p>

        <!-- CTA Button -->
        <div style="text-align: center; margin: 35px 0;">
          <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 10px; font-size: 16px; font-weight: 600; letter-spacing: 0.3px;">
            Reset My Password
          </a>
        </div>

        <p style="color: #64748b; font-size: 13px; margin: 30px 0 0; line-height: 1.6;">
          If the button doesn't work, copy and paste this link into your browser:
        </p>
        <p style="color: #818cf8; font-size: 13px; word-break: break-all; margin: 8px 0 0;">
          {reset_url}
        </p>

        <!-- Divider -->
        <hr style="border: none; border-top: 1px solid #1e1e3a; margin: 30px 0;">

        <p style="color: #475569; font-size: 13px; margin: 0; line-height: 1.5;">
          🔒 If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
        </p>
      </div>

      <!-- Footer -->
      <div style="background: #0a0a14; padding: 25px 30px; text-align: center; border-top: 1px solid #1e1e3a;">
        <p style="color: #475569; font-size: 12px; margin: 0;">
          © 2026 SkillSwap Pro — Swap skills, grow together.
        </p>
      </div>
    </div>
    '''
    try:
        mail.send(msg)
        logger.info(f"Password reset email sent to {user.email}")
    except Exception as e:
        logger.error(f"Error sending email to {user.email}: {e}")
        flash("We encountered an error sending the recovery email. Please try again later.", "warning")



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
