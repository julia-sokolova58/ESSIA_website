import sys
import os
import re
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Volume, Lemma

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DICTIONARY_PATH = os.path.join(BASE_DIR, 'dictionary')
EXCEL_FILE = 'index.xls'

app = create_app()


def get_volume_from_sheet(sheet_name):
    match = re.search(r'Том\s*(\d+)', sheet_name)
    if match:
        return int(match.group(1))
    return None


def import_excel_index(excel_path):
    import xlrd

    wb = xlrd.open_workbook(excel_path)

    for sheet_name in wb.sheet_names():
        vol_number = get_volume_from_sheet(sheet_name)
        if vol_number is None:
            print(f'Пропущен лист "{sheet_name}" — не удалось определить номер тома')
            continue

        ws = wb.sheet_by_name(sheet_name)

        volume = Volume.query.filter_by(volume_number=vol_number).first()
        if not volume:
            pdf_filename = f'vol_{vol_number:02d}.pdf'
            volume = Volume(volume_number=vol_number, pdf_filename=pdf_filename)
            db.session.add(volume)
            db.session.flush()

        count = 0
        for row_idx in range(2, ws.nrows):
            root_word = ws.cell_value(row_idx, 0)
            page = ws.cell_value(row_idx, 1)

            if root_word and page:
                try:
                    page_int = int(float(page))
                except (ValueError, TypeError):
                    continue

                lemma = Lemma(
                    lemma=str(root_word).strip(),
                    page=page_int,
                    volume_id=volume.id,
                    has_article=False
                )
                db.session.add(lemma)
                count += 1

        print(f'Том {vol_number}: {count} лемм из Excel')

    db.session.commit()
    print('Эталонные леммы импортированы.\n')


def import_xml_articles():
    for vol_name in sorted(os.listdir(DICTIONARY_PATH), key=lambda x: int(x) if x.isdigit() else 0):
        if not vol_name.isdigit():
            continue

        vol_number = int(vol_name)
        vol_path = os.path.join(DICTIONARY_PATH, vol_name)

        volume = Volume.query.filter_by(volume_number=vol_number).first()
        if not volume:
            print(f'Том {vol_number}: не найден в БД')
            continue

        xml_files = [f for f in os.listdir(vol_path) if f.endswith('.xml')]
        updated = 0
        errors = 0

        for xml_file in xml_files:
            xml_path = os.path.join(vol_path, xml_file)

            try:
                with open(xml_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                content = re.sub(r'(xml:id="[^"]*")\s+xml:id="[^"]*"', r'\1', content)

                root_elem = ET.fromstring(content)

                orth_text = None
                for form in root_elem.iter():
                    tag = form.tag.split('}')[-1] if '}' in form.tag else form.tag
                    if tag == 'form' and form.get('type') == 'reconstructed':
                        for orth in form.iter():
                            orth_tag = orth.tag.split('}')[-1] if '}' in orth.tag else orth.tag
                            if orth_tag == 'orth' and orth.text:
                                orth_text = orth.text.strip()
                                break
                        break

                pb = None
                for elem in root_elem.iter():
                    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                    if tag == 'pb':
                        pb = elem
                        break

                page_start = int(pb.get('n')) if pb is not None and pb.get('n') else None

                if page_start is None:
                    continue

                lemma_records = Lemma.query.filter_by(
                    page=page_start,
                    volume_id=volume.id
                ).all()

                if len(lemma_records) == 1:
                    lemma_record = lemma_records[0]
                elif len(lemma_records) > 1:
                    lemma_record = None
                    for lr in lemma_records:
                        if not lr.has_article:
                            lemma_record = lr
                            break
                    if lemma_record is None:
                        lemma_record = lemma_records[0]
                else:
                    continue

                if orth_text:
                    lemma_record.lemma = orth_text
                lemma_record.article_tei = ET.tostring(root_elem, encoding='unicode')
                lemma_record.has_article = True
                updated += 1

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f'  Ошибка: {xml_file} — {e}')

        print(f'Том {vol_number}: обновлено {updated} статей, ошибок {errors}')

    db.session.commit()
    print('\nTEI-тексты добавлены.')


def import_dictionary():
    with app.app_context():
        db.create_all()
        print('База данных создана.\n')

        excel_path = os.path.join(DICTIONARY_PATH, EXCEL_FILE)
        if not os.path.exists(excel_path):
            print(f'ОШИБКА: Excel-файл не найден: {excel_path}')
            sys.exit(1)

        print('=== Этап 1: Импорт из Excel ===')
        import_excel_index(excel_path)

        print('=== Этап 2: Добавление TEI-текстов ===')
        import_xml_articles()

        print('\n=== Импорт завершён! ===')


if __name__ == '__main__':
    import_dictionary()
