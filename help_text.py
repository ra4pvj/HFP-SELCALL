"""User guide shown by Help → Instructions (F1).  Lines starting with '# ' / '## ' are headings."""

RU = """# HFP+SELCALL — инструкция

Программа работает с двумя протоколами КВ-связи через звуковую карту компьютера, подключённую к трансиверу (SSB, обычно USB):
• HFPager (КВ-пейджер, PS-18) — короткие текстовые сообщения между ID 0…65535, совместимо с приложением HFPager;
• HF Selcall по CCIR 493-4, совместимый с CODAN, — индивидуальный вызов и вызов с сообщением (до 64 символов).
Оба приёмника слушают вход одновременно, переключать режимы не нужно.

## Первый запуск
1. Вкладка «Трансивер и аудио»: выберите вход (приём) и выход (передача) звуковой карты, канал входа («авто» — где есть сигнал).
2. Там же — уровень TX и задержка PTT/VOX; способ включения передачи (PTT): none (VOX), RTS/DTR COM-порта, CAT (YAESU, KENWOOD, ICOM…).
3. Вкладка «HFPager»: свой ID, скорость, тон 0. Вкладка «HF Selcall»: свой Selcall ID (4 или 6 цифр).
4. Нажмите «Применить». Первую передачу делайте на эквивалент нагрузки.

## Главное окно
Вверху всегда видны: лампы RX/TX, индикатор уровня входа, спектр 300–3000 Гц и часы (UTC и выбранный часовой пояс). Ниже — вкладки. Первая, «Чат и сообщения», — главная: сверху общий журнал обмена, под ним поля ввода сообщений и вызовов HFPager (слева) и HF Selcall (справа).
Цвета в чате: зелёный жирный — адресованное вам, голубой — чужое, красный — ваши передачи, жёлтый — служебные сообщения.
Текст из чата можно выделить мышью и скопировать (Ctrl+C или правая кнопка мыши → «Копировать»).

## Уровень входа
Индикатор показывает пиковый уровень в dBFS (0 dBFS — полная шкала звуковой карты):
• зелёный — ниже −12 dBFS, нормально;
• жёлтый — от −12 до −3 dBFS, громко;
• красный — выше −3 dBFS, опасно.
Перегрузка — отсчёты достигают 98 % полной шкалы (−0,2 dBFS): появляется надпись «ПЕРЕГРУЗКА ВХОДА». Сигнал искажается, в спектре появляются лишние составляющие, приём ухудшается. Уменьшите уровень на выходе трансивера или в настройках звука системы. Во время перегрузки шкала спектра не подстраивается, чтобы картинка не «прыгала».

## Сообщения и вызовы (вкладка «Чат и сообщения»)
HFPager: «Кому (ID)», текст до 252 символов, «Отправить» (или Enter). Символы сверх предела выделяются красным и не передаются — сократите текст.
HF Selcall: «Кому (Selcall ID)»; «Вызов» — вызов без текста, «Сообщение» — вызов с текстом (до 64 символов после транслитерации; кириллица передаётся латиницей, если включён «Транслит»).
«Прервать» останавливает текущую передачу и снимает PTT.

## Входящий вызов Selcall
Над вкладками появляется жёлтая панель «☎ … от NNNN» с кнопками «Ответить» (подставляет отправителя в поле Selcall «Кому» под чатом) и «Сбросить». Звучит звонок (тип, длительность и устройство — на вкладке «HF Selcall»).
Ответ в эфир: через 1 с программа один раз передаёт сигнал ответа (по умолчанию мелодия), чтобы вызывающий слышал, что вызов принят. Это автоматическая передача — выключите, если она не нужна.
Прослушивание: после вызова (и после своей передачи) звук входа идёт в динамик заданное время, чтобы услышать голосовое сообщение или ответ станции. Кнопка «Слушать» включает прослушивание вручную.

## Трансивер (CAT) и сценарии
На вкладке «Трансивер и аудио» можно установить частоту и режим, выбрать диапазон, перестроиться шагом. «Сценарии…» — таблица действий при получении сообщения HFPager на ваш ID (например, «QSY 7.120» → перестроить трансивер).
В списках COM-портов есть пункт «Выключено» — порт не используется. Если на компьютере один COM-порт, он не может одновременно быть портом PTT/CAT и портом внешнего устройства; при совпадении приоритет у PTT.

## Вызов HFPager и звонок
Кнопка «Вызов» в поле HFPager сразу отправляет на ID «Кому» сообщение CALL (текст вызова меняется на вкладке «HFPager»). Когда такое сообщение приходит на ваш ID, появляется жёлтая панель «☎ HFPager Вызов от …», звучит звонок, включается внешнее устройство (если отмечено), в эфир уходит ответ мелодией (после автоподтверждения, если оно включено), затем включается прослушивание эфира — всё как у Selcall, настройки на вкладке «HFPager».
Обычное сообщение на ваш ID сопровождается коротким «звуком входящего сообщения» (мелодия выбирается).

## Ответ на BCN REQ
Если на ваш ID пришло сообщение «BCN REQ», программа отвечает мелодией в эфир. Запрос, адресованный всем (ID 0), не обрабатывается — иначе ответили бы сразу все станции. Текст запроса и мелодия — на вкладке «HFPager». Это автоматическая передача.

## Макросы
Вкладка «Маяк и макросы»: 10 макросов — подпись кнопки, что делать (сообщение или вызов HFPager, вызов или сообщение Selcall), кому (пусто — из поля под чатом), текст и «Сразу». Кнопки с подписями видны над полями ввода под чатом. Без «Сразу» макрос только заполняет поля.

## Маяк
Вкладка «Маяк и макросы»: маяк каждые N минут или в заданное время UTC. Что передавать: кадр «маяк» HFPager (как маяк приложения HFPager, всем), сообщение HFPager, вызов или сообщение Selcall, или текст телеграфом (CW, скорость и тон задаются). Маяк ждёт, пока идёт приём или своя передача. «Передать маяк сейчас» — проверка.

## Сценарии для обоих протоколов
В таблице сценариев есть столбцы «Протокол» (оба / HFPager / Selcall), «От ID HFPager» и «От Selcall ID». Сценарий выполняется на сообщение HFPager на ваш ID или на Selcall-сообщение с текстом на ваш Selcall ID.

## Сканирование каналов
Вкладка «Трансивер и аудио», раздел «Сканирование»: таблица из 8 каналов — галочка, частота (МГц), режим и задержка на канале (с). Отметьте от 2 до 8 каналов и нажмите «Начать сканирование». Программа перестраивает трансивер через CAT по кругу. Как только на канале начинается приём (преамбула HFPager или точки Selcall) или идёт передача, сканирование останавливается на этом канале — можно работать с вызывающей станцией. После заданного времени тишины («Возобновить после тишины») сканирование продолжается. Текущий канал показан в строке состояния.

## Длина преамбулы HFPager
Стандартная преамбула HFPager — около 3–4 с (7,5 с на 1,46 Бод). Сканирующий приёмник попадает на канал в случайный момент, и ему нужно услышать хотя бы ~2 с преамбулы. Измерено на нашем приёмнике: сигнал на канале обнаруживается через 0,3 с после перехода (так что задержки 1–1,5 с на канал достаточно), а сообщение HFPager принимается, если осталось услышать не меньше ~2 с преамбулы. Поэтому для вызова сканирующей станции преамбула HFPager должна быть не короче цикла её сканирования (сумма задержек) + 2,5 с. Selcall принимается даже по последним 0,3 с точек, поэтому точек хватает на цикл + 1 с: стандартные 6 с CODAN — это 5–6 каналов по 1 с, что совпадает с практикой. В оригинальном HFPager сканирования нет, поэтому стандартная преамбула (3–4 с) рассчитана на приём без сканирования и годится максимум для 1–2 каналов. Длина задаётся на вкладке «HFPager» («0» — стандартная); кнопка «Для сканирования» / «Подобрать преамбулу и точки» вычисляет её по таблице сканирования и длину точек Selcall (цикл + 1 с, от 6 до 20 с).
Удлинённая преамбула — это та же последовательность символов, только длиннее; наш приёмник принимает её на всех скоростях, в том числе когда услышан только конец. Принимает ли её оригинальное приложение HFPager, проверить не удалось — проверьте на своём телефоне.

## Внешнее устройство
Сирена, лампа или реле на отдельном COM-порту: при вызове на ваш ID на линию RTS/DTR подаётся «1» на заданное время. «Импульс» — проверка, «Внешн.» — включить вручную до повторного нажатия.

## Отложенные сообщения (QRU?)
Меню «Файл → Отложенные сообщения». Сообщения для станций, которые сейчас не слушают: когда станция присылает «QRU?», программа отправляет ей её сообщения и удаляет их из очереди после подтверждения доставки.

## Буфер обмена
Во всех полях ввода и в чате работают Ctrl+C / Ctrl+V / Ctrl+X / Ctrl+A (на macOS — Cmd), в том числе при русской раскладке, и меню по правой кнопке мыши.

## Программа
Вкладка «Программа» и меню «Вид»: язык (русский / English), тема (светлая / тёмная), часовой пояс вторых часов, папка журнала и отложенных сообщений. Все сообщения записываются в текстовый журнал messages.txt (меню «Файл → Открыть журнал»).

## Если что-то не работает
• Нет приёма: проверьте вход и канал, уровень (индикатор должен двигаться), выключите перегрузку.
• Нет передачи: проверьте метод PTT и COM-порт («Тест PTT»), выход звуковой карты и уровень TX.
• Вход «засыпает» (например IC-705 по USB): программа сама перезапускает приём, если звук пропал больше чем на 4 с.
"""

