from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    SelectField,
    IntegerField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    Email,
    EqualTo,
    ValidationError,
    NumberRange,
    Optional,
    Regexp,
)
from models import User


class RegistrationForm(FlaskForm):
    """User registration form with validation."""

    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=100),
            Regexp(
                r"^[a-zA-Z0-9_]+$",
                message="Username can only contain letters, numbers, and underscores.",  # noqa: E501
            ),
        ],
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(
                min=8, message="Password must be at least 8 characters long."
            ),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )

    def validate_username(self, username):
        """Check if username already exists."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                "Username already taken. Please choose a different one."
            )

    def validate_email(self, email):
        """Check if email already exists."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                "Email already registered. Please use a different one."
            )


class LoginForm(FlaskForm):
    """User login form."""

    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])


class SkillForm(FlaskForm):
    """Add skill form."""

    name = StringField(
        "Skill Name",
        validators=[
            DataRequired(),
            Length(min=2, max=100),
            Regexp(
                r"^[a-zA-Z\s]+$",
                message="Skill name can only contain letters and spaces.",
            ),
        ],
    )
    category = SelectField(
        "Category",
        choices=[
            ("Programming", "Programming"),
            ("Design", "Design"),
            ("Business", "Business"),
            ("Languages", "Languages"),
            ("Music", "Music"),
            ("Fitness", "Fitness"),
            ("Lifestyle", "Lifestyle"),
            ("Other", "Other"),
        ],
        validators=[DataRequired()],
    )
    type = SelectField(
        "Type",
        choices=[
            ("offer", "I can teach this"),
            ("want", "I want to learn this"),
        ],
        validators=[DataRequired()],
    )


class ReviewForm(FlaskForm):
    """Submit review form."""

    rating = IntegerField(
        "Rating (1-5)",
        validators=[
            DataRequired(),
            NumberRange(
                min=1, max=5, message="Rating must be between 1 and 5."
            ),
        ],
    )
    comment = TextAreaField(
        "Comment",
        validators=[
            Optional(),
            Length(max=500, message="Comment cannot exceed 500 characters."),
        ],
    )


class EditProfileForm(FlaskForm):
    """Edit user profile form."""

    bio = TextAreaField(
        "Bio",
        validators=[
            Optional(),
            Length(max=500, message="Bio cannot exceed 500 characters."),
        ],
    )
    profile_pic = FileField(
        "Profile Picture",
        validators=[
            FileAllowed(["jpg", "png", "jpeg", "gif"], "Images only!")
        ],
    )


class ChatMessageForm(FlaskForm):
    """Chat message form."""

    content = TextAreaField(
        "Message",
        validators=[
            DataRequired(),
            Length(
                min=1,
                max=1000,
                message="Message must be between 1 and 1000 characters.",
            ),
        ],
    )
