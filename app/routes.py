from flask import Blueprint, render_template, request
from app.models import Volume, Lemma


main = Blueprint('main', __name__)


@main.route('/')
def index():
    volumes = Volume.query.order_by(Volume.volume_number).all()
    return render_template('index.html', volumes=volumes)


@main.route('/volume/<int:volume_id>')
def volume_view(volume_id):
    volume = Volume.query.get_or_404(volume_id)
    lemmas = volume.lemmas.order_by(Lemma.page, Lemma.id).all()
    return render_template('volume.html', volume=volume, lemmas=lemmas)


@main.route('/lemma/<int:lemma_id>')
def lemma_view(lemma_id):
    lemma = Lemma.query.get_or_404(lemma_id)
    volume = lemma.volume

    prev_lemma = Lemma.query.filter(
        Lemma.volume_id == volume.id,
        Lemma.id < lemma.id
    ).order_by(Lemma.id.desc()).first()

    next_lemma = Lemma.query.filter(
        Lemma.volume_id == volume.id,
        Lemma.id > lemma.id
    ).order_by(Lemma.id.asc()).first()

    article_html = None
    if lemma.has_article and lemma.article_tei:
        from app.tei_parser import tei_to_html
        article_html = tei_to_html(lemma.article_tei)

    return render_template('lemma.html', 
                           lemma=lemma, 
                           volume=volume,
                           article_html=article_html,
                           prev_lemma=prev_lemma,
                           next_lemma=next_lemma)


@main.route('/search')
def search():
    q = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'lemma')

    if not q:
        return render_template('search_results.html', query='', results=[], search_type=search_type)

    if search_type == 'lemma':
        results = Lemma.query.filter(
            Lemma.lemma.ilike(f'%{q}%')
        ).order_by(Lemma.lemma).all()
    else:
        results = Lemma.query.filter(
            Lemma.article_tei.ilike(f'%{q}%')
        ).order_by(Lemma.lemma).all()

    return render_template('search_results.html', query=q, results=results, search_type=search_type)
