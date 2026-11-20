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
