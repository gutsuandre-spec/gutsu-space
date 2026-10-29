"""Explicit price-free selection from the existing private Radar catalogue.

No stock, prices, source filenames, tax terms or supplier metadata cross this boundary.
The selection is reviewed data, never a nightly automatic publication.
"""
import argparse
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANDS = [
    ('aputure','Aputure','Профессиональное освещение','lighting',
     'Свет для павильона и выездной съёмки',
     'Подбираем постоянный свет и светоформирующие насадки под съёмочную задачу. В запросе укажите размер площадки, способ питания и требуемые крепления: так можно проверить совместимость всего комплекта до закупки.',
     ['Осветители','Софтбоксы','Линзы Френеля']),
    ('deity','Deity','Микрофоны и звук','audio',
     'Запись речи на площадке и в кадре',
     'Для интервью, репортажа и многокамерной съёмки важны не только микрофоны, но и полный звуковой тракт. Укажите число спикеров, камеру или рекордер, разъёмы и условия работы — сверим комплект приёмников, передатчиков и аксессуаров.',
     ['Микрофоны','Радиосистемы','Таймкод']),
    ('accsoon','Accsoon','Видеомониторинг и беспроводная передача','monitoring',
     'Изображение там, где работает команда',
     'Видеопередача и мониторинг помогают организовать работу оператора, режиссёра и клиента. Для подбора Accsoon нужны интерфейсы камер и мониторов, число приёмных точек и требования к сигналу. Питание и крепления проверяем отдельными позициями.',
     ['Видеосендеры','Мониторы','Адаптеры']),
    ('smallrig','SmallRig','Риги, крепления, аксессуары','rigging',
     'Собрать камеру под рабочий процесс',
     'Клетка, рукоятки, опоры и питание должны подходить к конкретной конфигурации камеры. В запросе на SmallRig укажите точный артикул, модель камеры и уже используемые крепления. Похожие обозначения и разные комплекты не считаем взаимозаменяемыми.',
     ['Клетки и риги','Штативы и моноподы','Рукоятки']),
    ('kf-concept','K&F Concept','Фильтры, штативы, аксессуары','optics',
     'Фильтры и опоры с проверкой совместимости',
     'У фильтра важны диаметр, тип крепления и рабочий диапазон, у штатива — камера, нагрузка и способ съёмки. Поможем составить запрос по этим параметрам и проверить точную серию K&F Concept перед согласованием поставки.',
     ['Фильтры','Штативы','Переходные кольца']),
    ('synco','Synco','Микрофоны и радиосистемы','audio',
     'Комплект звука для интервью и трансляций',
     'Подбор Synco начинается с количества участников и устройства записи. Уточните, нужен ли один передатчик или комплект на двух спикеров, какие разъёмы используются и какие кабели входят в набор. Условия поставки рассчитываем по выбранной комплектации.',
     ['Радиосистемы','Накамерные микрофоны','Аксессуары']),
    ('ulanzi','Ulanzi','Свет, штативы, аксессуары','rigging',
     'Мобильная съёмочная конфигурация',
     'Свет, компактные опоры и крепления Ulanzi можно подобрать для небольшой студии, выездной команды или мобильной съёмки. Пришлите модели устройств и список рабочих сценариев: проверим посадочные места, питание и состав комплекта.',
     ['Штативы','Компактный свет','Крепления']),
    ('7artisans','7Artisans','Фото- и кинообъективы','optics',
     'Оптика под камеру и характер съёмки',
     'Для выбора объектива 7Artisans укажите байонет, формат сенсора и необходимые фокусные расстояния. Фото- и киноверсии, автофокусные и ручные модели сверяем отдельно. Адаптеры и фильтры включаем в запрос только с проверкой совместимости.',
     ['Фотообъективы','Кинообъективы','Адаптеры']),
    ('exascend','Exascend','Карты памяти и накопители','media',
     'Носители для выбранного формата записи',
     'Совместимость накопителя определяется камерой, кодеком и режимом записи. Для подбора Exascend укажите объём, форм-фактор и требуемую устойчивую скорость. Заявленная пиковая скорость не заменяет проверку требований конкретного устройства.',
     ['Карты памяти','SSD','Картридеры']),
    ('kingma','Kingma','Аккумуляторы и зарядные устройства','power',
     'Питание съёмочного комплекта',
     'При подборе аккумуляторов и зарядных устройств Kingma проверяем точную модель камеры, тип батареи, разъёмы и состав набора. Укажите число рабочих часов и устройств. Ёмкость, совместимость и условия поставки согласуем до предложения.',
     ['Аккумуляторы','Зарядные устройства','Сетевые адаптеры'])]

