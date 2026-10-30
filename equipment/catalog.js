// Public catalogue context only. No forms, network requests, storage or mail sending.
(() => {
  'use strict';
  const panel = document.querySelector('[data-quote-contact]');
  if (!panel) return;
  const link = panel.querySelector('[data-quote-email]');
  const message = panel.querySelector('[data-quote-message]');
  const selection = panel.querySelector('[data-quote-selection]');
  const copy = panel.querySelector('[data-quote-copy]');
  const status = panel.querySelector('[data-quote-status]');
  let brand = panel.dataset.brand || '';
  let product = null;
  const catalogue = document.getElementById('request-catalog');
  if (catalogue) {
    const data = JSON.parse(catalogue.textContent);
    const params = new URLSearchParams(location.search);
    // Never interpolate arbitrary query text, recipient, subject or model values.
    const codes = params.getAll('code');
    if (codes.length) {
      product = codes.length === 1 ? data.products.find(item => item.code === codes[0]) : null;
      if (product) {
        brand = data.brands[product.brand];
      } else {
        selection.textContent = 'Код позиции не найден в каталоге. Откройте нужную модель заново или укажите её в письме.';
      }
    } else if (params.getAll('brand').length === 1 && Object.hasOwn(data.brands, params.get('brand'))) {
      brand = data.brands[params.get('brand')];
    }
  }
  const lines = ['Здравствуйте! Прошу подготовить коммерческое предложение.', ''];
  if (brand) lines.push('Бренд: ' + brand);
  if (product) {
    lines.push('Модель: ' + product.model, 'Код позиции GUTSU (SKU): ' + product.code,
      'Страница каталога: https://gutsu.space/equipment/brands/' + product.brand + '/', '');
    selection.textContent = brand + ' · ' + product.model + ' · ' + product.code +
      '. Код GUTSU не заменяет артикул производителя; точную версию и комплект проверим перед КП.';
  } else {
    lines.push('Модель / список оборудования: ');
    if (brand) selection.textContent = 'Запрос по бренду ' + brand + '. Укажите нужные модели или задачу в письме.';
  }
  lines.push('Количество: ', 'Город поставки: ', 'Желаемый срок: ', 'Требования к комплекту: ');
  const body = lines.join('\r\n');
  const subject = 'Запрос КП GUTSU' + (product ? ' — ' + product.model + ' — ' + product.code : brand ? ' — ' + brand : '');
  message.textContent = body;
  link.href = 'mailto:gutsuandre@gmail.com?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
  copy.hidden = false;
  copy.addEventListener('click', async () => {
    try {
      if (!navigator.clipboard || !window.isSecureContext) throw new Error('clipboard_unavailable');
      await navigator.clipboard.writeText(body);
      status.textContent = 'Текст скопирован. Вставьте его в письмо, дополните и отправьте на gutsuandre@gmail.com.';
    } catch (_) {
      const range = document.createRange();
      range.selectNodeContents(message);
      const selected = window.getSelection();
      selected.removeAllRanges();
      selected.addRange(range);
      message.focus();
      status.textContent = 'Текст выделен. Выберите «Копировать» в меню устройства или нажмите Ctrl+C / ⌘C.';
    }
  });
})();
