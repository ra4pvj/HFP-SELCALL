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
Прослушивание: после вызова (и после своей передачи) звук входа идёт в динамик заданное время, чтобы услышать голосовое сообщение или ответ станции. Кнопка «Слушать» включает прослушивание вручную; такая же кнопка есть на вкладке «HFPager» и на главной странице под кнопками декодеров — все три работают одинаково. Прослушивание после своей передачи настраивается отдельно для Selcall и для HFPager (после кадра маяка HFPager прослушивание не включается). Длина преамбулы (точек) Selcall задаётся на вкладке «HF Selcall», по умолчанию 6 с.

## Трансивер (CAT) и сценарии
На вкладке «Трансивер и аудио» можно установить частоту и режим, выбрать диапазон, перестроиться шагом. «Сценарии…» — таблица действий при получении сообщения HFPager на ваш ID (например, «QSY 7.120» → перестроить трансивер).
В списках COM-портов есть пункт «Выключено» — порт не используется. Если на компьютере один COM-порт, он не может одновременно быть портом PTT/CAT и портом внешнего устройства; при совпадении приоритет у PTT.

## Вызов HFPager и звонок
Кнопка «Вызов» в поле HFPager сразу отправляет на ID «Кому» сообщение CALL (текст вызова меняется на вкладке «HFPager»). Когда такое сообщение приходит на ваш ID, появляется жёлтая панель «☎ HFPager Вызов от …», звучит звонок, включается внешнее устройство (если отмечено), в эфир уходит ответ мелодией (подтверждение приёма на CALL не передаётся, даже если отправитель его запросил), затем включается прослушивание эфира — всё как у Selcall, настройки на вкладке «HFPager».
Обычное сообщение на ваш ID сопровождается коротким «звуком входящего сообщения» (мелодия выбирается).

## Ответ на BCN REQ
Если на ваш ID пришло сообщение «BCN REQ», программа отвечает в эфир без участия оператора: если отправитель запросил подтверждение — только подтверждением приёма (даже при выключенном автоподтверждении), если не запросил — мелодией. Звонка, звука и панели вызова у вас при этом нет: это проверка связи, не привлекающая внимания оператора. Запрос, адресованный всем (ID 0), не обрабатывается — иначе ответили бы сразу все станции. Текст запроса и мелодия — на вкладке «HFPager». Это автоматическая передача.

## Макросы
Вкладка «Маяк и макросы»: 10 макросов — подпись кнопки, что делать (сообщение или вызов HFPager, вызов или сообщение Selcall), кому (пусто — из поля под чатом), текст и «Сразу». Кнопки с подписями видны над полями ввода под чатом. Без «Сразу» макрос только заполняет поля.

## Маяк
Вкладка «Маяк и макросы»: маяк каждые N минут или в заданное время UTC. Что передавать: кадр «маяк» HFPager (как маяк приложения HFPager, всем), сообщение HFPager, вызов или сообщение Selcall, или текст телеграфом (CW, скорость и тон задаются). Маяк ждёт, пока идёт приём или своя передача. «Передать маяк сейчас» — проверка. При сканировании маяк всегда идёт на одном канале (выбирается в настройках маяка, по умолчанию канал 1): в нужное время сканер переходит на этот канал, передаёт маяк, ждёт заданное время тишины (вдруг кто-то ответит) и продолжает обход. Если сканер в этот момент стоит на канале из-за приёма, маяк ждёт конца связи.

## Сценарии для обоих протоколов
В таблице сценариев есть столбцы «Протокол» (оба / HFPager / Selcall), «От ID HFPager» и «От Selcall ID». Сценарий выполняется на сообщение HFPager на ваш ID или на Selcall-сообщение с текстом на ваш Selcall ID.

## Главная страница: декодеры, СКАН и каналы
Вверху справа от часов: кнопки «HFPager» и «Selcall» включают и выключают декодеры (при каждом запуске программы оба включены; спектр и индикатор работают и при выключенных). Под чатом: «СКАН» включает и выключает сканирование, 6 кнопок каналов сразу перестраивают трансивер на канал (во время сканирования — останавливают его на этом канале). Подписи кнопок задаются в таблице каналов или правой кнопкой мыши по кнопке. Повторный щелчок по нажатой кнопке отжимает её (трансивер не перестраивается). Когда сканирование выключено, программа каждые 2 с читает частоту трансивера по CAT: если она отличается от частоты канала, кнопка отжимается, а если трансивер настроили точно на частоту одного из каналов, нажимается кнопка этого канала. Во время передачи частота не читается; если трансивер не ответил, кнопки не меняются. При CAT «Выключено» кнопку можно отжать только вручную.