CATEGORIES = {
 'lighting': ('Свет для съёмки','Постоянный свет, насадки и опоры. В запросе укажите площадку, питание и характер света.'),
 'audio': ('Микрофоны и звук','Комплекты для записи речи, интервью и трансляций. Проверяем число каналов, разъёмы и аксессуары.'),
 'monitoring': ('Видеомониторинг и передача','Мониторинг и беспроводной видеосигнал. Для подбора нужны интерфейсы, формат и число приёмников.'),
 'rigging': ('Риги, штативы и крепления','Опоры и обвес под конкретную камеру. Проверяем нагрузку, посадочные места и совместимость комплекта.'),
 'optics': ('Оптика и фильтры','Объективы и фильтры по байонету, формату сенсора и диаметру. Разные версии сверяем отдельно.'),
 'media': ('Карты памяти и накопители','Носители под камеру и режим записи. Форм-фактор, объём и устойчивая скорость требуют проверки.'),
 'power': ('Аккумуляторы и питание','Аккумуляторы, зарядные устройства и адаптеры с проверкой разъёмов и совместимости.')}

PUBLIC_KEYS = {'id','brand','name','category','catalog_date'}

def category_for(item):
    name=item['name'].casefold()
    for pattern,category in [
        (r'светофильтр|объектив|lens focus|адаптер объектива','optics'),
        (r'осветитель|софтбокс|френел|lantern|nova p','lighting'),
        (r'микрофон|радиосистема|гарнитура|boom pole','audio'),
        (r'видеосендер|монитор|видеопередат','monitoring'),
        (r'карта памяти|ssd|картридер','media'),
        (r'аккумулятор|зарядное|сетевой адаптер','power'),
        (r'штатив|монопод|крепление|клетка|рукоят','rigging')]:
        if re.search(pattern,name): return category
    return next(b[3] for b in BRANDS if b[0]==item['brand'])


def validate(products):
    seen=set(); allowed={b[0] for b in BRANDS}
    for p in products:
        if set(p)!=PUBLIC_KEYS or p['brand'] not in allowed:
            raise ValueError('public_catalogue_schema_rejected')
        if not re.fullmatch(r'GS-[A-Za-z0-9_-]{1,64}',p['id']) or p['id'] in seen:
            raise ValueError('duplicate_or_invalid_public_id')
        if re.search(r'godox|уцен|б/у',p['name'],re.I): raise ValueError('excluded_public_item')
        if not all(isinstance(v,str) and v.strip() for v in p.values()): raise ValueError('invalid_public_value')
        seen.add(p['id'])
    return products

def export(db, count=8):
    report=json.loads(db.execute('SELECT report FROM catalog_imports ORDER BY catalog_date DESC,imported_at DESC LIMIT 1').fetchone()[0])
    rows=[json.loads(r[0]) for r in db.execute('SELECT record FROM catalog_items WHERE import_sha256=?',(report['sha256'],))]
    selected=[]
    for slug,name,*_ in BRANDS:
        variants={'kf-concept':r'K\s*&\s*F(?:\s+Concept)?'}.get(slug,re.escape(name))
        candidates=[]
        for r in rows:
            text=' '.join(r['name'].split()); m=re.search(variants,text,re.I)
            if not m or re.search(r'godox|уцен|б/у',text,re.I): continue
            prefix=text[:m.start()]
            if re.search(r'\b(?:для|for|совместим\w*|DigitalFoto)\b',prefix,re.I): continue
            # Curate primary equipment before cables/cases, across categories.
            rank=0 if re.match(r'(?:Осветитель|Радиосистема|Микрофон|Видеосендер|Монитор|Штатив|Монопод|Объектив|Светофильтр|Карта памяти|SSD|Аккумулятор|Зарядное)',text,re.I) else 1
            candidates.append((rank,len(text),str(r['sku']),r))
        chosen=[]; categories={}
        for _,_,_,r in sorted(candidates):
            category=r['category'] or 'Оборудование'
            if categories.get(category,0)>=3: continue
            chosen.append(r); categories[category]=categories.get(category,0)+1
            if len(chosen)==count: break
        for r in chosen:
            selected.append({'id':'GS-'+r['sku'],'brand':slug,'name':' '.join(r['name'].split()),
                'category':str(r['category'] or 'Оборудование'),'catalog_date':report['catalog_date']})
    return validate(selected)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--database',type=Path,required=True); p.add_argument('--out',type=Path,default=ROOT/'data/equipment-public.json'); args=p.parse_args()
    db=sqlite3.connect(args.database.resolve().as_uri()+'?mode=ro',uri=True)
    products=export(db); args.out.write_text(json.dumps(products,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'public_products':len(products),'brands':len({x['brand'] for x in products}),'price_fields':0,'stock_fields':0}))
