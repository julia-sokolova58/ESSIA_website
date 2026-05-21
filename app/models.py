from app import db


class Volume(db.Model):
    __tablename__ = 'volumes'
    id = db.Column(db.Integer, primary_key=True)
    volume_number = db.Column(db.Integer, unique=True, nullable=False)
    pdf_filename = db.Column(db.String(255), nullable=False)
    lemmas = db.relationship('Lemma', backref='volume', lazy='dynamic',
                             order_by='Lemma.page')

    def __repr__(self):
        return f'<Volume {self.volume_number}>'


class Lemma(db.Model):
    __tablename__ = 'lemmas'
    id = db.Column(db.Integer, primary_key=True)
    lemma = db.Column(db.String(255), nullable=False, index=True)
    page = db.Column(db.Integer, nullable=False)
    volume_id = db.Column(db.Integer, db.ForeignKey('volumes.id'), nullable=False)
    article_tei = db.Column(db.Text, nullable=True)
    has_article = db.Column(db.Boolean, default=False)
    order_in_volume = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        db.Index('ix_lemma_volume_page', 'volume_id', 'page'),
        db.Index('ix_lemma_lemma', 'lemma'),
    )

    def __repr__(self):
        return f'<Lemma {self.lemma}>'