## Сканирование каналов
Вкладка «Трансивер и аудио», раздел «Сканирование»: таблица из 6 каналов — подпись кнопки, галочка «Скан», частота (МГц), режим и задержка на канале (с). Отметьте от 2 до 6 каналов и нажмите «СКАН» (на главной странице) или «Начать сканирование». Перед запуском программа запоминает частоту трансивера и после остановки возвращает его на неё (режим не восстанавливается: его нельзя прочитать по CAT). Программа перестраивает трансивер через CAT по кругу. Как только на канале начинается приём (преамбула HFPager или точки Selcall) или идёт передача, сканирование останавливается на этом канале — можно работать с вызывающей станцией. После заданного времени тишины («Возобновить после тишины») сканирование продолжается. Текущий канал показан в строке состояния.

## Длина преамбулы HFPager
Стандартная преамбула HFPager — около 3–4 с (7,5 с на 1,46 Бод). Сканирующий приёмник попадает на канал в случайный момент, и ему нужно услышать хотя бы ~2 с преамбулы. Измерено на нашем приёмнике: сигнал на канале обнаруживается через 0,3 с после перехода (так что задержки 1–1,5 с на канал достаточно), а сообщение HFPager принимается, если осталось услышать не меньше ~2 с преамбулы. Худший случай — вызов начался сразу после того, как сканер ушёл с канала: он вернётся через обход остальных каналов, (N − 1) × (задержка + перестройка). Поэтому преамбула HFPager вызывающей станции должна быть не короче этого времени + 2,3 с, а точки Selcall — + 0,6 с (Selcall принимается даже по последним 0,3 с точек). Стандартных 6 с точек CODAN хватает на 6 каналов по 1 с при быстрой перестройке трансивера, что совпадает с практикой. Время перестройки сканер измеряет сам, расчёт показан под таблицей каналов. В оригинальном HFPager сканирования нет, поэтому стандартная преамбула (3–4 с) рассчитана на приём без сканирования и годится максимум для 1–2 каналов. Длина задаётся на вкладке «HFPager» («0» — стандартная); кнопка «Для сканирования» / «Подобрать преамбулу и точки» вычисляет её по таблице сканирования и длину точек Selcall (от 6 до 20 с).
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
• Окно не помещается на экране: каждая вкладка прокручивается (полосы прокрутки появляются, когда окно меньше содержимого; колесо мыши, Shift + колесо — по горизонтали).
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
Listening: after a call (and after your own transmission) the input audio goes to the loudspeaker for the set time, to hear a voice message or the station's reply. "Listen" switches it on manually; the same button is on the «HFPager» tab and on the main page under the decoder buttons — all three work alike. Listening after your own transmission is set separately for Selcall and HFPager (it does not start after an HFPager beacon frame). The Selcall preamble (dots) length is set on the «HF Selcall» tab, default 6 s.

## Transceiver (CAT) and scenarios
On the "Transceiver & audio" tab you can set frequency and mode, choose a band and tune in steps. "Scenarios…" — a table of actions on an HFPager message to your ID (e.g. "QSY 7.120" → retune the transceiver).
COM port lists contain "Off" — the port is not used. With a single COM port it cannot be both the PTT/CAT port and the external-device port; if they are the same, PTT wins.

## HFPager call and ring
The «Call» button in the HFPager field sends the message CALL to the «To» ID at once (the call text is set on the «HFPager» tab). When such a message arrives for your ID, a yellow bar «☎ HFPager Call from …» appears, the ring sounds, the external device switches on (if ticked), the answer melody goes on air (no acknowledgement is sent for CALL, even if the sender asked for one), then listening starts — all like Selcall; the settings are on the «HFPager» tab.
An ordinary message to your ID plays a short «incoming message sound» (selectable).

