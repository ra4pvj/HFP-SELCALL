"""English interface text: Russian source string -> English.  Kept in sync by tests/test_i18n.py."""

EN = {
    '# HFPager: отложенные сообщения. Одна строка = одно сообщение:  ID получателя|текст\n# Строки с # и пустые игнорируются. Кодировка UTF-8. Файл можно править вручную или из другой программы:\n# приложение перечитывает его при изменении и при запросе QRU?. Отправленные строки удаляются\n# отсюда и дописываются в outbox_sent.txt в формате  дата время|ID|текст\n':
        '# HFPager: deferred messages. One line = one message:  recipient ID|text\n# Lines starting with # and empty lines are ignored. UTF-8. The file may be edited by hand or by another program:\n# the application re-reads it when it changes and on a QRU? request. Sent lines are removed\n# from here and appended to outbox_sent.txt as  date time|ID|text\n',
    'ПОДТВЕРЖДЕНИЕ':
        'CONFIRMATION',
    'Ответ в эфир не передан: идёт передача.':
        'Answer on air not sent: a transmission is in progress.',
    'Передача уже идёт.':
        'A transmission is already in progress.',
    'ID должен быть в диапазоне 0…65535.':
        'ID must be in the range 0…65535.',
    'Частота нулевого тона должна быть в диапазоне 300…2000 Гц.':
        'Tone 0 frequency must be in the range 300…2000 Hz.',
    'Длительность преамбулы Selcall должна быть 0.5…20 с.':
        'Selcall preamble duration must be 0.5…20 s.',
    'Приём запущен (%d Гц). HFPager: все скорости, АПЧ %s.  Selcall: %s.':
        'Reception started (%d Hz). HFPager: all speeds, AFC %s.  Selcall: %s.',
    'СООБЩЕНИЕ':
        'MESSAGE',
    'ВЫЗОВ':
        'CALL',
    'Звуковая библиотека недоступна: %s':
        'Sound library not available: %s',
    '%s  SELCALL ОТВЕТ В ЭФИР → %s':
        '%s  SELCALL ANSWER ON AIR → %s',
    '%s  %s  %d → %d  №%d  (%s Бод)%s: %s':
        '%s  %s  %d → %d  #%d  (%s Bd)%s: %s',
    'Сценарий пропущен: идёт передача.':
        'Scenario skipped: a transmission is in progress.',
    'сценарий %d «%s»':
        'scenario %d «%s»',
    '%s  ПОДТВЕРЖДЕНИЕ ОТПРАВЛЕНО  для ID %d, сообщение №%d':
        '%s  CONFIRMATION SENT  to ID %d, message #%d',
    'ID должны быть числами.':
        'IDs must be numbers.',
    'Длина текста: от 1 до 252 символов (сейчас %d).':
        'Text length: 1 to 252 characters (now %d).',
    '%s  ПЕРЕДАЧА  %d → %d  №%d  (%s Бод)%s: %s':
        '%s  TRANSMIT  %d → %d  #%d  (%s Bd)%s: %s',
    'Введите текст сообщения (до %d символов).':
        'Enter the message text (up to %d characters).',
    '%s  SELCALL ПЕРЕДАЧА  %s %s → %s%s':
        '%s  SELCALL TRANSMIT  %s %s → %s%s',
    'Не удалось открыть %s: %s':
        'Could not open %s: %s',
    'Не удалось открыть вход звуковой карты: %s':
        'Could not open the sound card input: %s',
    'Прослушивание: приём выключен.':
        'Listening: reception is off.',
    'Прослушивание эфира включено на %.0f с':
        'Listening to the air for %.0f s',
    '%s  %s       для ID %d, исходное сообщение №%d%s':
        '%s  %s       for ID %d, original message #%d%s',
    '%s  ОТЛОЖЕННОЕ ДОСТАВЛЕНО  → %d: %s':
        '%s  DEFERRED DELIVERED  → %d: %s',
    '%s  ЗАПРОС %s от ID %d: отложенных сообщений %d':
        '%s  REQUEST %s from ID %d: deferred messages %d',
    'Трансивер  ':
        'Transceiver  ',
    '%s  ТРАНСИВЕР  %s':
        '%s  TRANSCEIVER  %s',
    'Не удалось сохранить настройки: %s':
        'Could not save settings: %s',
    '%s  Журнал создан':
        '%s  Journal created',
    'Ошибка опроса звуковых устройств: %s':
        'Error listing sound devices: %s',
    'включена':
        'on',
    'выключена':
        'off',
    'выключен':
        'off',
    ' [СОМНИТЕЛЬНО]':
        ' [DOUBTFUL]',
    ' [своя передача]':
        ' [own transmission]',
    'Прослушивание: %s':
        'Listening: %s',
    'Внешнее устройство: порт %s занят PTT/CAT — выберите другой COM-порт':
        'External device: port %s is used by PTT/CAT — choose another COM port',
    'МАЯК  ':
        'BEACON  ',
    'ПРИЁМ  ':
        'RECEIVE ',
    ' [повтор]':
        ' [repeat]',
    'Не удалось прочитать %s: %s':
        'Could not read %s: %s',
    'Не удалось записать %s: %s':
        'Could not write %s: %s',
    'Отложенное сообщение для %d не отправлено: %s':
        'Deferred message for %d not sent: %s',
    'Отложенное сообщение для %d НЕ отправлено (останется в очереди): %s':
        'Deferred message for %d NOT sent (stays in the queue): %s',
    'Отложенное сообщение для %d передано, жду подтверждение до %.0f с…':
        'Deferred message for %d transmitted, waiting for confirmation up to %.0f s…',
    'Подтверждение от ID %d получено – сообщение удалено из очереди.':
        'Confirmation from ID %d received – message removed from the queue.',
    'Запрос %s от ID %d – отправляю отложенные сообщения: %d':
        'Request %s from ID %d – sending deferred messages: %d',
    'Сценарий: %s':
        'Scenario: %s',
    ' [запрос подтверждения]':
        ' [confirmation requested]',
    'PTT: %s – передача отменена':
        'PTT: %s – transmission cancelled',
    'мой ID %s, АПЧ %s':
        'my ID %s, AFC %s',
    'ОТКАЗ':
        'REFUSAL',
    'Подтверждения от ID %d нет – сообщение остаётся в очереди (будет отправлено снова при следующем запросе).':
        'No confirmation from ID %d – the message stays in the queue (it will be sent again on the next request).',
    '%s  ОТЛОЖЕННОЕ БЕЗ ПОДТВЕРЖДЕНИЯ  → %d: %s':
        '%s  DEFERRED WITHOUT CONFIRMATION  → %d: %s',
    'Запрос %s от ID %d – отложенных нет, отвечаю QRU':
        'Request %s from ID %d – nothing deferred, answering QRU',
    'Запрос %s от ID %d – отложенных сообщений для него нет':
        'Request %s from ID %d – no deferred messages for it',
    'ОШИБКА: ':
        'ERROR: ',
    'НЕ УДАЛОСЬ СНЯТЬ PTT: %s – выключите передачу вручную!':
        'COULD NOT RELEASE PTT: %s – switch the transmitter off by hand!',
    ' (доставлено: «%s»)':
        ' (delivered: «%s»)',
    'выключена, центр %.0f Гц':
        'off, centre %.0f Hz',
    'авто (где есть сигнал)':
        'auto (the one with signal)',
    '1 (левый)':
        '1 (left)',
    '2 (правый)':
        '2 (right)',
    'Сценарии: действия при получении сообщения':
        'Scenarios: actions on a received message',
    'Отложенные сообщения':
        'Deferred messages',
    'О программе':
        'About',
    'Местное (компьютер)':
        'Local (computer)',
    'Копировать':
        'Copy',
    'Выделить всё':
        'Select all',
    'Открыть журнал (TXT)':
        'Open journal (TXT)',
    'Папка журнала и отложенных…':
        'Journal and deferred messages folder…',
    'Отложенные сообщения…':
        'Deferred messages…',
    'Выход':
        'Exit',
    'Файл':
        'File',
    'Вид':
        'View',
    'Инструкция (F1)':
        'User guide (F1)',
    'Справка':
        'Help',
    'ПЕРЕГРУЗКА ВХОДА — уменьшите уровень!':
        'INPUT OVERLOAD — lower the level!',
    'HFPager (PS-18)':
        'HFPager (PS-18)',
    'Прервать':
        'Abort',
    'Отправить':
        'Send',
    'HF Selcall (CCIR 493-4, CODAN)':
        'HF Selcall (CCIR 493-4, CODAN)',
    'Сообщение':
        'Message',
    'Вызов':
        'Call',
    'Параметры HFPager':
        'HFPager settings',
    'Мой ID (0…65535):':
        'My ID (0…65535):',
    'Скорость передачи, Бод:':
        'Transmit speed, Bd:',
    'Тон 0, Гц (300…2000):':
        'Tone 0, Hz (300…2000):',
    'Порог приёма, дБ (1…20):':
        'Receive threshold, dB (1…20):',
    'Параметры Selcall':
        'Selcall settings',
    'Вызов на мой ID':
        'Call to my ID',
    'Слушать':
        'Listen',
    'Звуковой интерфейс':
        'Audio interface',
    'Управление передачей (PTT)':
        'Transmit control (PTT)',
    'Тест PTT (1 с, без звука)':
        'PTT test (1 s, no audio)',
    'Трансивер (CAT): частота, режим, сценарии':
        'Transceiver (CAT): frequency, mode, scenarios',
    'Внешнее устройство (сирена, лампа, реле) — отдельный COM-порт':
        'External device (siren, lamp, relay) — separate COM port',
    'Внешн.':
        'Ext.',
    'Папки':
        'Folders',
    'Папка журнала и отложенных сообщений':
        'Journal and deferred messages folder',
    'Журнал':
        'Journal',
    'Отправка':
        'Send',
    'Текст длиннее 252 символов: лишнее выделено красным.':
        'Text longer than 252 characters: the excess is marked red.',
    '%d/252 байт, время в эфире ≈ %.0f с, сообщение № %d':
        '%d/252 bytes, air time ≈ %.0f s, message # %d',
    '%d/%d символов%s%s.  Время в эфире: вызов ≈ %.1f с, сообщение ≈ %.1f с':
        '%d/%d characters%s%s.  Air time: call ≈ %.1f s, message ≈ %.1f s',
    'от':
        'from',
    'Звонок':
        'Ring',
    'Сигнал ответа':
        'Answer signal',
    'Внешнее устройство':
        'External device',
    'Укажите COM-порт внешнего устройства.':
        'Choose the COM port of the external device.',
    'Метод PTT = none: управлять нечем.':
        'PTT method = none: nothing to control.',
    'Тест PTT':
        'PTT test',
    'Трансивер включится на передачу примерно на 1 секунду (звука не будет). Нагрузка подключена, диапазон свободен?':
        'The transceiver will transmit for about 1 second (no audio). Is a load connected and the band free?',
    'Вкл':
        'On',
    'Текст сообщения (* = любое слово)':
        'Message text (* = any word)',
    'От ID (пусто = любой)':
        'From ID (empty = any)',
    'Действие':
        'Action',
    'Сценарии':
        'Scenarios',
    'Заменить таблицу стандартным набором сценариев?':
        'Replace the table with the standard set of scenarios?',
    'Добавить':
        'Add',
    'Заменить':
        'Replace',
    'Удалить':
        'Delete',
    'Стандартные':
        'Defaults',
    'Режим «QRU?»':
        '«QRU?» mode',
    'Кому (ID)':
        'To (ID)',
    'Текст сообщения':
        'Message text',
    'Отправить сейчас':
        'Send now',
    'Перечитать файл':
        'Re-read file',
    'Открыть TXT':
        'Open TXT',
    'Вырезать':
        'Cut',
    'Вставить':
        'Paste',
    'и':
        'and',
    'Светлая':
        'Light',
    'Тёмная':
        'Dark',
    'Внешн. ВКЛ':
        'Ext. ON',
    'Сценарий':
        'Scenario',
    'Заполните текст сообщения и действие.':
        'Fill in the message text and the action.',
    'Выберите строку таблицы.':
        'Select a table row.',
    'Сообщений в очереди: %d':
        'Messages in the queue: %d',
    'Отложенные':
        'Deferred',
    'ID получателя: число 0…65535.':
        'Recipient ID: a number 0…65535.',
    'Выберите строку.':
        'Select a row.',
    'Инструкция':
        'User guide',
    'HFPager-совместимый пейджер (PS-18) и HF Selcall CCIR 493-4 (совместимо с CODAN).':
        'HFPager-compatible pager (PS-18) and HF Selcall CCIR 493-4 (CODAN-compatible).',
    'Установите: pip install sounddevice numpy':
        'Install: pip install sounddevice numpy',
    'Передача и приём идут через выбранные звуковые устройства.':
        'Transmission and reception use the selected sound devices.',
    'Ожидание':
        'Idle',
    'Уровень входа (пик), dBFS':
        'Input level (peak), dBFS',
    'Чат':
        'Chat',
    'Только адресованные мне (фильтр ID)':
        'Only addressed to me (ID filter)',
    'Новое сообщение / вызов':
        'New message / call',
    'Очистить окно':
        'Clear window',
    'Журнал (TXT)':
        'Journal (TXT)',
    'Кому (ID):':
        'To (ID):',
    'Скорость:':
        'Speed:',
    'Запрос подтверждения':
        'Request confirmation',
    'Текст (до 252 символов; лишние выделяются красным, Enter — отправить):':
        'Text (up to 252 characters; the excess is marked red, Enter — send):',
    'Кому (Selcall ID):':
        'To (Selcall ID):',
    'Транслит':
        'Translit',
    'АПЧ':
        'AFC',
    'Автоподтверждение':
        'Auto-confirm',
    'Фильтр ID':
        'ID filter',
    'Применить':
        'Apply',
    'Отложенные сообщения (QRU?)…':
        'Deferred messages (QRU?)…',
    'Мой ID, скорость и тон 0 должны совпадать с настройками корреспондентов. Порог приёма: больше — меньше ложных срабатываний, меньше — чувствительнее. Звуковые устройства, уровень TX и PTT — на вкладке «Трансивер и аудио».':
        'My ID, speed and tone 0 must match the settings of the other stations. Receive threshold: higher — fewer false triggers, lower — more sensitive. Sound devices, TX level and PTT are on the «Transceiver & audio» tab.',
    'Приём Selcall':
        'Selcall reception',
    'Мой Selcall ID:':
        'My Selcall ID:',
    'Преамбула, с (по умолчанию 6):':
        'Preamble, s (default 6):',
    'центр без АПЧ, Гц:':
        'centre without AFC, Hz:',
    'длительность, с:':
        'duration, s:',
    'на:':
        'on:',
    'Проверить звонок':
        'Test ring',
    'Ответ в эфир (вызывающий слышит, что вызов принят; один раз, уровень TX):':
        'Answer on air (the caller hears that the call was received; once, TX level):',
    'Прослушать':
        'Preview',
    'Слушать эфир после вызова на мой ID, с:':
        'Listen to the air after a call to my ID, s:',
    'после своей передачи (ответ станции), с:':
        "after own transmission (station's reply), s:",
    'Включать внешнее устройство (настройка — на вкладке «Трансивер и аудио»)':
        'Switch the external device on (set up on the «Transceiver & audio» tab)',
    'Selcall передаётся через тот же выход, с тем же уровнем TX и тем же PTT/CAT. Частоты: 1700/1870 Гц (центр 1785 Гц, USB). Звонок и прослушивание идут на выбранное устройство (например, динамики компьютера).':
        "Selcall is transmitted through the same output, with the same TX level and the same PTT/CAT. Tones: 1700/1870 Hz (centre 1785 Hz, USB). The ring and listening go to the selected device (e.g. the computer's speakers).",
    'Трансивер и аудио':
        'Transceiver & audio',
    'Вход (приём):':
        'Input (receive):',
    'канал:':
        'channel:',
    'Выход (передача):':
        'Output (transmit):',
    'Уровень TX:':
        'TX level:',
    'Задержка PTT/VOX, с:':
        'PTT/VOX delay, s:',
    'Обновить список':
        'Refresh list',
    'Перегрузка входа: отсчёты достигают 98 % полной шкалы (−0,2 dBFS). Держите пики сигнала в зелёной зоне (ниже −12 dBFS), жёлтая −12…−3, красная выше −3 dBFS.':
        'Input overload: samples reach 98 % of full scale (−0.2 dBFS). Keep signal peaks in the green zone (below −12 dBFS); yellow −12…−3, red above −3 dBFS.',
    'Метод:':
        'Method:',
    'COM-порт:':
        'COM port:',
    'Инверсия (линия)':
        'Invert (line)',
    'ICOM модель:':
        'ICOM model:',
    'CI-V адрес (hex):':
        'CI-V address (hex):',
    'KENWOOD команда:':
        'KENWOOD command:',
    'RTS/DTR: «1» на линии COM-порта на время передачи. YAESU: TX1;/TX0;  YAESU-OLD: 5-байтовый CAT (FT-817/857/897)  KENWOOD/ELECRAFT: TX;/RX;  ICOM: CI-V 1C 00. «Выключено» в списке портов — порт не используется. Сначала проверяйте на эквиваленте нагрузки.':
        'RTS/DTR: «1» on a COM port line while transmitting. YAESU: TX1;/TX0;  YAESU-OLD: 5-byte CAT (FT-817/857/897)  KENWOOD/ELECRAFT: TX;/RX;  ICOM: CI-V 1C 00. «Off» in the port list — the port is not used. Test into a dummy load first.',
    'Протокол:':
        'Protocol:',
    'Как в PTT':
        'Same as PTT',
    'Частота, МГц:':
        'Frequency, MHz:',
    'Режим:':
        'Mode:',
    'Установить':
        'Set',
    'Только режим':
        'Mode only',
    'Прочитать частоту':
        'Read frequency',
    'Диапазон, м:':
        'Band, m:',
    'Шаг, кГц:':
        'Step, kHz:',
    'Сценарии…':
        'Scenarios…',
    'линия:':
        'line:',
    'инверсия':
        'invert',
    'время, с (1–60):':
        'time, s (1–60):',
    'Импульс':
        'Pulse',
    'Порт PTT и порт CAT для внешнего устройства не используются. Если на компьютере один COM-порт и он нужен для PTT — выберите здесь «Выключено».':
        'The PTT port and the CAT port are not used for the external device. If the computer has a single COM port and it is needed for PTT, choose «Off» here.',
    'Программа':
        'Program',
    'Язык интерфейса:':
        'Interface language:',
    'Вторые часы (первые — UTC):':
        'Second clock (the first is UTC):',
    'Журнал и отложенные сообщения:':
        'Journal and deferred messages:',
    'Выбрать…':
        'Choose…',
    'По умолчанию':
        'Default',
    'Настройки программы:':
        'Program settings:',
    'Файл отложенных сообщений можно задать отдельно в окне «Отложенные сообщения».':
        'The deferred-messages file can be set separately in the «Deferred messages» window.',
    'Журнал: %s':
        'Journal: %s',
    ' (лишнее не будет передано)':
        ' (the excess will not be sent)',
    'Сбросить':
        'Dismiss',
    'Ответить':
        'Answer',
    'Слушаю ■':
        'Listening ■',
    'Слушаю…':
        'Listening…',
    'Выполнять сценарии при получении сообщений, адресованных моему ID':
        'Run scenarios on messages addressed to my ID',
    'Сообщение:':
        'Message:',
    'От ID:':
        'From ID:',
    'Действие:':
        'Action:',
    'Проверка (имитация сообщения):':
        'Test (simulated message):',
    'Выполнить':
        'Run',
    'При получении запроса от ID отправлять ему его отложенные сообщения':
        'On a request from an ID send it its deferred messages',
    'Текст запроса:':
        'Request text:',
    'Ждать подтверждение, с:':
        'Wait for confirmation, s:',
    'Если для него ничего нет — отвечать «QRU»':
        'If there is nothing for it — answer «QRU»',
    'TXT-файл:':
        'TXT file:',
    'Длина текста: 1…252 байта (сейчас %d).':
        'Text length: 1…252 bytes (now %d).',
    'Текст:':
        'Text:',
    'Формат файла (UTF-8): одна строка = одно сообщение,  ID|текст.  Сообщение удаляется из очереди только после подтверждения доставки. Строки с # игнорируются. Файл перечитывается при изменении; отправленные строки переносятся в outbox_sent.txt.':
        'File format (UTF-8): one line = one message,  ID|text.  A message leaves the queue only after a delivery confirmation. Lines starting with # are ignored. The file is re-read when it changes; sent lines move to outbox_sent.txt.',
    'Настройки: %s':
        'Settings: %s',
    'Последний кадр: центр %.0f Гц, диапазон АПЧ %.1f Гц':
        'Last frame: centre %.0f Hz, AFC range %.1f Hz',
    'Библиотека sounddevice/PortAudio недоступна:':
        'sounddevice/PortAudio library not available:',
    'Текст сообщения (до %d символов после транслита; для вызова не нужен):':
        'Message text (up to %d characters after transliteration; not needed for a call):',
    'Звонок:':
        'Ring:',
    '%s МГц':
        '%s MHz',
    'нет подходящего сценария':
        'no matching scenario',
    '.  Передатчик сценарии не включают. Выполняется только первый подходящий сценарий (порядок сверху вниз); для защиты укажите «От ID». Связь с трансивером — на вкладке «Трансивер и аудио».':
        '.  Scenarios never key the transmitter. Only the first matching scenario runs (top to bottom); for protection set «From ID». The transceiver connection is on the «Transceiver & audio» tab.',
    'Не удалось открыть файл: %s':
        'Could not open the file: %s',
    'панель':
        'panel',
    'ошибка: %s':
        'error: %s',
    'выполнено: ':
        'done: ',
    'Действия (через «;»): BND <м> · FRQ <МГц> [режим] · MODE <режим> · UP/DOWN <кГц> · WAIT <с>.  Параметры из сообщения: {1}, {2}…  Режимы: ':
        'Actions (separated by «;»): BND <m> · FRQ <MHz> [mode] · MODE <mode> · UP/DOWN <kHz> · WAIT <s>.  Parameters from the message: {1}, {2}…  Modes: ',
    '[%s] %d → %d  №%d  (%s Бод, АПЧ %.0f Гц): %s%s':
        '[%s] %d → %d  #%d  (%s Bd, AFC %.0f Hz): %s%s',
    'Маяк от':
        'Beacon from',
    'Бод':
        'Bd',
    '[%s] ✔ %s: сообщение №%d для %d доставлено («%s»)':
        '[%s] ✔ %s: message #%d to %d delivered («%s»)',
    '[%s] ✔ %s для ID %d (исходное сообщение №%d, CRC %04X)':
        '[%s] ✔ %s for ID %d (original message #%d, CRC %04X)',
    '   (повтор)':
        '   (repeat)',
    'запрошено подтверждение доставки – отправляю':
        'delivery confirmation requested – sending',
    'запрошено подтверждение доставки (автоподтверждение выключено)':
        'delivery confirmation requested (auto-confirm is off)',
    'Ошибка интерфейса:':
        'Interface error:',
    'Передача…':
        'Transmitting…',
    'Тест PTT:':
        'PTT test:',
    '[%s] ✔ → %d  подтверждение сообщения №%d  (%s Бод, ≈ %.0f с)':
        '[%s] ✔ → %d  confirmation of message #%d  (%s Bd, ≈ %.0f s)',
    'выполнен (включено и выключено)':
        'done (keyed and released)',
    'Гц':
        'Hz',
    '[своя передача]':
        '[own transmission]',
    'Ответ в эфир…':
        'Answer on air…',
    'СОМНИТЕЛЬНО':
        'DOUBTFUL',
    '[%s] SELCALL ОТВЕТ В ЭФИР → %s   (≈ %.1f с)':
        '[%s] SELCALL ANSWER ON AIR → %s   (≈ %.1f s)',
    'Передача Selcall…':
        'Selcall transmitting…',
    'Selcall АПЧ: ':
        'Selcall AFC: ',
    '[%s] SELCALL %s %s → %s%s   (передача ≈ %.0f с)':
        '[%s] SELCALL %s %s → %s%s   (transmission ≈ %.0f s)',
    '[%s] %d → %d  №%d  (%s Бод, передача ≈ %.0f с): %s':
        '[%s] %d → %d  #%d  (%s Bd, transmission ≈ %.0f s): %s',
    'Вход не отдаёт звук %.0f с — приём перезапущен':
        'The input gives no audio for %.0f s — reception restarted',
    'Вход не отдаёт звук %.0f с — перезапустить приём не удалось':
        'The input gives no audio for %.0f s — could not restart reception',
    'Ошибка передачи:':
        'Transmission error:',
    'Приём сигнала…':
        'Receiving signal…',
    'Декодирование…':
        'Decoding…',
    'Внутренняя ошибка:':
        'Internal error:',
    'Принят сигнал (%.0f с), но кадр HFPager не удалось декодировать (слишком слабый или искажён)':
        'A signal was received (%.0f s) but the HFPager frame could not be decoded (too weak or distorted)',
    'Укажите цифровые Selcall ID: свой и получателя (4 или 6 цифр).':
        "Enter numeric Selcall IDs: your own and the recipient's (4 or 6 digits).",
    'Selcall ID: не больше 10 цифр (обычно 4 или 6).':
        'Selcall ID: at most 10 digits (usually 4 or 6).',
    'звуковая библиотека недоступна':
        'sound library not available',
    'pyserial недоступен':
        'pyserial not available',
    'не выбран COM-порт внешнего устройства':
        'no COM port selected for the external device',
    'Внешнее устройство: %s':
        'External device: %s',
    'Ошибка декодера Selcall: %s':
        'Selcall decoder error: %s',
    'Двухтональный':
        'Two-tone',
    'Трель':
        'Trill',
    'Короткие гудки':
        'Short beeps',
    'Мелодия «Калинка»':
        '«Kalinka» melody',
    'Выключено':
        'Off',
    'системный выход':
        'system output',
    'Подтверждение':
        'Confirmation',
    'Чат и сообщения':
        'Chat & messages',
    '%d/252 байт · в эфире ≈ %.0f с · № %d':
        '%d/252 bytes · air time ≈ %.0f s · # %d',
    '%d/%d симв.%s%s · в эфире: вызов ≈ %.1f с, сообщение ≈ %.1f с':
        '%d/%d chars%s%s · air time: call ≈ %.1f s, message ≈ %.1f s',
    'CW: нет передаваемых символов.':
        'CW: no characters to send.',
    '%s  %s ОТВЕТ В ЭФИР → %s':
        '%s  %s ANSWER ON AIR → %s',
    '%s  CW: %s':
        '%s  CW: %s',
    'Запрос %s от ID %d — отвечаю мелодией в эфир':
        'Request %s from ID %d — answering with a melody on air',
    'Маяк: %s':
        'Beacon: %s',
    'передан':
        'sent',
    'Маяк: ошибка %s':
        'Beacon: error %s',
    'Вызов и сообщения на мой ID':
        'Calls and messages to my ID',
    'Маяк':
        'Beacon',
    'Макросы (кнопки под чатом)':
        'Macros (buttons under the chat)',
    'следующий маяк через %d:%02d (в %s UTC)':
        'next beacon in %d:%02d (at %s UTC)',
    'оба':
        'both',
    'Протокол':
        'Protocol',
    'От ID HFPager':
        'From HFPager ID',
    'От Selcall ID':
        'From Selcall ID',
    '№':
        '#',
    'Подпись кнопки':
        'Button caption',
    'Что':
        'What',
    'Кому (пусто — из поля)':
        'To (empty = from the field)',
    'Текст':
        'Text',
    'Сразу':
        'At once',
    'маяк выключен':
        'beacon is off',
    'Макросы…':
        'Macros…',
    'Текст вызова (кнопка «Вызов»):':
        'Call text («Call» button):',
    'Звонок при вызове':
        'Ring on a call',
    'Звук входящего сообщения':
        'Incoming message sound',
    'Ответ в эфир на вызов (один раз, уровень TX):':
        'Answer a call on air (once, TX level):',
    'Слушать эфир после вызова, с:':
        'Listen to the air after a call, s:',
    'Включать внешнее устройство при вызове':
        'Switch the external device on at a call',
    'Отвечать мелодией в эфир на сообщение':
        'Answer with a melody on air to the message',
    '(на мой ID или всем, ID 0):':
        '(to my ID or to all, ID 0):',
    'Мой ID, скорость и тон 0 должны совпадать с настройками корреспондентов. Порог приёма: больше — меньше ложных срабатываний, меньше — чувствительнее. Звуковые устройства, уровень TX, PTT, устройство звонка и внешнее устройство — на вкладке «Трансивер и аудио». Ответ в эфир и ответ на BCN REQ — автоматическая передача.':
        'My ID, speed and tone 0 must match the settings of the other stations. Receive threshold: higher — fewer false triggers, lower — more sensitive. Sound devices, TX level, PTT, the ring device and the external device are on the «Transceiver & audio» tab. The answer on air and the BCN REQ answer are automatic transmissions.',
    'Звонок и прослушивание:':
        'Ring and listening:',
    'Маяк и макросы':
        'Beacon & macros',
    'Маяк включён':
        'Beacon on',
    'каждые, мин:':
        'every, min:',
    'в заданное время UTC (ЧЧ:ММ через пробел):':
        'at UTC times (HH:MM separated by spaces):',
    'Что передавать:':
        'What to send:',
    'кому (ID):':
        'to (ID):',
    'CW: скорость, WPM:':
        'CW: speed, WPM:',
    'тон, Гц:':
        'tone, Hz:',
    'Текст маяка:':
        'Beacon text:',
    'Передать маяк сейчас':
        'Send beacon now',
    'Маяк не начинает передачу, пока идёт приём сигнала или своя передача — ждёт. «HFPager: кадр маяк» — как маяк приложения HFPager (тип 0x06, всем). Пустой текст: «Beacon from <мой ID>». Selcall: вызов или сообщение на ID «кому». CW — текст телеграфом (латиница, цифры, русские буквы).':
        'The beacon does not start while a signal is being received or we are transmitting — it waits. «HFPager: beacon frame» is like the HFPager app beacon (type 0x06, to all). Empty text: «Beacon from <my ID>». Selcall: a call or a message to the «to» ID. CW — the text in Morse (Latin, digits, Russian letters).',
    'Сохранить макросы':
        'Save macros',
    'Кнопка показывается, если у макроса есть подпись. «Сразу» — нажатие сразу передаёт; без галочки — только заполняет поля под чатом.':
        'A button is shown when the macro has a caption. «At once» — a click transmits immediately; without it the click only fills the fields under the chat.',
    'Выполнять сценарии при получении сообщений на мой ID (HFPager — мой ID, Selcall — мой Selcall ID, сообщение с текстом)':
        'Run scenarios on messages to my ID (HFPager — my ID, Selcall — my Selcall ID, a message call with text)',
    'От Selcall ID:':
        'From Selcall ID:',
    '[%s] %s ОТВЕТ В ЭФИР → %s   (≈ %.1f с)':
        '[%s] %s ANSWER ON AIR → %s   (≈ %.1f s)',
    'Передача CW…':
        'Transmitting CW…',
    '[%s] CW: %s   (передача ≈ %.0f с)':
        '[%s] CW: %s   (transmission ≈ %.0f s)',
    'HFPager: кадр «маяк»':
        'HFPager: beacon frame',
    'HFPager: сообщение':
        'HFPager: message',
    'HFPager: вызов (CALL)':
        'HFPager: call (CALL)',
    'Selcall: вызов':
        'Selcall: call',
    'Selcall: сообщение':
        'Selcall: message',
    'CW (телеграф)':
        'CW (Morse)',
    '(только на мой ID):':
        '(to my ID only):',
    'Для сканирования отметьте от 2 до 6 каналов с частотой.':
        'For scanning, tick 2 to 6 channels with a frequency.',
    'Не выбран COM-порт CAT трансивера (вкладка «Трансивер и аудио»).':
        'No CAT COM port of the transceiver selected («Transceiver & audio» tab).',
    'Сканирование: %d каналов, цикл %.0f с':
        'Scanning: %d channels, cycle %.0f s',
    'Сканирование остановлено: меньше 2 каналов.':
        'Scanning stopped: fewer than 2 channels.',
    'Сканирование: ошибка %s':
        'Scanning: error %s',
    'Сканирование остановлено: ошибка CAT: %s':
        'Scanning stopped: CAT error: %s',
    '%s  СКАНИРОВАНИЕ: остановка на канале %d (%s %s)':
        '%s  SCAN: stopped on channel %d (%s %s)',
    'СТОП на канале':
        'STOP on channel',
    'скан':
        'scan',
    'Преамбула при передаче, с (0 = стандартная):':
        'Transmit preamble, s (0 = standard):',
    'Сканирование каналов (через CAT)':
        'Channel scanning (via CAT)',
    'Начать сканирование':
        'Start scanning',
    'Сканирование':
        'Scanning',
    'Отметьте в таблице сканирования хотя бы 2 канала.':
        'Tick at least 2 channels in the scan table.',
    'Частота, МГц':
        'Frequency, MHz',
    'Режим':
        'Mode',
    'Задержка на канале, с':
        'Dwell on channel, s',
    'стандартная на %s Бод: %.1f с; будет %.1f с':
        'standard at %s Bd: %.1f s; will be %.1f s',
    'Для сканирования':
        'For scanning',
    'Возобновить сканирование после тишины, с:':
        'Resume scanning after silence, s:',
    'Подобрать преамбулу и точки':
        'Fit preamble and dots',
    'Отметьте от 2 до 6 каналов. Программа перестраивает трансивер по кругу; если на канале начинается приём (преамбула HFPager или точки Selcall) или идёт передача, сканирование останавливается на этом канале и возобновляется после заданного времени тишины. Чтобы сканирующая станция успела остановиться, вызывающая должна передавать преамбулу (HFPager) и точки (Selcall) не короче цикла сканирования + 3 с — кнопка «Подобрать» считает это значение по таблице.':
        'Tick 2 to 6 channels. The program retunes the transceiver in a circle; when reception starts on a channel (HFPager preamble or Selcall dots) or we transmit, scanning stops on that channel and resumes after the set time of silence. For a scanning station to stop in time, the calling station must send a preamble (HFPager) and dots (Selcall) at least as long as the scan cycle + 3 s — the «Fit» button computes this from the table.',
    'Остановить сканирование':
        'Stop scanning',
    'Преамбула HFPager %.1f с, точки Selcall %.1f с (цикл сканирования %.0f с + 3 с)':
        'HFPager preamble %.1f s, Selcall dots %.1f s (scan cycle %.0f s + 3 s)',
    'Цикл сканирования %.1f с: преамбула HFPager %.1f с (цикл + 2,5 с), точки Selcall %.1f с (цикл + 1 с, не меньше 6 с)':
        'Scan cycle %.1f s: HFPager preamble %.1f s (cycle + 2.5 s), Selcall dots %.1f s (cycle + 1 s, at least 6 s)',
    'Отметьте от 2 до 6 каналов. Программа перестраивает трансивер по кругу; если на канале начинается приём (преамбула HFPager или точки Selcall) или идёт передача, сканирование останавливается на этом канале и возобновляется после заданного времени тишины. Задержка на канале: сигнал обнаруживается через 0,3 с после перехода, поэтому хватает 1–1,5 с (если трансивер быстро перестраивается). Вызывающая станция должна передавать преамбулу HFPager не короче цикла сканирования + 2,5 с (приёмнику нужно услышать ~2 с преамбулы) и точки Selcall не короче цикла + 1 с — кнопка «Подобрать» считает это по таблице.':
        'Tick 2 to 6 channels. The program retunes the transceiver in a circle; when reception starts on a channel (HFPager preamble or Selcall dots) or we transmit, scanning stops on that channel and resumes after the set time of silence. Dwell: a signal is detected 0.3 s after landing, so 1–1.5 s is enough (if the transceiver retunes quickly). The calling station must send an HFPager preamble at least as long as the scan cycle + 2.5 s (the receiver needs to hear ~2 s of preamble) and Selcall dots at least cycle + 1 s — the «Fit» button computes this from the table.',
    'СКАН':
        'SCAN',
    'ВКЛ':
        'ON',
    'ВЫКЛ':
        'OFF',
    'Декодер HFPager включён':
        'HFPager decoder on',
    'Декодер HFPager выключен':
        'HFPager decoder off',
    'Декодер Selcall включён':
        'Selcall decoder on',
    'Декодер Selcall выключен':
        'Selcall decoder off',
    'Отмечено каналов: %d (нужно от 2 до 6)':
        'Channels ticked: %d (2 to 6 needed)',
    'Каналов %d, цикл %.1f с, перестройка %.2f с%s. Вызывающему нужно: преамбула HFPager ≥ %.1f с, точки Selcall ≥ %.1f с. Стандартных 6 с точек CODAN хватает на %d кан.':
        'Channels %d, cycle %.1f s, retune %.2f s%s. The caller needs: HFPager preamble ≥ %.1f s, Selcall dots ≥ %.1f s. The standard 6 s CODAN dots cover %d channels.',
    ' (оценка, измерится при сканировании)':
        ' (estimate, measured while scanning)',
    'Сканирование %d каналов: преамбула HFPager %.1f с, точки Selcall %.1f с (обход остальных каналов + 2,3 с / + 0,6 с)':
        'Scanning %d channels: HFPager preamble %.1f s, Selcall dots %.1f s (round over the other channels + 2.3 s / + 0.6 s)',
    'Отметьте от 2 до 6 каналов. Программа перестраивает трансивер по кругу; если на канале начинается приём (преамбула HFPager или точки Selcall) или идёт передача, сканирование останавливается на этом канале и возобновляется после заданного времени тишины. Сигнал обнаруживается через 0,3 с после перехода, поэтому хватает задержки 1 с на канал. Худший случай — вызов начался сразу после ухода с канала: сканер вернётся через обход остальных каналов, (N − 1) × (задержка + перестройка). Поэтому вызывающая станция должна передавать точки Selcall не короче этого времени + 0,6 с, а преамбулу HFPager — + 2,3 с (приёмнику нужно услышать ~2 с преамбулы). Время перестройки сканер измеряет сам. Кнопка «Подобрать» считает длины по таблице. Кнопка «СКАН» есть и на главной странице.':
        'Tick 2 to 6 channels. The program retunes the transceiver in a circle; when reception starts on a channel (HFPager preamble or Selcall dots) or we transmit, scanning stops on that channel and resumes after the set time of silence. A signal is detected 0.3 s after landing, so a dwell of 1 s per channel is enough. Worst case — the call starts just after the scanner left the channel: it comes back after the round over the other channels, (N − 1) × (dwell + retune). So the calling station must send Selcall dots at least that long + 0.6 s, and an HFPager preamble + 2.3 s (the receiver needs to hear ~2 s of preamble). The scanner measures the retune time itself. The «Fit» button computes the lengths from the table. The «SCAN» button is also on the main page.',
    'Сканирование: исходная частота %s МГц':
        'Scanning: starting frequency %s MHz',
    'Сканирование: не удалось прочитать частоту трансивера (%s) — после остановки он останется на последнем канале':
        'Scanning: could not read the transceiver frequency (%s) — after stopping it stays on the last channel',
    'Сканирование остановлено, трансивер возвращён на %s МГц':
        'Scanning stopped, transceiver returned to %s MHz',
    'Сканирование остановлено; вернуть частоту не удалось: %s':
        'Scanning stopped; could not restore the frequency: %s',
    'Скан':
        'Scan',
    'Канал':
        'Channel',
    'Подпись кнопки канала %d (%s %s):':
        'Caption of the channel %d button (%s %s):',
    'У канала %d не задана частота (таблица каналов на вкладке «Трансивер и аудио»).':
        'Channel %d has no frequency (channel table on the «Transceiver & audio» tab).',
    'канал %d «%s»':
        'channel %d «%s»',
    'Декодеры':
        'Decoders',
    'Автоподтверждение для ID %d не отправлено: передатчик занят.':
        'Auto-acknowledgement for ID %d not sent: the transmitter is busy.',
    'Автоподтверждение для ID %d не отправлено: %s':
        'Auto-acknowledgement for ID %d not sent: %s',
    'у канала %d не задана частота':
        'channel %d has no frequency',
    'Маяк при сканировании: %s.':
        'Beacon while scanning: %s.',
    'Маяк: сканер перейдёт на канал %d и передаст его':
        'Beacon: the scanner will go to channel %d and send it',
    '%s  СКАНИРОВАНИЕ: маяк на канале %d (%s %s)':
        '%s  SCANNING: beacon on channel %d (%s %s)',
    'Маяк (канал %d): %s':
        'Beacon (channel %d): %s',
    'Маяк при сканировании не передан: %s.':
        'Beacon while scanning not sent: %s.',
    'При сканировании маяк передаётся на канале:':
        'While scanning, the beacon goes out on channel:',
    'При сканировании маяк всегда идёт на одном канале: в нужное время сканер переходит на него, передаёт маяк, ждёт заданное время тишины и продолжает обход. Если сканер стоит на канале из-за приёма, маяк ждёт конца связи.':
        'While scanning, the beacon always goes out on one channel: when it is due, the scanner goes there, sends the beacon, waits the set time of silence and goes on scanning. If the scanner is holding on a channel because of reception, the beacon waits for the contact to end.',
    'Передача: %s — повторяю':
        'Transmission: %s — retrying',
    'Запрос %s от ID %d с запросом подтверждения — отвечаю подтверждением':
        '%s request from ID %d with an acknowledgement request — answering with the acknowledgement',
    'Пока нажата':
        'While pressed',
    'Нажал — вкл., ещё раз — выкл.':
        'Press on, press again off',
    'Горячая клавиша':
        'Hot key',
    'Микрофон и настройки…':
        'Microphone and settings…',
    'Микрофон и PTT (голосовая передача)':
        'Microphone and PTT (voice transmission)',
    'Режим: ':
        'Mode: ',
    'Микрофон:':
        'Microphone:',
    'Усиление, дБ:':
        'Gain, dB:',
    'Режим PTT:':
        'PTT mode:',
    'Горячая клавиша:':
        'Hot key:',
    'Ограничение, с:':
        'Time limit, s:',
    'Слушать эфир после передачи голосом, с:':
        'Listen to the air after a voice transmission, s:',
    'Кнопка PTT на главной странице (и горячая клавиша) включает передачу: звук микрофона идёт на «Выход (передача)», трансивер переключается методом PTT ниже. Если микрофон «Выключено», PTT только включает передачу трансивера (говорите в его микрофон). Ограничение — наибольшая длительность одной передачи (0 — без ограничения).':
        'The PTT button on the main page (and the hot key) starts a transmission: the microphone sound goes to «Output (TX)», the transceiver is keyed by the PTT method below. With the microphone «Off», PTT only keys the transceiver (speak into its own microphone). The time limit is the longest single transmission (0 — no limit).',
    'Передача голосом (PTT)…':
        'Voice transmission (PTT)…',
    'Нет ни микрофона, ни управления PTT: выберите их на вкладке «Трансивер и аудио».':
        'Neither a microphone nor PTT control: choose them on the «Transceiver & audio» tab.',
    'Микрофон и выход передачи не работают на общей частоте дискретизации':
        'The microphone and the TX output have no common sample rate',
    'Передача голосом остановлена: превышено ограничение %.0f с':
        'Voice transmission stopped: the %.0f s limit was reached',
    '%s  ГОЛОС: передача %.0f с%s':
        '%s  VOICE: transmission %.0f s%s',
}
