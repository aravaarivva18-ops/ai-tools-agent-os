document.addEventListener('DOMContentLoaded', () => {
    const messagesContainer = document.getElementById('messages-container');
    const chatInput = document.getElementById('chat-input');
    const btnSend = document.getElementById('btn-send');
    const btnCalculate = document.getElementById('btn-calculate');
    const scenarioButtons = document.querySelectorAll('.btn-scenario');

    // Настройки калькулятора
    const inputWidth = document.getElementById('width');
    const inputLength = document.getElementById('length');
    const inputHeight = document.getElementById('height');
    const selectThickness = document.getElementById('thickness');

    // Базовые параметры
    const PRICE_PER_CUBIC_METER = 5800; // средняя цена Bikton за куб
    const BLOCK_LENGTH = 0.625; // 625 мм
    const BLOCK_HEIGHT = 0.250; // 250 мм
    
    let activeScenario = 'calc';
    let typingTimeout = null;
    let followUpTimeout = null;

    // Сценарии сообщений
    const scenarios = {
        calc: {
            user: "Здравствуйте! Хочу рассчитать газобетон на дом. Размеры 10 на 12 метров, высота стен 3 метра. Нам советовали толщину стен 400 мм. Сколько нужно блоков и какая цена?",
            ai: (width, length, height, thickness) => {
                const w = parseFloat(width) || 10;
                const l = parseFloat(length) || 12;
                const h = parseFloat(height) || 3;
                const t = parseFloat(thickness) || 400;
                
                const perimeter = (w + l) * 2;
                const wallArea = perimeter * h;
                const thicknessM = t / 1000;
                const volumeRaw = wallArea * thicknessM;
                const volumeFinal = Math.round(volumeRaw * 0.85 * 100) / 100; // 15% на проемы
                
                const blockVolume = BLOCK_LENGTH * thicknessM * BLOCK_HEIGHT;
                const blocksCount = Math.ceil(volumeFinal / blockVolume);
                const totalPrice = Math.round(volumeFinal * PRICE_PER_CUBIC_METER);

                return `Здравствуйте! С удовольствием помогу рассчитать объем и стоимость газобетонных блоков.

Давайте сделаем предварительный расчет для коробки дома ${w}х${l} м, высотой ${h} м, толщиной стен ${t} мм (D400/D500):

1. **Периметр коробки**: (${w} + ${l}) * 2 = ${perimeter} м.
2. **Площадь стен**: ${perimeter} * ${h} = ${wallArea} кв.м.
3. **Объем без учета проемов**: ${wallArea} * ${thicknessM} = ${volumeRaw.toFixed(2)} куб.м.
4. **Объем за вычетом проемов** (окна/двери, средний коэф. 0.85): **${volumeFinal} куб.м.** (это примерно **${blocksCount} шт.** блоков размером 625х${t}х250 мм).

💰 **Стоимость блоков Bikton** (Ижевск) сейчас составляет от ${PRICE_PER_CUBIC_METER.toLocaleString('ru-RU')} руб/куб.м.
**Ориентировочная стоимость материала**: ${volumeFinal} куб.м * ${PRICE_PER_CUBIC_METER.toLocaleString('ru-RU')} руб = **${totalPrice.toLocaleString('ru-RU')} рублей**.

*Примечание: Дополнительно понадобятся клей-пена или кладочная смесь, арматура для армирования рядов и U-блоки под армопояс.*

У вас уже есть готовый проект или планировка? Могу передать расчет нашему инженеру для точной сметы, и мы зафиксируем за вами скидку на доставку!`;
            },
            followUp: "Кстати, сейчас действует акция: при заказе газобетона от 40 куб.м дарим скидку 5% на клей-пену и бесплатное хранение на нашем складе до начала строительства.\n\nУдобно будет получить точный расчет доставки манипулятором до вашего участка?"
        },
        compare: {
            user: "А в чем разница между блоками ЗЯБ и Bikton? Что лучше выбрать для Ижевска? ЗЯБ вроде подешевле выходит.",
            ai: "Отличный вопрос! Действительно, ЗЯБ (Набережные Челны) и Bikton (Казань) — самые популярные блоки в Удмуртии, но у них есть важные технические различия:\n\n" +
                "1. 📐 **Геометрия и пазы**:\n" +
                "   • **Bikton**: Производится на немецком оборудовании Masa-Henke. Идеальная геометрия (отклонение до 1 мм). Кладка идет на тонкошовный клей-пену, что исключает «мостики холода». Есть удобная система паз-гребень и захваты для рук.\n" +
                "   • **ЗЯБ**: Геометрия попроще (отклонения до 2-3 мм), чаще укладывается на обычный раствор, что увеличивает расход смеси и теплопотери.\n\n" +
                "2. 🌡️ **Теплопроводность и плотность**:\n" +
                "   • У Bikton D400 прочность на сжатие выше при меньшей плотности, то есть стены будут теплее при той же толщине. ЗЯБ D500 плотнее и прочнее, но холоднее (потребуется больше утеплителя).\n\n" +
                "3. 💳 **Итоговая стоимость**:\n" +
                "   • ЗЯБ за куб стоит чуть дешевле (на 200-300 рублей), но из-за расхода раствора для швов и более сложной штукатурки неровных стен итоговая смета коробки «под ключ» выходит даже дороже, чем с Bikton.\n\n" +
                "Мы рекомендуем Bikton для жилых домов и ЗЯБ для неотапливаемых построек (гаражи, хозблоки).\n\n" +
                "Подскажите, вы строите дом для постоянного проживания или дачу? Помогу подобрать оптимальную плотность.",
            followUp: "Если хотите, я могу выслать вам сравнительную таблицу характеристик и расчет стоимости кладки под ключ для обоих вариантов. Куда удобнее отправить — сюда или в WhatsApp?"
        },
        discount: {
            user: "Нам предложили Bikton по 5600 руб/куб у другого дилера в Ижевске. Вы можете сделать дешевле? Нам нужно 45 кубов.",
            ai: "Понимаю ваше желание сэкономить на объеме, 45 кубов — это серьезный заказ.\n\n" +
                "Мы являемся официальным дилером завода Bikton, поэтому гарантируем оригинальное качество, правильное хранение и честную цену.\n\n" +
                "Давайте сделаем так: мы готовы дать лучшую смету «под ключ». Для этого мне нужно уточнить:\n" +
                "1. Включена ли в те 5600 рублей доставка до участка и разгрузка манипулятором? (Часто конкуренты занижают цену блока, но накручивают на логистике).\n" +
                "2. Какой способ оплаты планируете (наличные, карта, безнал с НДС)?\n\n" +
                "Напишите адрес вашего участка, я рассчитаю доставку напрямую с завода нашей машиной. Если у вас есть КП от другого дилера, пришлите его — мы сделаем встречное предложение с дополнительной скидкой!",
            followUp: "Для объема 45 кубов мы также можем согласовать спец-условия по доставке. Напишите, пожалуйста, кадастровый номер или название населенного пункта, где планируется стройка."
        }
    };

    // Очистить тайм-ауты
    function clearPendingTimeouts() {
        if (typingTimeout) clearTimeout(typingTimeout);
        if (followUpTimeout) clearTimeout(followUpTimeout);
    }

    // Рендер сообщения
    function appendMessage(sender, text, isAi = false) {
        const wrapper = document.createElement('div');
        wrapper.className = `msg-wrapper ${isAi ? 'ai' : 'user'}`;

        const senderSpan = document.createElement('span');
        senderSpan.className = 'msg-sender';
        senderSpan.textContent = sender;

        const bubble = document.createElement('div');
        bubble.className = 'msg-bubble';
        
        // Преобразуем маркдаун-подобные переносы строк и жирный шрифт в HTML
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/• (.*?)\n/g, '• $1<br>')
            .replace(/\n/g, '<br>');
            
        bubble.innerHTML = formattedText;

        wrapper.appendChild(senderSpan);
        wrapper.appendChild(bubble);
        messagesContainer.appendChild(wrapper);
        
        // Прокрутка вниз
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return wrapper;
    }

    // Рендер индикатора печатания
    function showTypingIndicator() {
        const wrapper = document.createElement('div');
        wrapper.className = 'msg-wrapper ai id-typing';

        const senderSpan = document.createElement('span');
        senderSpan.className = 'msg-sender';
        senderSpan.textContent = 'ИИ-Менеджер чатов (Кирпич Центр)';

        const bubble = document.createElement('div');
        bubble.className = 'msg-bubble';

        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            indicator.appendChild(dot);
        }

        bubble.appendChild(indicator);
        wrapper.appendChild(senderSpan);
        wrapper.appendChild(bubble);
        messagesContainer.appendChild(wrapper);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return wrapper;
    }

    function removeTypingIndicator() {
        const indicators = document.querySelectorAll('.id-typing');
        indicators.forEach(ind => ind.remove());
    }

    // Симуляция ответа ИИ
    function simulateAiResponse(userMessage, aiMessageGenerator, followUpText, delay = 2000) {
        clearPendingTimeouts();
        
        // 1. Показываем сообщение пользователя
        appendMessage('Клиент', userMessage, false);

        // 2. Через 500мс показываем индикатор набора текста
        typingTimeout = setTimeout(() => {
            showTypingIndicator();
            
            // 3. Через `delay` меняем индикатор на ответ ИИ
            typingTimeout = setTimeout(() => {
                removeTypingIndicator();
                
                let actualResponse = typeof aiMessageGenerator === 'function' 
                    ? aiMessageGenerator(inputWidth.value, inputLength.value, inputHeight.value, selectThickness.value)
                    : aiMessageGenerator;
                
                appendMessage('ИИ-Менеджер чатов (Кирпич Центр)', actualResponse, true);

                // 4. Через 6 секунд отправляем авто-дожим (follow-up)
                if (followUpText) {
                    followUpTimeout = setTimeout(() => {
                        showTypingIndicator();
                        
                        followUpTimeout = setTimeout(() => {
                            removeTypingIndicator();
                            appendMessage('ИИ-Менеджер чатов (Кирпич Центр)', followUpText, true);
                        }, 1500);
                    }, 6000);
                }

            }, delay);
        }, 600000 % 500); // 500мс
    }

    // Инициализация сценария
    function initScenario(scenarioKey) {
        messagesContainer.innerHTML = '';
        clearPendingTimeouts();
        
        const scenario = scenarios[scenarioKey];
        activeScenario = scenarioKey;
        
        // Симулируем диалог для выбранного сценария
        simulateAiResponse(scenario.user, scenario.ai, scenario.followUp, 2000);
    }

    // Переключение сценариев
    scenarioButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            scenarioButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const scenario = btn.getAttribute('data-scenario');
            initScenario(scenario);
        });
    });

    // Обработка ручного ввода клиента
    function handleManualSend() {
        const text = chatInput.value.trim();
        if (!text) return;

        chatInput.value = '';
        appendMessage('Клиент', text, false);

        // Анализ ключевых слов для генерации контекстного ответа
        let aiResponse = "";
        let followUp = "";
        
        const textLower = text.toLowerCase();
        
        if (textLower.includes('доставк') || textLower.includes('манипулятор') || textLower.includes('привезти')) {
            aiResponse = "Для точного расчета доставки мне понадобится адрес или кадастровый номер вашего участка. Мы возим блоки напрямую с завода спецтехникой (длинномеры или манипуляторы для разгрузки поддонов).\n\nНапишите, пожалуйста, населенный пункт (или район Ижевска), я сделаю точный расчет логистики.";
            followUp = "Кстати, при заказе от 30 поддонов мы дарим скидку 10% на доставку манипулятором!";
        } else if (textLower.includes('скидк') || textLower.includes('дешев') || textLower.includes('акци') || textLower.includes('промо')) {
            aiResponse = "У нас действует гибкая система скидок от объема. Напрямую от завода Bikton мы можем предложить дилерские цены на объем от 30 кубов.\n\nКакое общее количество блоков вам необходимо? Я согласую максимальную скидку у руководства.";
            followUp = "Также у нас сейчас бесплатное хранение на складе: вы можете купить блоки по зимней/весенней цене, а забрать летом, когда начнется стройка.";
        } else if (textLower.includes('зяб') || textLower.includes('биктон') || textLower.includes('сравн')) {
            aiResponse = scenarios.compare.ai;
            followUp = scenarios.compare.followUp;
        } else if (textLower.includes('расчет') || textLower.includes('посчита') || textLower.includes('куб') || textLower.includes('размер')) {
            aiResponse = scenarios.calc.ai(inputWidth.value, inputLength.value, inputHeight.value, selectThickness.value);
            followUp = scenarios.calc.followUp;
        } else if (textLower.includes('телефон') || textLower.includes('номер') || textLower.includes('созвон') || textLower.includes('ватсап') || textLower.includes('whatsapp')) {
            aiResponse = "Отлично! Наш ведущий менеджер свяжется с вами в течение 5 минут. Пожалуйста, напишите ваш номер телефона, если он отличается от номера в профиле.";
        } else {
            aiResponse = "Спасибо за сообщение! Я ИИ-ассистент компании «Кирпич Центр». С удовольствием отвечу на любые вопросы по газобетонным блокам (расчет объема, сравнение брендов Bikton/ЗЯБ, условия доставки и скидки).\n\nХотите сделать быстрый расчет блоков для вашего дома? Укажите размеры коробки (длину, ширину, высоту) или просто напишите ваш вопрос.";
        }

        // Показываем индикатор набора текста и отвечаем
        showTypingIndicator();
        typingTimeout = setTimeout(() => {
            removeTypingIndicator();
            appendMessage('ИИ-Менеджер чатов (Кирпич Центр)', aiResponse, true);
            
            if (followUp) {
                followUpTimeout = setTimeout(() => {
                    showTypingIndicator();
                    followUpTimeout = setTimeout(() => {
                        removeTypingIndicator();
                        appendMessage('ИИ-Менеджер чатов (Кирпич Центр)', followUp, true);
                    }, 1200);
                }, 5000);
            }
        }, 1500);
    }

    btnSend.addEventListener('click', handleManualSend);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            handleManualSend();
        }
    });

    // Обработка клика по интерактивному калькулятору
    btnCalculate.addEventListener('click', () => {
        const w = inputWidth.value;
        const l = inputLength.value;
        const h = inputHeight.value;
        const t = selectThickness.value;

        // Переводим калькулятор в фокус и отправляем кастомный запрос от пользователя
        const userMsg = `Рассчитайте блоки для дома: длина ${l}м, ширина ${w}м, высота ${h}м, толщина стены ${t}мм.`;
        
        simulateAiResponse(
            userMsg, 
            scenarios.calc.ai, 
            scenarios.calc.followUp, 
            1800
        );
    });

    // Запускаем первый сценарий по умолчанию при загрузке
    initScenario('calc');
});
