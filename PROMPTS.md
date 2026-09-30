# Продающие промты для Reels / Клипов / Telegram — поделки ручной работы

Фото лежат в `assets/`:

| Поделка | Файлы |
|---|---|
| Робот-дачник | `robot_1.jpg` (крупно), `robot_2.jpg` (с лилиями) |
| Новогоднее колесо обозрения | `wheel_1.jpg` (днём), `wheel_2.jpg` (вечером, горит гирлянда) |
| Панно «С Днём Рождения!» | `birthday_board.jpg` |

---

## 0. Как пользоваться

1. **Видео из фото (image-to-video):** Kling, Runway, Hailuo, Veo, Sora и т.п.
   Загружаете фото как **первый кадр**, вставляете английский `VIDEO PROMPT` и `NEGATIVE PROMPT`.
   Формат **9:16**, длина одного клипа — **5 сек** (или 10 сек, где сервис позволяет).
2. **Склейка:** 2–3 сгенерированных клипа + финальный кадр-фото собираете в CapCut / InShot / VK Клипы.
3. **Текст на экране добавляйте в монтажке, а не в нейросети** — нейросети портят русские буквы.
4. **Музыку** берите из библиотеки Instagram / VK (тогда нет блокировок) по ключевым словам ниже
   или сгенерируйте свою в Suno / Udio по готовому промту.
5. Поделку нейросеть **не должна перерисовывать** — поэтому в каждом промте есть жёсткое требование
   «сохранить предмет как на фото». Если форма «поплыла» — перегенерируйте, покупатель должен получить
   именно то, что видел.

### Технические требования (для всех трёх площадок)

- 1080×1920, 9:16, 30 fps, 12–15 сек (досматривают до конца → алгоритм продвигает).
- **Безопасные зоны:** не ставить текст в верхние ~250 px и нижние ~350 px (там интерфейс Instagram/VK),
  и в правые ~150 px (кнопки лайков).
- Крупный шрифт (≥ 60 px), максимум 5–6 слов на экране, каждая надпись висит ≥ 1,5 сек.
- Первый кадр — самый яркий крупный план (это обложка и хук).
- Смена кадра — на сильную долю музыки.

---

## 1. Универсальная продающая структура (15 сек)

| Время | Задача | Что в кадре | Текст на экране |
|---|---|---|---|
| 0–2 с | **Хук** — остановить скролл | Самая яркая деталь крупно, резкий наезд | Вопрос или «вау»-фраза |
| 2–6 с | **Показать ручную работу** | Проезд по деталям | «Ручная работа», «каждая деталь — вручную» |
| 6–10 с | **Польза / кому подойдёт** | Предмет в интерьере, общий план | Повод + для кого |
| 10–15 с | **Призыв (CTA)** | Предмет целиком, красивый финал | Цена / «на заказ» / «пиши в директ» |

### Мастер-промт (шаблон, если нужно для новой поделки)

```
VIDEO PROMPT:
Vertical 9:16 product reel of a handmade craft: [ОПИСАНИЕ ПРЕДМЕТА ПО-АНГЛИЙСКИ].
Keep the object EXACTLY as in the reference photo: same shape, colors, materials, every detail in place.
Shot 1: extreme close-up of [самая яркая деталь], fast smooth push-in.
Shot 2: slow macro slide across [детали 2–3], shallow depth of field, soft bokeh.
Shot 3: camera pulls back to reveal the whole object in a cozy home interior, [свет/настроение].
Lighting: soft natural light, warm tones, high detail, crisp textures, cinematic, commercial product video.
Subtle ambient motion only (light flicker, gentle bokeh, slight parallax). Static object, camera moves.

NEGATIVE PROMPT:
changing the object, morphing, melting, extra parts, missing parts, deformed shape, text, letters,
watermark, logo, people, hands, blurry, low quality, flicker, distorted proportions, cartoon style
```

---

## 2. Робот-дачник 🤖🌱

**Кому продаём:** подарок дачнику, папе/дедушке, на новоселье на даче, садовый декор, подарок учителю технологии.
**Главная фишка:** сделан из «железок» — настоящие манометр, часы, спидометр, термометр, шланги-руки, лопатка и грабли.

### Сценарий

