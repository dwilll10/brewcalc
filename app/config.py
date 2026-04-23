import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, '..', 'data', 'brewcalc.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FERMCTL_API_URL = os.environ.get("FERMCTL_API_URL", "http://raspberrypi.local:5001")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
