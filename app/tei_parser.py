import xml.etree.ElementTree as ET
import re
from app.models import Lemma


def find_lemma_in_db(word):
    clean = word.strip('*').strip()
    if not clean:
        return None
    return Lemma.query.filter(Lemma.lemma.ilike(clean)).first()


def make_crossref_link(word):
    clean = word.strip('*').strip()
    lemma = find_lemma_in_db(clean)
    if lemma:
        return f'<a href="/lemma/{lemma.id}" class="crossref-link">{word}</a>'
    return word


def has_content(elem):
    if elem is None:
        return False
    text = ''.join(elem.itertext()).strip()
    return bool(text)


def tei_to_html(tei_string):
    try:
        root = ET.fromstring(tei_string)
    except ET.ParseError as e:
        return f'<p class="text-danger">Ошибка отображения: {e}</p>'

    def convert(elem):
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

        if tag == 'form' and elem.get('type') == 'reconstructed':
            return ''

        if tag in ('pb', 'pos'):
            return ''

        text = elem.text or ''
        children_html = ''

        for child in elem:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

            if child_tag == 'item' and not has_content(child):
                continue

            child_html = convert(child)
            children_html += child_html
            if child.tail:
                children_html += child.tail

        full_text = text + children_html

        if tag == 'etym':
            if not full_text.strip():
                return ''
            return f'<div class="etymology">{full_text}</div>'

        if tag == 'item':
            if not full_text.strip():
                return ''
            return f'<li class="mb-2">{full_text}</li>'

        if tag == 'form':
            return full_text

        if tag == 'ref':
            ref_type = elem.get('type')
            if ref_type == 'etymon':
                target = elem.get('target', '')
                if target:
                    lemma = find_lemma_in_db(target)
                    if lemma:
                        return f'<a href="/lemma/{lemma.id}" class="crossref-link">{full_text}</a>'
                return full_text
            else:
                lemma = find_lemma_in_db(full_text.strip())
                if lemma:
                    return f'<a href="/lemma/{lemma.id}" class="crossref-link">{full_text}</a>'
                return full_text

        mapping = {
            'entry':       ('<div class="entry">', '</div>'),
            'def':         ('<span class="def">', '</span>'),
            'bibl':        ('<span class="bibl">', '</span>'),
            'gram':        ('<em>', '</em>'),
            'gramgrp':     ('<div class="grammar mb-2">', '</div>'),
            'sense':       ('<div class="sense ms-3 mb-2">', '</div>'),
            'xr':          ('<span class="crossref-text">', '</span>'),
            'note':        ('<div class="note alert py-2">', '</div>'),
            'cit':         ('<span class="citation">', '</span>'),
            'quote':       ('<blockquote class="blockquote small">', '</blockquote>'),
            'm':           ('<code>', '</code>'),
        }

        if tag in mapping:
            open_tag, close_tag = mapping[tag]
            return f'{open_tag}{full_text}{close_tag}'

        return full_text

    body = convert(root)

    def replace_star_words(text):
        pattern = r'\*[^\s]+'
        def replacer(m):
            word = m.group(0)
            return make_crossref_link(word)
        return re.sub(pattern, replacer, text)

    body = replace_star_words(body)

    return f'<div class="tei-article">{body}</div>'