| Время | Кадр (фото) | Текст на экране |
|---|---|---|
| 0–2 с | Лицо робота крупно, наезд на глаза (`robot_1`) | **«Знакомьтесь — робот-дачник!»** |
| 2–5 с | Проезд по панели: часы → спидометр → манометр | **«Собран вручную из настоящих деталей»** |
| 5–8 с | Рука-шланг с лопаткой и граблями | **«Сам сажает, сам поливает, сам удобряет»** |
| 8–11 с | Общий план с лилиями (`robot_2`) | **«Лучший подарок для дачника 🌿»** |
| 11–15 с | Робот целиком, лёгкий «кивок» камеры | **«Сделаю такого же — пишите!»** + цена |

### VIDEO PROMPT (для `robot_1.jpg`)

```
Vertical 9:16 product reel of a handmade robot sculpture standing on a white windowsill in front of
green summer trees. The robot has a square silver foil-textured head with big googly cartoon eyes,
a black ring nose and a red smile, two wire antennae; a silver box body decorated with a real
analog wall clock, a car speedometer, a pressure gauge, a small thermometer, yellow gear pieces,
silver pinwheels; flexible metal corrugated hose arms holding a blue toy shovel and red toy rake;
legs made of metal cans.
Keep the robot EXACTLY as in the reference photo: same shape, same details, same colors.
Shot 1: fast smooth push-in onto the robot's big eyes, playful.
Shot 2: slow macro slide across the clock, speedometer and pressure gauge, metallic foil glitter,
shallow depth of field.
Shot 3: camera arcs slightly to the toy shovel and rake in the robot's hand, then pulls back to show
the whole robot on a sunny windowsill with leaves gently swaying outside.
Bright summer daylight, sun glints on the silver foil, cheerful, crisp detail, commercial product video.
Only subtle motion: leaves moving outside, light sparkling on foil, clock second hand ticking.
```

### NEGATIVE PROMPT

```
robot moving, robot walking, changing the robot, morphing, melting, extra arms, extra eyes,
missing gauges, deformed face, text, letters, watermark, people, hands, blurry, flicker,
cartoon render, CGI look
```

### 🎵 Музыка

- **Настроение:** весёлое, «механическое», дачно-солнечное. 110–125 BPM.
- **Поиск в библиотеке IG/VK:** `happy ukulele`, `whistle happy`, `funny robot`, `quirky`, `chiptune happy`, `summer garden`.
- **Suno/Udio промт:**
  ```
  cheerful quirky instrumental, ukulele and whistling melody, playful 8-bit robot bleeps, light claps,
  sunny summer garden vibe, 118 bpm, catchy hook in first 2 seconds, no vocals, 15 seconds
  ```
- Звуковые акценты: «бип-буп» на хуке, тиканье часов на кадре с панелью.

---

## 3. Новогоднее колесо обозрения 🎡✨

**Кому продаём:** новогодний декор, подарок коллегам/учителю/воспитателю, поделка на конкурс в садик/школу.
**Главная фишка:** светится! Золотое колесо из деревянных палочек, помпоны, гирлянда, мишура, ёлочка и машинка с ёлкой.

### Сценарий

| Время | Кадр (фото) | Текст на экране |
|---|---|---|
| 0–2 с | Вечернее фото (`wheel_2`), огоньки мерцают, наезд | **«Включаем новогоднее настроение ✨»** |
| 2–5 с | Дневное фото (`wheel_1`): спицы, помпоны, золото | **«Колесо обозрения ручной работы»** |
| 5–8 с | Макро: машинка с ёлочкой, подарки, мишура | **«Каждая деталь — вручную»** |
| 8–11 с | Снова вечернее фото, общий план | **«Украсит дом, садик или офис»** |
| 11–15 с | Огоньки ярче, «снег» сверху | **«Успейте заказать до Нового года 🎄»** + цена |

### VIDEO PROMPT (для `wheel_2.jpg` — вечер)

