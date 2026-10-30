"""Build the existing website through a strict public-file boundary."""
import argparse
from html import escape as h
import json
from pathlib import Path
import shutil
from urllib.parse import urlencode, urlsplit, quote
import xml.etree.ElementTree as ET
from catalog_public import BRANDS,CATEGORIES,validate,ROOT,category_for

ORIGIN='https://gutsu.space'

def page(path,title,description,body,*,robots=None,api_origin=None):
    canonical=ORIGIN+path
    brand=next((b[0] for b in BRANDS if path=='/equipment/brands/'+b[0]+'/'),None)
    request_url='/equipment/request/'+('?'+urlencode({'brand':brand}) if brand else '')
    crumbs=[{'@type':'ListItem','position':1,'name':'GUTSU','item':ORIGIN+'/'},
            {'@type':'ListItem','position':2,'name':'Equipment','item':ORIGIN+'/equipment/'},
            {'@type':'ListItem','position':3,'name':title,'item':canonical}]
    schema={'@context':'https://schema.org','@type':'CollectionPage','name':title,'url':canonical,
            'inLanguage':'ru-RU','breadcrumb':{'@type':'BreadcrumbList','itemListElement':crumbs}}
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{h(title)} — GUTSU / Equipment</title><meta name="description" content="{h(description,quote=True)}">
<link rel="canonical" href="{canonical}"><meta property="og:type" content="website"><meta property="og:site_name" content="GUTSU.SPACE">
<meta property="og:title" content="{h(title,quote=True)}"><meta property="og:description" content="{h(description,quote=True)}"><meta property="og:url" content="{canonical}">
<meta property="og:image" content="{ORIGIN}/assets/og-gutsu.svg"><meta name="theme-color" content="#0B0D10">
{f'<meta name="robots" content="{robots}">' if robots else ''}
{f'<meta name="gutsu-api-origin" content="{h(api_origin,quote=True)}">' if api_origin else ''}
<link rel="icon" href="/assets/gutsu-symbol.svg" type="image/svg+xml"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/equipment/catalog.css">
<script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace('<','&lt;')}</script></head>
<body class="is-ready"><a class="skip-link" href="#main-content">Перейти к содержанию</a>
<div class="wrap"><header><nav class="nav"><a class="asset-lockup asset-lockup--sub" href="/" aria-label="GUTSU SPACE"><img class="brand-lockup-image" src="/assets/gutsu-lockup-horizontal.svg" alt="GUTSU SPACE" width="220" height="55"></a>
<div class="nav-contact"><a class="mail" href="/equipment/">Equipment</a><a class="mail" href="/equipment/brands/">Бренды</a><a class="mail" href="{request_url}">Запросить КП</a></div></nav></header>
<main id="main-content" tabindex="-1">{body}</main>
<footer class="footer"><div class="footer-brand"><img class="brand-wordmark-image" src="/assets/gutsu-wordmark.svg" alt="GUTSU SPACE" width="180" height="45"><span>/ EQUIPMENT</span></div><div><a href="/equipment/brands/">Каталог брендов</a> · <a href="{request_url}">Запросить КП</a><br><a href="https://t.me/gutsuspace" rel="noopener" target="_blank">Telegram</a> · <a href="/privacy/">Персональные данные</a></div></footer></div>
<script src="/equipment/catalog.js" defer></script></body></html>'''

def hero(kicker,title,lead):
    return f'<section class="catalog-hero"><p class="eyebrow">{h(kicker)}</p><h1>{title}</h1><p class="lead">{lead}</p></section>'

def quote_text(brand=''):
    return ('Здравствуйте! Прошу подготовить коммерческое предложение.\n\n'
            +(f'Бренд: {brand}\n' if brand else '')
            +'Модель / список оборудования:\nКоличество:\nГород поставки:\nЖелаемый срок:\nТребования к комплекту:')

def static_request(brand='',products=None):
    text=quote_text(brand)
    mail='mailto:gutsuandre@gmail.com?'+urlencode({'subject':'Запрос КП GUTSU'+(' — '+brand if brand else ''),'body':text},quote_via=quote)
    catalogue=''
    if products is not None:
        names={b[0]:b[1] for b in BRANDS}
        data={'brands':names,'products':[{'code':p['id'],'model':p['name'],'brand':p['brand']} for p in products]}
        catalogue='<script type="application/json" id="request-catalog">'+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+'</script>'
    return ('<section class="request-section" id="request"><div><p class="eyebrow">ПОД ЗАКАЗ / B2B</p>'
            '<h2>Запросить КП по email</h2><p>Проверим выбранные модели, комплектность и условия поставки. Добавьте в письмо количество, город и желаемый срок.</p></div>'
            f'<div class="lead-form quote-contact" data-quote-contact data-brand="{h(brand,quote=True)}">'
            '<p data-quote-selection>Можно прислать готовый список или описать задачу для подбора.</p>'
            '<p>Почта GUTSU: <a class="quote-address" href="mailto:gutsuandre@gmail.com">gutsuandre@gmail.com</a></p>'
            f'<div class="catalog-actions"><a class="btn" data-quote-email href="{h(mail,quote=True)}">Открыть письмо ↗</a>'
            '<button class="micro-link quote-copy" type="button" data-quote-copy hidden>Скопировать текст</button></div>'
            '<p class="form-alternative">Откроется ваша почтовая программа. Если она не настроена, скопируйте текст ниже и отправьте его из своей почты.</p>'
            f'<pre class="quote-message" data-quote-message tabindex="0" aria-label="Текст запроса КП">{h(text)}</pre>'
            '<p class="quote-status" data-quote-status role="status" aria-live="polite"></p>'
            '<p class="form-alternative">Письмо отправляете вы. Эта страница не отправляет запрос и не принимает контактные данные или вложения. Цена, наличие и срок поставки требуют подтверждения.</p>'
            '<noscript><p>Для автоматической подстановки выбранной модели нужен JavaScript. Можно скопировать её название из каталога и написать на указанный email.</p></noscript>'
            '</div>'+catalogue+'</section>')

def form(model='',static_catalog=False):
    if static_catalog: return static_request(model)
    return f'''<section class="request-section" id="request"><div><p class="eyebrow">ПОД ЗАКАЗ / B2B</p><h2>Запросить коммерческое предложение</h2><p>Проверим выбранные модели, количество и условия поставки. Цена и наличие — по запросу.</p><p>Сначала согласуем комплект, договор и условия предоплаты, затем закупку и поставку.</p></div>