EN = """# HFP+SELCALL — user guide

The program works with two HF protocols through the computer's sound card connected to the transceiver (SSB, usually USB):
• HFPager (PS-18) — short text messages between IDs 0…65535, compatible with the HFPager app;
• HF Selcall per CCIR 493-4, CODAN-compatible — individual call and message call (up to 64 characters).
Both receivers listen to the input at the same time; there is no mode switch.

## First start
1. "Transceiver & audio" tab: choose the sound card input (receive) and output (transmit) and the input channel ("auto" = the one with signal).
2. On the same tab: TX level and PTT/VOX delay; PTT method: none (VOX), RTS/DTR of a COM port, CAT (YAESU, KENWOOD, ICOM…).
3. "HFPager" tab: your ID, speed, tone 0. "HF Selcall" tab: your Selcall ID (4 or 6 digits).
4. Press "Apply". Make the first transmission into a dummy load.

## Main window
Always visible at the top: RX/TX lamps, input level meter, 300–3000 Hz spectrum and the clocks (UTC and a chosen time zone). Below are the tabs. The first one, "Chat & messages", is the main page: the common message log on top, and under it the message / call fields for HFPager (left) and HF Selcall (right).
Chat colours: bold green — addressed to you, cyan — to others, red — your transmissions, yellow — service messages.
Chat text can be selected and copied (Ctrl+C or right click → "Copy").

## Input level
The meter shows the peak level in dBFS (0 dBFS = full scale of the sound card):
• green — below −12 dBFS, fine;
• yellow — −12 to −3 dBFS, loud;
• red — above −3 dBFS, dangerous.
Overload — samples reach 98 % of full scale (−0.2 dBFS): "INPUT OVERLOAD" is shown. The signal is distorted, extra components appear in the spectrum and reception gets worse. Lower the transceiver's output or the system recording level. During an overload the spectrum colour scale is frozen so the picture does not jump.

## Messages and calls ("Chat & messages" tab)
HFPager: "To (ID)", text up to 252 characters, "Send" (or Enter). Characters beyond the limit are shown red and are not sent — shorten the text.
HF Selcall: "To (Selcall ID)"; "Call" — a call without text, "Message" — a call with text (up to 64 characters after transliteration; Cyrillic is sent in Latin letters when "Translit" is on).
"Abort" stops the current transmission and releases PTT.

## Incoming Selcall
A yellow bar "☎ … from NNNN" appears above the tabs with "Answer" (fills in the sender in the Selcall "To" field under the chat) and "Dismiss". The ring sounds (type, duration and device are on the "HF Selcall" tab).
Answer on air: after 1 s the program transmits the answer signal once (a melody by default) so the caller hears that the call was received. This is an automatic transmission — switch it off if you do not want it.
Listening: after a call (and after your own transmission) the input audio goes to the loudspeaker for the set time, to hear a voice message or the station's reply. "Listen" switches it on manually.

## Transceiver (CAT) and scenarios
On the "Transceiver & audio" tab you can set frequency and mode, choose a band and tune in steps. "Scenarios…" — a table of actions on an HFPager message to your ID (e.g. "QSY 7.120" → retune the transceiver).
COM port lists contain "Off" — the port is not used. With a single COM port it cannot be both the PTT/CAT port and the external-device port; if they are the same, PTT wins.

## HFPager call and ring
The «Call» button in the HFPager field sends the message CALL to the «To» ID at once (the call text is set on the «HFPager» tab). When such a message arrives for your ID, a yellow bar «☎ HFPager Call from …» appears, the ring sounds, the external device switches on (if ticked), the answer melody goes on air (after the auto-confirmation, if that is on), then listening starts — all like Selcall; the settings are on the «HFPager» tab.
An ordinary message to your ID plays a short «incoming message sound» (selectable).

## Answer to BCN REQ
When the message «BCN REQ» arrives for your ID, the program answers with a melody on air. A request to all (ID 0) is ignored — otherwise every station would answer at once. The request text and the melody are on the «HFPager» tab. This is an automatic transmission.

## Macros
«Beacon & macros» tab: 10 macros — button caption, what to do (HFPager message or call, Selcall call or message), to (empty = from the field under the chat), text and «At once». Buttons with captions appear above the input fields under the chat. Without «At once» a macro only fills the fields.

## Beacon
«Beacon & macros» tab: a beacon every N minutes or at given UTC times. What to send: an HFPager beacon frame (like the HFPager app beacon, to all), an HFPager message, a Selcall call or message, or text in Morse (CW, speed and tone are set). The beacon waits while a signal is being received or we transmit. «Send beacon now» tests it.

## Scenarios for both protocols
The scenario table has the columns «Protocol» (both / HFPager / Selcall), «From HFPager ID» and «From Selcall ID». A scenario runs on an HFPager message to your ID or on a Selcall message call with text to your Selcall ID.

## Channel scanning
«Transceiver & audio» tab, «Scanning» section: a table of 8 channels — tick, frequency (MHz), mode and dwell (s). Tick 2 to 8 channels and press «Start scanning». The program retunes the transceiver via CAT in a circle. As soon as reception starts on a channel (HFPager preamble or Selcall dots) or we transmit, scanning stops on that channel so you can work the calling station. After the set time of silence («Resume after silence») scanning continues. The current channel is shown in the status bar.

## HFPager preamble length
The standard HFPager preamble is about 3–4 s (7.5 s at 1.46 Bd). A scanning receiver lands on the channel at a random moment and needs to hear at least ~2 s of preamble. Measured with our receiver: a signal is detected 0.3 s after landing on the channel (so a dwell of 1–1.5 s per channel is enough), and an HFPager message decodes if at least ~2 s of preamble is still to come. So to call a scanning station the HFPager preamble must be at least its scan cycle (sum of dwells) + 2.5 s. Selcall decodes even from the last 0.3 s of dots, so dots must cover cycle + 1 s: the CODAN standard 6 s is 5–6 channels of 1 s, as in practice. The original HFPager has no scanning, so its standard preamble (3–4 s) is meant for reception without scanning and is good for 1–2 channels at most. The length is set on the «HFPager» tab («0» = standard); the «For scanning» / «Fit preamble and dots» button computes it from the scan table and the Selcall dots (cycle + 1 s, 6 to 20 s).
The long preamble is the same symbol sequence, only longer; our receiver accepts it at all speeds, also when only its end is heard. Whether the original HFPager app accepts it could not be tested — please check with your phone.

## External device
A siren, lamp or relay on a separate COM port: on a call to your ID "1" is put on RTS/DTR for the set time. "Pulse" tests it, "Ext." switches it on until pressed again.

## Deferred messages (QRU?)
Menu "File → Deferred messages". Messages for stations that are not listening now: when the station sends "QRU?", the program sends its messages and removes them from the queue after a delivery confirmation.

## Clipboard
Ctrl+C / Ctrl+V / Ctrl+X / Ctrl+A (Cmd on macOS) work in all input fields and in the chat, also with a non-Latin keyboard layout, and there is a right-click menu.

## Program
"Program" tab and the "View" menu: language (Русский / English), theme (light / dark), time zone of the second clock, folder of the journal and deferred messages. All messages are written to the text journal messages.txt (menu "File → Open journal").

## Troubleshooting
• No reception: check the input and channel, the level (the meter must move), avoid overload.
• No transmission: check the PTT method and COM port ("PTT test"), the sound card output and the TX level.
• The input "falls asleep" (e.g. IC-705 over USB): the program restarts reception by itself if the audio stops for more than 4 s.
"""


def get(lang):
    return EN if lang == 'en' else RU