```
Vertical 9:16 product reel of a handmade Ferris wheel Christmas decoration on a windowsill at evening.
The wheel is made of popsicle sticks painted gold, with colorful glitter pompoms on every tip, green
pipe-cleaner wraps, and a warm fairy-light garland woven through it. The base is covered in gold and
silver tinsel with small Christmas ornaments, tiny gift boxes, a small red car carrying a Christmas
tree, and a green cone Christmas tree with a golden bow.
Keep the object EXACTLY as in the reference photo: same shape, same colors, same details.
Shot 1: slow push-in, the fairy lights twinkle and softly glow, warm golden bokeh.
Shot 2: gentle camera orbit (max 15 degrees) around the wheel, tinsel sparkles.
Shot 3: macro on the red car with the tree and the gift boxes, then pull back to the whole wheel;
soft snowflakes drift outside the window.
Cozy magical Christmas atmosphere, warm light, festive, high detail, cinematic commercial.
Only subtle motion: twinkling lights, sparkling tinsel, falling snow outside.
```

> Для дневного фото `wheel_1.jpg` — тот же промт, но замените `at evening` на `in soft daylight`
> и уберите `fairy lights twinkle` → `golden paint gently glints`.

### NEGATIVE PROMPT

```
changing the wheel, morphing, broken sticks, extra spokes, missing pompoms, melting, wheel spinning fast,
text, letters, watermark, people, hands, blurry, harsh light, flicker, plastic CGI look
```

### 🎵 Музыка

- **Настроение:** волшебное, уютное, «зимняя сказка». 90–120 BPM.
- **Поиск в библиотеке IG/VK:** `christmas magic`, `jingle bells instrumental`, `sleigh bells`, `winter wonderland`, `новогодняя`, `christmas lofi`.
- «Jingle Bells» — общественное достояние, инструментальные версии безопасны.
- **Suno/Udio промт:**
  ```
  magical Christmas instrumental, sleigh bells, celesta and glockenspiel melody, soft strings,
  warm cozy festive mood, sparkling intro, 100 bpm, no vocals, 15 seconds
  ```
- Звуковой акцент: «дзынь»/звон колокольчика на хуке.

---

## 4. Панно «С Днём Рождения!» 🎈💜

**Кому продаём:** подарок девушке/маме/подруге, фотозона, декор к празднику, большая открытка-сюрприз.
**Главная фишка:** объёмное: настоящие пастельные шарики, ленты, стразы, сердечки, конверт для денег/пожеланий.

### Сценарий

| Время | Кадр (фото) | Текст на экране |
|---|---|---|
| 0–2 с | Шарики крупно, быстрый отъезд | **«Этот подарок не купить в магазине»** |
| 2–5 с | «С Днём Рождения!» и бант | **«Ручная работа 💜»** |
| 5–8 с | Сердечки, стразы, конверт с розами | **«Конверт для денег или пожеланий»** |
| 8–11 с | Панно целиком | **«Любой цвет и надпись под ваш повод»** |
| 11–15 с | Финал + конфетти | **«Закажи к празднику — пиши в директ»** + цена |

### VIDEO PROMPT (для `birthday_board.jpg`)

```
Vertical 9:16 product reel of a handmade birthday greeting board. A vivid purple panel decorated with
real pastel matte balloons (pink, mint, blue, yellow, lilac, peach) with curly white ribbons, a big cream
satin bow, "Happy Birthday" paper banners in orange and pink, stitched paper hearts in yellow and
orange, sparkling rhinestones, a paper figure of a girl in a floral dress with a pink felt heart,
and a pink rose-print envelope with a heart.
Keep the board EXACTLY as in the reference photo: same layout, colors and details; do not redraw
the banner text.
Shot 1: close-up on the pastel balloons, quick smooth pull-back, balloons gently sway.
Shot 2: slow slide down along the curly ribbons to the satin bow and hearts, rhinestones sparkle.
Shot 3: macro on the rose envelope, then pull back to reveal the whole board, soft festive bokeh.
Bright, soft, airy light, pastel dreamy mood, festive and tender, high detail, commercial product video.
Only subtle motion: balloons slightly swaying, ribbons fluttering, rhinestones glinting.
```

### NEGATIVE PROMPT

```
balloons flying away, balloons popping, changing layout, morphing, new text, garbled letters,
extra balloons, deformed hearts, watermark, people, hands, blurry, dark lighting, flicker
```

### 🎵 Музыка

