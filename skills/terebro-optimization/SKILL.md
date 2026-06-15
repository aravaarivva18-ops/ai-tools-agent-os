---
name: terebro-optimization
description: Guidelines and exact font mapping specifications for optimizing the terebro-gnb.com Tilda website.
---

# Оптимизация сайта Tilda: terebro-gnb.com

Этот навык содержит правила и точные технические спецификации для оптимизации верстки, шрифтов и скриптов сайта `terebro-gnb.com`.

---

## 1. 🔤 Шрифты и Типографика (LCP / FCP)
* **Семейство**: Всегда используйте `'Opensans'` (символ `s` в нижнем регистре) в CSS-правилах для переопределения шрифтов сайта.
* **Спецификация файлов шрифтов**:
  * **Oswald-Medium** (вес `100`):
    `https://static.tildacdn.com/tild6339-3266-4861-a562-663932383063/Oswald-Medium_1.woff`
  * **Oswald-Regular** (вес `200`):
    `https://static.tildacdn.com/tild3537-3636-4661-b836-666436373562/Oswald-Regular.woff`
  * **OpenSans-LightItalic** (вес `300`):
    `https://static.tildacdn.com/tild3933-6439-4966-b131-303431386465/OpenSans-LightItalic.woff`
  * **OpenSans-Regular** (вес `400`):
    `https://static.tildacdn.com/tild3961-3631-4935-a263-623938353262/OpenSans-Regular.woff`
  * **OpenSans-SemiBold** (вес `600`):
    `https://static.tildacdn.com/tild3039-3738-4562-b836-636363366466/OpenSans-SemiBold.woff`
  * **OpenSans-Bold** (вес `700`):
    `https://static.tildacdn.com/tild3038-6338-4863-b365-306366306235/OpenSans-Bold.woff`

* **Критические правила preloading**:
  * Не прелоадить Montserrat. Прелоадить только используемые файлы Oswald и OpenSans (веса 100, 200, 400, 600, 700).
  * LCP-изображение (десктопный бэкграунд `2323.jpg`) прелоадить только для десктопов с помощью `media="(min-width: 980px)"`.

* **Форсирование `font-display: swap`**:
  * Поскольку Tilda загружает файлы CSS позже, инжектируйте правила `@font-face` динамически через JS:
    ```javascript
    var fontStyle = document.createElement('style');
    fontStyle.textContent = "...";
    document.head.appendChild(fontStyle);
    ```

---

## 2. 🏷️ Микроразметка (Schema.org)
* **Запрет на дублирование**: Никогда не вставляйте Schema.org JSON-LD (разметка `Organization`) внутрь кастомного HEAD-файла. Она уже настроена глобально в Tilda и генерируется платформой. Дубликаты вызывают критические ошибки валидатора поисковиков.

---

## 3. ⚡ Производительность скриптов (TBT)
* **Яндекс.Метрика**: Инициализируется **синхронно** непосредственно в `<head>` во избежание потери данных о трафике (особенно при работе DDoS-Guard/сетевых задержках). Запрещено использовать lazy-load для Метрики.
* **Кастомные виджеты (Callibri, BotFAQtor)**: Должны загружаться **лениво** через функцию `loadWidgets()` по первому действию пользователя (scroll, touch, mousemove, click) или по таймеру задержки в 4500 мс для оптимизации Total Blocking Time (TBT).
* **Дублирование**: Поле счетчика в интерфейсе Tilda Settings -> Аналитика должно оставаться пустым при использовании кастомного кода в HEAD.
