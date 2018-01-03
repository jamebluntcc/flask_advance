from ext import db

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(45))
    email = db.Column(db.String(45))

    def __init__(self, name, email):
        self.name = name
        self.email = email

    def __repr__(self):
        return '<user:{0}>'.format(self.name)