## Answer to BCN REQ
When the message «BCN REQ» arrives for your ID, the program answers on air without the operator: with the acknowledgement alone if the sender asked for one (even with auto-acknowledgement off), otherwise with the melody. No ring, sound or call bar here: it is a link check that does not draw the operator's attention. A request to all (ID 0) is ignored — otherwise every station would answer at once. The request text and the melody are on the «HFPager» tab. This is an automatic transmission.

## Macros
«Beacon & macros» tab: 10 macros — button caption, what to do (HFPager message or call, Selcall call or message), to (empty = from the field under the chat), text and «At once». Buttons with captions appear above the input fields under the chat. Without «At once» a macro only fills the fields.

## Beacon
«Beacon & macros» tab: a beacon every N minutes or at given UTC times. What to send: an HFPager beacon frame (like the HFPager app beacon, to all), an HFPager message, a Selcall call or message, or text in Morse (CW, speed and tone are set). The beacon waits while a signal is being received or we transmit. «Send beacon now» tests it. While scanning, the beacon always goes out on one channel (chosen in the beacon settings, channel 1 by default): when it is due, the scanner goes to that channel, sends the beacon, waits the set time of silence (someone may answer) and goes on scanning. If the scanner is holding on a channel because of reception at that moment, the beacon waits for the contact to end.

## Scenarios for both protocols
The scenario table has the columns «Protocol» (both / HFPager / Selcall), «From HFPager ID» and «From Selcall ID». A scenario runs on an HFPager message to your ID or on a Selcall message call with text to your Selcall ID.

## Main page: decoders, SCAN and channels
At the top, right of the clocks: the «HFPager» and «Selcall» buttons switch the decoders on and off (both are on at every start of the program; the spectrum and the meter work either way). Under the chat: «SCAN» switches scanning on and off, and 6 channel buttons retune the transceiver at once (during a scan they stop it on that channel). Button captions are set in the channel table or by right-clicking a button. Clicking a pressed button again releases it (the transceiver is not retuned). When scanning is off, the program reads the transceiver frequency via CAT every 2 s: if it differs from the channel frequency, the button is released, and if the transceiver is tuned exactly to one of the channels, that channel's button is pressed. The frequency is not read while transmitting; if the transceiver does not answer, the buttons stay as they are. With CAT «Off», a button can only be released by hand.

## Channel scanning
«Transceiver & audio» tab, «Scanning» section: a table of 6 channels — button caption, «Scan» tick, frequency (MHz), mode and dwell (s). Tick 2 to 6 channels and press «SCAN» (main page) or «Start scanning». Before starting, the program remembers the transceiver frequency and returns to it after stopping (the mode is not restored: it cannot be read via CAT). The program retunes the transceiver via CAT in a circle. As soon as reception starts on a channel (HFPager preamble or Selcall dots) or we transmit, scanning stops on that channel so you can work the calling station. After the set time of silence («Resume after silence») scanning continues. The current channel is shown in the status bar.

## HFPager preamble length
The standard HFPager preamble is about 3–4 s (7.5 s at 1.46 Bd). A scanning receiver lands on the channel at a random moment and needs to hear at least ~2 s of preamble. Measured with our receiver: a signal is detected 0.3 s after landing on the channel (so a dwell of 1–1.5 s per channel is enough), and an HFPager message decodes if at least ~2 s of preamble is still to come. Worst case — the call starts just after the scanner left the channel: it comes back after the round over the other channels, (N − 1) × (dwell + retune). So the calling station's HFPager preamble must be at least that + 2.3 s, and Selcall dots + 0.6 s (Selcall decodes even from the last 0.3 s of dots). The standard 6 s CODAN dots cover 6 channels of 1 s with a fast-retuning transceiver, as in practice. The scanner measures the retune time itself; the calculation is shown under the channel table. The original HFPager has no scanning, so its standard preamble (3–4 s) is meant for reception without scanning and is good for 1–2 channels at most. The length is set on the «HFPager» tab («0» = standard); the «For scanning» / «Fit preamble and dots» button computes it from the scan table and the Selcall dots (6 to 20 s).
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
• The window does not fit the screen: every tab scrolls (scrollbars appear when the window is smaller than the content; mouse wheel, Shift + wheel sideways).
• The input "falls asleep" (e.g. IC-705 over USB): the program restarts reception by itself if the audio stops for more than 4 s.
"""


def get(lang):
    return EN if lang == 'en' else RU