<form class="lead-form" data-lead-form novalidate><p class="form-status" role="status" aria-live="polite">Проверяем доступность формы…</p>
<fieldset disabled><legend>Данные для ответа на запрос</legend>
<label>Тип запроса<select name="kind"><option value="quote">Запросить КП</option><option value="selection">Подбор оборудования</option></select></label>
<div class="form-pair"><label>Компания<input name="company" required maxlength="200" autocomplete="organization"></label><label>Контактное лицо<input name="contact" required maxlength="120" autocomplete="name"></label></div>
<div class="form-pair"><label>Email<input name="email" type="email" required maxlength="254" autocomplete="email"></label><label>Телефон — необязательно<input name="phone" type="tel" maxlength="40" autocomplete="tel"></label></div>
<label>Бренд, модель или артикул<input name="models" value="{h(model,quote=True)}" maxlength="1000" placeholder="Укажите точную модель или опишите задачу ниже"></label>
<label>Количество<input name="quantity" type="number" min="1" max="100000" step="1" placeholder="Если известно"></label>
<label>Задача или комментарий<textarea name="comment" maxlength="5000" rows="4" placeholder="Для подбора: задача, камера, состав комплекта и желаемый срок"></textarea></label>
<label>Список оборудования — необязательно<input name="attachment" type="file" accept=".pdf,.xlsx,.csv,.txt"><small>Один PDF, XLSX, CSV или TXT до 2 МБ. Без исполняемых файлов и макросов.</small></label>
<label class="form-trap" aria-hidden="true">Сайт<input name="website" tabindex="-1" autocomplete="off"></label>
<label class="consent"><input name="consent" type="checkbox" required><span>Даю <a href="/consent/" target="_blank" rel="noopener">согласие на обработку персональных данных</a> для ответа на запрос и ознакомлен с <a href="/privacy/" target="_blank" rel="noopener">политикой</a>. Это не согласие на рекламную рассылку.</span></label>
<button class="btn" type="submit">Отправить запрос <span aria-hidden="true">↗</span></button></fieldset>
<p class="form-alternative">Можно обсудить задачу в <a href="https://t.me/gutsuspace" target="_blank" rel="noopener">Telegram</a>.</p></form></section>'''

def products_table(items):
    lines=[]
    for p in items:
        query=urlencode({'brand':p['brand'],'model':p['name'],'code':p['id']})
        lines.append(f'<tr><td><strong>{h(p["name"])}</strong><small>Код позиции {h(p["id"])} · {h(p["category"])}</small></td><td>Цена и наличие — по запросу</td><td><a href="/equipment/request/?{query}">Запросить КП <span aria-hidden="true">↗</span></a></td></tr>')
    return '<div class="table-scroll"><table class="product-table"><caption>Модели для подбора. Код позиции не является артикулом производителя.</caption><thead><tr><th>Оборудование</th><th>Условия</th><th>Запрос</th></tr></thead><tbody>'+''.join(lines)+'</tbody></table></div>'

def generate(root=ROOT,static_catalog=False):
    products=validate(json.loads((root/'data/equipment-public.json').read_text()))
    config=json.loads((root/'data/site.json').read_text()); paths=[]
    api=None if static_catalog else config.get('api_origin')
    if api:
        parsed=urlsplit(api)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ('','/') or parsed.query or parsed.fragment: raise ValueError('https_api_origin_required')
        api=api.rstrip('/')
    def write(path,title,description,body,robots=None):
        dest=root/(path.strip('/')+'/index.html'); dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(page(path,title,description,body,robots=robots,api_origin=api)); paths.append(path)
    tiles=''.join(f'<a class="brand-tile" href="/equipment/brands/{b[0]}/"><span class="brand-name">{h(b[1])}</span><span>{h(b[2])}</span><span class="tile-arrow" aria-hidden="true">↗</span></a>' for b in BRANDS)
    body=hero('EQUIPMENT / БРЕНДЫ','Техника под задачу.<br><em>Поставка под заказ.</em>','Профессиональное оборудование для студий, продакшнов и команд трансляций. Выберите бренд или пришлите готовый список — проверим модели, комплектность и условия поставки.')
    body+='<div class="catalog-actions"><a class="btn" href="/equipment/request/">Запросить КП ↗</a><a class="micro-link" href="/equipment/categories/">По категориям →</a></div><section class="section"><h2>Бренды оборудования</h2><div class="brand-grid">'+tiles+'</div></section>'
    body+='<section class="supply-note"><h2>До закупки — проверка условий</h2><p>Каталог помогает выбрать модели. Наличие, актуальную цену и срок проверяем у поставщика перед предложением. Аналоги согласуем отдельно.</p><a href="/equipment/procurement/">Как подготовить закупочный запрос →</a></section>'
    write('/equipment/brands/','Бренды профессионального оборудования','Подбор и поставка Aputure, Deity, Accsoon, SmallRig, K&F Concept, Synco, Ulanzi, 7Artisans, Exascend и Kingma для бизнеса.',body)
    for slug,name,category,category_slug,headline,description,cats in BRANDS:
        items=[p for p in products if p['brand']==slug]
        body=f'<nav class="breadcrumbs" aria-label="Хлебные крошки"><a href="/equipment/">Equipment</a> / <a href="/equipment/brands/">Бренды</a> / {h(name)}</nav>'
        body+=hero(f'{name} / {category}',f'{h(name)}.<br><em>{h(headline)}.</em>',h(description))
        body+='<div class="category-chips">'+''.join(f'<span>{h(x)}</span>' for x in cats)+''.join(f'<a href="/equipment/categories/{c}/">{h(CATEGORIES[c][0])} →</a>' for c in sorted({category_for(p) for p in items}))+'</div>'
        body+=f'<section class="section"><h2>Модели {h(name)} для вашего запроса</h2><p>Ассортимент сверён по каталогу от {h(items[0]["catalog_date"])}. Это не подтверждение текущих остатков. Конкретную версию и комплект проверим перед КП.</p>'+products_table(items)+'</section>'+form(name,static_catalog)
        write('/equipment/brands/'+slug+'/',name+' — подбор и поставка для бизнеса',description,body)
    catlinks=''.join(f'<a class="category-tile" href="/equipment/categories/{slug}/"><h2>{h(c[0])}</h2><p>{h(c[1])}</p><span aria-hidden="true">↗</span></a>' for slug,c in CATEGORIES.items())
    write('/equipment/categories/','Категории оборудования для бизнеса','Свет, звук, видеомониторинг, оптика, риги, носители и питание для профессиональной съёмки.',hero('EQUIPMENT / КАТЕГОРИИ','Собрать рабочий комплект.','Выберите направление или опишите задачу для подбора.')+'<div class="category-grid">'+catlinks+'</div>')
    for slug,(title,desc) in CATEGORIES.items():
        items=[p for p in products if category_for(p)==slug]; ids={p['brand'] for p in items}; brands=[b for b in BRANDS if b[0] in ids]
        body=hero('EQUIPMENT / КАТЕГОРИИ',h(title),h(desc))+'<div class="category-chips">'+''.join(f'<a href="/equipment/brands/{b[0]}/">{h(b[1])}</a>' for b in brands)+'</div>'+products_table(items)+form(static_catalog=static_catalog)
        write('/equipment/categories/'+slug+'/',title+' под заказ',desc,body)
    write('/equipment/request/','Запросить КП или подбор оборудования','Пришлите модели, количество или задачу. Подбор и поставка профессионального оборудования под заказ для бизнеса.',hero('EQUIPMENT / ЗАПРОС','От задачи — к комплекту.','Укажите оборудование или опишите задачу. Цену, комплектность и условия поставки согласуем до закупки.')+(static_request(products=products) if static_catalog else form()))
    if static_catalog:
        note=('<article class="policy-copy"><p>Форма приёма заявок на этом сайте не активирована. '
              'Сайт не принимает контактные данные и вложения через форму.</p>'
              '<p>Документы для будущей формы находятся на проверке и будут размещены перед её запуском.</p>'
              '<p><a href="/equipment/brands/">Вернуться к каталогу оборудования →</a></p></article>')
        write('/privacy/','Информация о форме приёма заявок','Форма GUTSU.SPACE пока не принимает персональные данные.',
              hero('GUTSU / ИНФОРМАЦИЯ','Форма пока недоступна.','Документы для её запуска находятся на проверке.')+note,robots='noindex,follow')
        write('/consent/','Согласие через сайт не запрашивается','Форма отключена; согласие на обработку данных через неё не запрашивается.',
              hero('GUTSU / ИНФОРМАЦИЯ','Согласие не запрашивается.','Форма приёма заявок пока отключена.')+note,robots='noindex,follow')
    else:
        draft='<p class="policy-draft">Проект документа для проверки владельцем. Публичный сбор данных пока отключён.</p>'
        operator=h(config['operator_name']); email=h(config['email']); address=h(config.get('privacy_contact_address') or 'Обязательный реквизит: адрес для обращений заполнит владелец до публикации.')
        common=f'<p>Оператор: {operator}. ИНН {h(config["inn"])}; ОГРНИП {h(config["ogrnip"])}.</p><p>Обращения: <a href="mailto:{email}">{email}</a>. {address}</p>'
        policy=f'''{draft}{common}<h2>Цель и состав данных</h2><p>Ответ на запрос оборудования, подбор, подготовка и согласование предложения. Обрабатываются компания, имя контактного лица, email, необязательный телефон, модели, количество, комментарий и приложенный перечень оборудования. Не включайте в вложения данные, не нужные для этой цели.</p><h2>Согласие и обработка</h2><p>Согласие даётся отдельно активной отметкой перед отправкой формы. Автоматическая подписка на рекламу отсутствует. Операции: сбор, запись, хранение, уточнение, использование для ответа, ограничение, удаление или обезличивание.</p><h2>Срок хранения</h2><p>Обычные заявки хранятся 12 месяцев с последнего взаимодействия, если отсутствует другое законное основание. Затем контактные данные и вложения удаляются или обезличиваются. Для договорных и бухгалтерских документов действуют отдельные обязательные сроки; они не удаляются автоматически по сроку обычной заявки.</p><h2>Ваши права</h2><p>Можно запросить сведения, уточнение, ограничение обработки, отзыв согласия или удаление. Запрос рассматривается после проверки полномочий и применимых оснований хранения; отзыв не отменяет обработку, необходимую по закону.</p><h2>Размещение и доступ</h2><p>Публичная форма активируется только после выбора места хранения в России, определения обработчиков, мер защиты и утверждения документов. Конфигурация размещения ещё не утверждена. Вложения не публикуются, доступ к заявкам ограничивается владельцем и допущенными лицами.</p>'''
        write('/privacy/','Политика обработки персональных данных','Проект политики обработки персональных данных для формы GUTSU.SPACE.',hero('ДОКУМЕНТ / ПРОЕКТ','Персональные данные.','Версия '+config['privacy_version'])+'<article class="policy-copy">'+policy+'</article>',robots='noindex,follow')
        consent=f'''{draft}{common}<p>Отправляя форму с отдельной отметкой согласия, я разрешаю обработку указанных мной контактных данных и приложений исключительно для рассмотрения моего запроса, обратной связи и подготовки предложения.</p><p>Перечень данных: компания, контактное лицо, email, телефон при его указании, описание запроса и переданные вложения. Срок — 12 месяцев после последнего взаимодействия, если нет другого законного основания. Согласие можно отозвать обращением к оператору после подтверждения полномочий. Согласия на рекламную рассылку я не даю.</p><p>До активации формы владелец проверяет реквизиты, основания, обработчиков, сроки и окончательный текст этого согласия.</p>'''
        write('/consent/','Согласие на обработку персональных данных','Отдельное согласие для ответа на запрос оборудования, без рекламной подписки.',hero('ДОКУМЕНТ / ПРОЕКТ','Согласие для формы.','Версия '+config['privacy_version'])+'<article class="policy-copy">'+consent+'</article>',robots='noindex,follow')
    (root/'404.html').write_text(page('/404.html','Страница не найдена','Перейдите к каталогу оборудования GUTSU.',hero('404 / СТРАНИЦА НЕ НАЙДЕНА','Здесь пока ничего нет.','<a href="/equipment/brands/">Перейти к брендам →</a>'),robots='noindex,follow'))
    existing=['/','/equipment/','/equipment/procurement/','/ai/','/ai/audit/','/ai/services/']
    urls=existing+[p for p in paths if p not in ['/privacy/','/consent/']]
    xml='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'  <url><loc>{ORIGIN+p}</loc></url>\n' for p in urls)+'</urlset>\n'
    (root/'sitemap.xml').write_text(xml)
    return paths

def bundle(root=ROOT,out=None,release=False,static_catalog=False):
    root=Path(root).resolve(); out=Path(out or root/'dist').resolve()
    # Never delete an arbitrary directory selected by CLI arguments.
    if out != root/'dist': raise ValueError('output_must_be_dist')
    config=json.loads((root/'data/site.json').read_text())
    if release and config.get('catalog_publication_approved') is not True:
        raise ValueError('catalog_publication_requires_owner_approval')
    if release and not static_catalog and (not config.get('privacy_documents_final') or not config.get('privacy_approved_at') or not config.get('consent_approved_at')
                    or not config.get('privacy_contact_address') or 'draft' in config.get('privacy_version','').casefold()
                    or any('policy-draft' in (root/p/'index.html').read_text() for p in ['privacy','consent'])):
        raise ValueError('draft_privacy_documents_must_not_be_published')
    if static_catalog and (config.get('public_intake_enabled') is not False or config.get('api_origin') is not None):
        raise ValueError('static_release_requires_disabled_intake')
    files=[root/n for n in ['index.html','404.html','styles.css','script.js','CNAME','robots.txt','sitemap.xml','.nojekyll']]
    routes=['equipment','equipment/procurement','ai','ai/audit','ai/services','privacy','consent','equipment/request','equipment/brands','equipment/categories']
    routes += ['equipment/brands/'+b[0] for b in BRANDS]
    routes += ['equipment/categories/'+slug for slug in CATEGORIES]
    files += [root/r/'index.html' for r in routes]
    files += [root/'equipment'/n for n in ['catalog.css','catalog.js']]
    files += [root/p for p in json.loads((root/'data/public-assets.json').read_text())]
    # Validate every input before replacing the previous successful build.
    for f in files:
        rel=f.relative_to(root)
        if f.is_symlink() or any(p.is_symlink() for p in f.parents if p!=root) or not f.resolve().is_relative_to(root) or not f.is_file():
            raise ValueError('invalid_public_input:'+str(rel))
        if str(rel).startswith('assets/') and (f.suffix not in {'.svg','.png','.webp','.jpg','.ico'} or len(rel.parts)!=2):
            raise ValueError('invalid_public_asset')
    if static_catalog:
        for f in files:
            if f.suffix=='.html' and any(x in f.read_text().lower() for x in ['<form', '<input', '<textarea', '<select', 'data-lead-form', 'gutsu-api-origin', 'policy-draft']):
                raise ValueError('interactive_or_draft_content_in_static_release:'+str(f.relative_to(root)))
    from security_audit import scan_public
    scan_public(files,root)
    if out.is_symlink(): raise ValueError('public_symlink_rejected')
    if out.exists(): shutil.rmtree(out)
    out.mkdir()
    for f in files:
        target=out/f.relative_to(root); target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(f,target)
    if len(list(p for p in out.rglob('*') if p.is_file()))!=45:
        raise ValueError('public_manifest_must_contain_45_files')
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--out',type=Path); p.add_argument('--release',action='store_true'); p.add_argument('--static-catalog',action='store_true'); a=p.parse_args()
    paths=generate(static_catalog=a.static_catalog); out=bundle(out=a.out,release=a.release,static_catalog=a.static_catalog)
    print(json.dumps({'generated_pages':len(paths),'public_bundle':str(out),'static_catalog':a.static_catalog,'published':False}))