- **Настроение:** нежное, праздничное, «девчачье». 110–128 BPM.
- **Поиск в библиотеке IG/VK:** `happy birthday instrumental`, `birthday pop`, `cute`, `party`, `sweet`.
- Мелодия «Happy Birthday» — общественное достояние (её же синтезирует `music.py` этого репозитория).
- **Suno/Udio промт:**
  ```
  sweet happy birthday pop instrumental, music box and glockenspiel intro, light claps, bubbly synths,
  pastel dreamy party mood, 120 bpm, catchy, no vocals, 15 seconds
  ```
- Звуковой акцент: «хлоп» хлопушки/конфетти на финале.

---

## 5. Бонус: общий ролик-витрина «3 поделки — какую выберешь?»

Такой ролик лучше всего собирает комментарии (а комментарии = охваты).

| Время | Кадр | Текст |
|---|---|---|
| 0–2 с | Быстрая нарезка трёх поделок по 0,5 сек | **«Делаю подарки, которых нет в магазинах»** |
| 2–6 с | Робот | **«1 — Робот-дачник 🤖»** |
| 6–10 с | Колесо обозрения (вечер) | **«2 — Новогоднее колесо 🎡»** |
| 10–13 с | Панно | **«3 — Панно на ДР 🎈»** |
| 13–15 с | Коллаж из трёх | **«Какую выберешь? Пиши цифру 👇»** |

Музыка: энергичный поп 124–128 BPM, смена кадра на каждую долю
(поиск: `upbeat pop`, `happy vlog`, `showcase`).

---

## 6. Подписи к постам

Подставьте цену и срок. Одинаковый смысл, но адаптировано под площадку.

### Instagram (Reels)

```
Этот робот-дачник сам сажает, сам поливает, сам удобряет 🤖🌱
Собран вручную из настоящих деталей: часы, манометр, спидометр, термометр.
Идеальный подарок для дачника и любителя сада.

💰 Цена: ___ ₽
⏳ Изготовлю на заказ за ___ дней
📩 Пишите «РОБОТ» в директ — расскажу подробности

#ручнаяработа #поделки #подарокдачнику #хендмейд #подарокпапе #декордлядачи #handmade #подароксвоимируками
```

### ВКонтакте (Клипы)

```
Робот-дачник ручной работы 🤖🌱 Сам сажает, сам поливает, сам удобряет!
Цена ___ ₽. Делаю на заказ — пишите в сообщения сообщества 👇
#ручнаяработа #поделки #подарок #хендмейд #дача
```

### Telegram

```
🤖 Робот-дачник — ручная работа

Часы, манометр, спидометр и термометр — всё настоящее.
Руки-шланги держат лопатку и грабли 🌱

💰 ___ ₽ | ⏳ ___ дней
👉 Заказать: @ваш_ник
```

Для колеса и панно — тот же шаблон, замените первую строку:

- **Колесо:** «Новогоднее колесо обозрения, которое светится ✨🎡 Золотые спицы, помпоны, мишура и гирлянда.
  Успейте заказать до Нового года!» — ключевое слово для директа «ЁЛКА».
  Хэштеги: `#новогоднийдекор #новогодняяподелка #подарокнановыйгод #поделкавсадик`
- **Панно:** «Подарок, который не купить в магазине 🎈💜 Объёмное панно с шариками, лентами и конвертом для
  пожеланий. Любой цвет и надпись под ваш праздник.» — ключевое слово «ПАННО».
  Хэштеги: `#подарокнаденьрождения #подарокдевушке #фотозона #декорпраздника`

---

## 7. Чек-лист перед публикацией

- [ ] Первые 2 секунды — самый яркий кадр и понятный хук-текст.
- [ ] Поделка на видео выглядит так же, как в жизни (нет «поплывших» деталей).
- [ ] Текст в безопасной зоне, читается без звука.
- [ ] Музыка из библиотеки площадки или своя (Suno) — чтобы ролик не заглушили.
- [ ] В конце — цена или «на заказ» + как купить (директ / сообщения / @ник).
- [ ] Обложка — кадр с поделкой целиком.
- [ ] Ключевое слово для директа («РОБОТ», «ЁЛКА», «ПАННО») — легко считать заявки с ролика.
