import os

class Config:
    # 개발 환경 (SQLite)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(os.getcwd(), 'instance', 'bank.db'))
    
    # 배포 환경에서도 SQLite 사용 (임시)
    # if os.environ.get('DATABASE_URL'):
    #     SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    #     if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
    #         SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your-secret-key'