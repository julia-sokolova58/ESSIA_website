import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'etymology-dict-secret-key-2025')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(basedir, "etymology.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
