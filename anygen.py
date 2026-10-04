# ============================================
#   AnyGen — 40 генераторов + шаринг
#   Домен: https://anygen.ru
#   Запуск: gunicorn anygen:app
# ============================================

from flask import Flask, render_template_string, jsonify, abort
import random
import string
import hashlib
import uuid
import json
import os
from datetime import datetime

app = Flask(__name__)

SITE_URL = "https://anygen.ru"
DB_FILE = "generated.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def gen_password():
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(16))

def gen_hash():
    return hashlib.sha256(str(random.random()).encode()).hexdigest()

def gen_emoji():
    emojis = ["😀","😂","😍","🤔","😎","🥳","😭","🤯","🥶","🤩","😴","🤖","👾","🎃","🔥","✨","💎","🚀","🌈","🍕"]
    return ''.join(random.choice(emojis) for _ in range(5))

def gen_lottery():
    return ', '.join(str(n) for n in sorted(random.sample(range(1, 46), 6)))

GENERATORS = [
    {"id":"password","emoji":"🔐","name":"Пароль","desc":"Надёжный пароль","type":"func","func":gen_password},
    {"id":"pin","emoji":"🔢","name":"PIN-код","desc":"4-значный код","type":"pin"},
    {"id":"uuid","emoji":"🆔","name":"UUID","desc":"Уникальный ID","type":"uuid"},
    {"id":"hash","emoji":"#️⃣","name":"SHA-256","desc":"Хеш-строка","type":"func","func":gen_hash},
    {"id":"nick","emoji":"😎","name":"Никнейм","desc":"Случайный ник","type":"template",
     "data":{"a":["Быстрый","Тёмный","Красный","Синий","Дикий","Хитрый","Холодный","Огненный","Лунный","Стальной"],
             "b":["Волк","Дракон","Тигр","Орёл","Феникс","Тень","Вихрь","Клинок","Шторм","Призрак"]},
     "pattern":"{a}{b}{n}","n_min":1,"n_max":999},
    {"id":"name","emoji":"👤","name":"Имя","desc":"Случайное ФИО","type":"template",
     "data":{"a":["Алекс","Иван","Максим","Дмитрий","Артём","Егор","Никита","Кирилл","Роман","Павел"],
             "b":["Смирнов","Иванов","Кузнецов","Попов","Соколов","Лебедев","Козлов","Новиков","Морозов","Петров"]},
     "pattern":"{a} {b}"},
    {"id":"email","emoji":"📧","name":"Email","desc":"Случайный email","type":"template",
     "data":{"a":["user","admin","mail","info","contact","hello","test","dev"],
             "b":["mail.ru","gmail.com","yandex.ru","example.com","site.ru"]},
     "pattern":"{a}{n}@{b}","n_min":1,"n_max":999},
    {"id":"city","emoji":"🏙️","name":"Город","desc":"Название города","type":"template",
     "data":{"a":["Ново","Красно","Бело","Черно","Верхне","Нижне","Старо","Средне"],
             "b":["горск","поль","реченск","озёрск","морск","град","славль","камск"]},
     "pattern":"{a}{b}"},
    {"id":"country","emoji":"🌍","name":"Страна","desc":"Название страны","type":"template",
     "data":{"a":["Республика","Королевство","Федерация","Империя","Союз","Княжество"],
             "b":["Бергамутия","Зелдания","Аквилония","Норвания","Тирения","Люминия","Ордания","Кальвания"]},
     "pattern":"{a} {b}"},
    {"id":"planet","emoji":"🪐","name":"Планета","desc":"Название планеты","type":"template",
     "data":{"a":["Ксе","Зор","Тал","Вер","Ним","Люм","Кар","Дра"],
             "b":["рон","тис","мир","дос","кар","ния","пар","зул"]},
     "pattern":"{a}{b}"},
    {"id":"color","emoji":"🎨","name":"HEX-цвет","desc":"Случайный цвет","type":"color"},
    {"id":"rgb","emoji":"🌈","name":"RGB-цвет","desc":"Цвет в RGB","type":"rgb"},
    {"id":"number","emoji":"🔢","name":"Число","desc":"1–100","type":"number","min":1,"max":100},
    {"id":"dice","emoji":"🎲","name":"Кубик","desc":"Бросок 1–6","type":"dice"},
    {"id":"coin","emoji":"🪙","name":"Монетка","desc":"Орёл или решка","type":"coin"},
    {"id":"lottery","emoji":"🎟️","name":"Лотерея","desc":"6 чисел 1–45","type":"func","func":gen_lottery},
    {"id":"idea","emoji":"💡","name":"Идея","desc":"Идея для проекта","type":"list",
     "data":["Приложение для обмена навыками","Сервис доставки домашней еды","Платформа для поиска попутчиков",
             "Игра про выживание в мегаполисе","Бот для медитации","Сайт с рецептами по ингредиентам",
             "Маркетплейс ручной работы","Трекер привычек с геймификацией","Сервис аренды инструментов","Соцсеть для коллекционеров"]},
    {"id":"word","emoji":"📖","name":"Слово","desc":"Случайное слово","type":"list",
     "data":["кот","дом","лес","мир","свет","тьма","путь","сон","дым","лёд","огонь","ветер","камень","река","гора"]},
    {"id":"sentence","emoji":"📝","name":"Предложение","desc":"Случайная фраза","type":"template",
     "data":{"a":["Кот","Дракон","Рыцарь","Волшебник","Пёс","Птица"],
             "b":["летит","идёт","спит","поёт","танцует","ищет"],
             "c":["к звёздам","в лесу","по крыше","за мечтой","в тишине","у реки"]},
     "pattern":"{a} {b} {c}."},
    {"id":"quote","emoji":"💬","name":"Цитата","desc":"Мудрость","type":"list",
     "data":["«Дорогу осилит идущий»","«Не откладывай на завтра то, что можно сделать сегодня»",
             "«Знание — сила»","«Терпение и труд всё перетрут»","«Семь раз отмерь, один раз отрежь»",
             "«Всё гениальное — просто»","«Кто ищет, тот всегда найдёт»"]},
    {"id":"fact","emoji":"🧠","name":"Факт","desc":"Интересный факт","type":"list",
     "data":["Мёд не портится тысячелетиями.","Осьминоги имеют три сердца.","Бананы — это ягоды.",
             "Молния в 5 раз горячее поверхности Солнца.","У улитки около 25 000 зубов.",
             "Венера вращается против часовой стрелки.","Пингвины делают предложение камешком."]},
    {"id":"joke","emoji":"😂","name":"Шутка","desc":"Случайная шутка","type":"list",
     "data":["Почему программисты путают Хэллоуин и Рождество? Потому что OCT 31 == DEC 25.",
             "Есть 10 типов людей: те, кто понимает двоичный код, и те, кто нет.",
             "— Как дела? — Всё компилируется.",
             "Программист — это машина по превращению кофе в код."]},
    {"id":"emoji","emoji":"😀","name":"Эмодзи","desc":"5 эмодзи","type":"func","func":gen_emoji},
    {"id":"team","emoji":"⚔️","name":"Команда","desc":"Название команды","type":"template",
     "data":{"a":["Красные","Синие","Тёмные","Золотые","Железные","Огненные","Ледяные","Дикие"],
             "b":["Волки","Драконы","Орлы","Титаны","Фениксы","Львы","Ястребы","Змеи"]},
     "pattern":"{a} {b}"},
    {"id":"game","emoji":"🎮","name":"Игра","desc":"Название игры","type":"template",
     "data":{"a":["Cyber","Dark","Neo","Mega","Ultra","Hyper","Star","Pixel"],
             "b":["City","World","Legends","Warriors","Quest","Racing","Empire","Survival"]},
     "pattern":"{a} {b}"},
    {"id":"book","emoji":"📚","name":"Книга","desc":"Название книги","type":"template",
     "data":{"a":["Тайна","Легенда","Хроники","История","Сказание","Путь","Тень","Свет"],
             "b":["древнего города","потерянного мира","последнего героя","северных земель","алмазного трона","тихой реки"]},
     "pattern":"{a} {b}"},
    {"id":"song","emoji":"🎵","name":"Песня","desc":"Название песни","type":"template",
     "data":{"a":["Ночной","Вечный","Холодный","Яркий","Тихий","Дикий","Лунный","Огненный"],
             "b":["дождь","город","свет","путь","сон","ветер","берег","огонь"]},
     "pattern":"{a} {b}"},
    {"id":"date","emoji":"📅","name":"Дата","desc":"Случайная дата","type":"date"},
    {"id":"time","emoji":"⏰","name":"Время","desc":"Случайное время","type":"time"},
    {"id":"domain","emoji":"🌐","name":"Домен","desc":"Случайный домен","type":"template",
     "data":{"a":["super","fast","best","my","new","top","pro","web"],
             "b":[".ru",".com",".net",".org",".io"]},
     "pattern":"{a}{n}{b}","n_min":1,"n_max":99},
    {"id":"animal","emoji":"🐾","name":"Животное","desc":"Случайное животное","type":"list",
     "data":["🐱 Кот","🐶 Пёс","🦊 Лис","🐻 Медведь","🐼 Панда","🦁 Лев","🐯 Тигр","🐺 Волк","🦉 Сова","🐸 Жаба"]},
    {"id":"spell","emoji":"✨","name":"Заклинание","desc":"Название заклинания","type":"template",
     "data":{"a":["Огненный","Ледяной","Тёмный","Святой","Древний","Кровавый","Лунный","Громовой"],
             "b":["шар","вихрь","луч","щит","клинок","шторм","взрыв","поток"]},
     "pattern":"{a} {b}"},
    {"id":"potion","emoji":"🧪","name":"Зелье","desc":"Название зелья","type":"template",
     "data":{"a":["Красное","Синее","Зелёное","Чёрное","Золотое","Лунное"],
             "b":["зелье силы","зелье мудрости","зелье скорости","зелье невидимости","зелье удачи","зелье здоровья"]},
     "pattern":"{a} {b}"},
    {"id":"dish","emoji":"🍲","name":"Блюдо","desc":"Название блюда","type":"template",
     "data":{"a":["Жареный","Тушёный","Печёный","Маринованный","Острый","Сладкий"],
             "b":["картофель","цыплёнок","перец","баклажан","грибы","сыр"]},
     "pattern":"{a} {b}"},
    {"id":"cocktail","emoji":"🍹","name":"Коктейль","desc":"Название коктейля","type":"template",
     "data":{"a":["Синий","Красный","Золотой","Лунный","Огненный","Ледяной"],
             "b":["закат","рассвет","шторм","берег","мираж","прибой"]},
     "pattern":"{a} {b}"},
    {"id":"profession","emoji":"💼","name":"Профессия","desc":"Случайная профессия","type":"list",
     "data":["Программист","Дизайнер","Врач","Учитель","Инженер","Повар","Пилот","Архитектор",
             "Фотограф","Журналист","Музыкант","Художник","Учёный","Юрист","Бухгалтер"]},
    {"id":"role","emoji":"🎭","name":"Роль","desc":"Роль в команде","type":"list",
     "data":["Лидер","Стратег","Исполнитель","Генератор идей","Критик","Дипломат","Аналитик","Творец"]},
    {"id":"car","emoji":"🚗","name":"Машина","desc":"Название машины","type":"template",
     "data":{"a":["Turbo","Neo","Mega","Ultra","Hyper","Cyber","Star"],
             "b":["X1","GT","Pro","Max","Sport","Prime"]},
     "pattern":"{a} {b}"},
    {"id":"hobby","emoji":"🎯","name":"Хобби","desc":"Случайное хобби","type":"list",
     "data":["Рисование","Плавание","Бег","Шахматы","Гитара","Фотография","Кулинария","Садоводство",
             "Путешествия","Чтение","Танцы","Рыбалка"]},
    {"id":"elf","emoji":"🧝","name":"Эльф","desc":"Имя эльфа","type":"template",
     "data":{"a":["Эль","Аэ","Ли","Та","Силь","Ми","Фа"],
             "b":["ронд","лас","тиэль","наар","дир","мир","вэн"]},
     "pattern":"{a}{b}"},
    {"id":"orc","emoji":"👹","name":"Орк","desc":"Имя орка","type":"template",
     "data":{"a":["Гром","Кров","Желез","Камен","Тёмн","Дик"],
             "b":["зуб","клык","кулак","топор","молот","череп"]},
     "pattern":"{a}{b}"},
    {"id":"ghost","emoji":"👻","name":"Призрак","desc":"Имя призрака","type":"template",
     "data":{"a":["Тихий","Холодный","Бледный","Лунный","Ночной","Печальный"],
             "b":["шёпот","стон","вздох","крик","плач","зов"]},
     "pattern":"{a} {b}"},
    {"id":"curse","emoji":"💀","name":"Проклятие","desc":"Название проклятия","type":"template",
     "data":{"a":["Тёмное","Вечное","Кровавое","Ледяное","Огненное","Древнее"],
             "b":["проклятие","заклятие","проклятье","заклинание"]},
     "pattern":"{a} {b}"},
]

GENERATORS_BY_ID = {g["id"]: g for g in GENERATORS}

def generate_value(g):
    t = g["type"]
    if t == "func": return str(g["func"]())
    if t == "list": return random.choice(g["data"])
    if t == "template":
        result = g["pattern"]
        for key, arr in g["data"].items():
            result = result.replace("{" + key + "}", random.choice(arr))
        if "{n}" in result:
            n = random.randint(g.get("n_min", 1), g.get("n_max", 999))
            result = result.replace("{n}", str(n))
        return result
    if t == "number": return str(random.randint(g["min"], g["max"]))
    if t == "dice": return f"🎲 Выпало: {random.randint(1, 6)}"
    if t == "coin": return random.choice(["🪙 Орёл", "🪙 Решка"])
    if t == "pin": return ''.join(random.choice(string.digits) for _ in range(4))
    if t == "uuid": return str(uuid.uuid4())
    if t == "color": return "#{:06x}".format(random.randint(0, 0xFFFFFF))
    if t == "rgb": return f"rgb({random.randint(0,255)}, {random.randint(0,255)}, {random.randint(0,255)})"
    if t == "date":
        start = datetime(2000,1,1).toordinal()
        end = datetime(2030,12,31).toordinal()
        return datetime.fromordinal(random.randint(start, end)).strftime("%d.%m.%Y")
    if t == "time": return f"{random.randint(0,23):02d}:{random.randint(0,59):02d}"
    return "???"

MAIN_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AnyGen — генераторы</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',Arial,sans-serif; background:#0d1117; color:#e6edf3; min-height:100vh; }
  header { text-align:center; padding:40px 20px 20px; }
  h1 { font-size:48px; letter-spacing:4px; background:linear-gradient(90deg,#58a6ff,#bc8cff,#ff7b72); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
  header p { color:#8b949e; margin-top:8px; }
  #search { margin-top:20px; padding:12px 20px; width:100%; max-width:400px; background:#161b22; border:1px solid #30363d; border-radius:30px; color:#e6edf3; font-size:15px; outline:none; }
  #search:focus { border-color:#58a6ff; }
  main { padding:30px 20px 60px; max-width:1200px; margin:0 auto; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:14px; }
  .card { padding:18px; background:#161b22; border:1px solid #30363d; border-radius:12px; cursor:pointer; transition:.2s; }
  .card:hover { border-color:#58a6ff; transform:translateY(-3px); }
  .emoji { font-size:28px; }
  .name { font-weight:600; margin-top:8px; }
  .desc { font-size:12px; color:#8b949e; margin-top:4px; }
  .modal { position:fixed; inset:0; display:none; align-items:center; justify-content:center; background:rgba(0,0,0,.8); z-index:100; padding:20px; }
  .modal.open { display:flex; }
  .modal-content { background:#161b22; border:1px solid #30363d; border-radius:16px; padding:30px; width:100%; max-width:500px; position:relative; }
  .close { position:absolute; top:14px; right:14px; background:transparent; border:none; color:#8b949e; font-size:18px; cursor:pointer; }
  .close:hover { color:#ff7b72; }
  .modal-content h2 { margin-bottom:20px; }
  .gen-btn { width:100%; padding:14px; background:linear-gradient(90deg,#58a6ff,#bc8cff); border:none; border-radius:10px; color:#fff; font-size:16px; font-weight:600; cursor:pointer; margin-top:10px; }
  .gen-btn:hover { opacity:.9; }
  .share-btn { width:100%; padding:12px; background:#21262d; border:1px solid #30363d; border-radius:10px; color:#e6edf3; font-size:14px; cursor:pointer; margin-top:8px; display:none; }
  .share-btn:hover { border-color:#58a6ff; }
  .result { margin-top:16px; padding:16px; background:#0d1117; border:1px solid #30363d; border-radius:10px; font-size:18px; text-align:center; word-break:break-all; min-height:56px; display:flex; align-items:center; justify-content:center; }
  .link-box { margin-top:12px; padding:10px; background:#0d1117; border:1px dashed #30363d; border-radius:8px; font-size:12px; color:#8b949e; word-break:break-all; display:none; }
  .link-box.show { display:block; }
  .link-box a { color:#58a6ff; text-decoration:none; }
  footer { text-align:center; padding:20px; color:#484f58; font-size:13px; }
</style>
</head>
<body>
<header>
  <h1>AnyGen</h1>
  <p>{{ count }} генераторов в одном месте</p>
  <input id="search" type="text" placeholder="🔍 Поиск...">
</header>
<main>
  <div class="grid" id="grid"></div>
</main>

<div class="modal" id="modal">
  <div class="modal-content">
    <button class="close" onclick="closeModal()">✕</button>
    <h2 id="modal-title"></h2>
    <div class="result" id="result">Нажми «Сгенерировать»</div>
    <button class="gen-btn" onclick="generate()">🎲 Сгенерировать</button>
    <button class="share-btn" id="share-btn" onclick="share()">🔗 Поделиться ссылкой</button>
    <div class="link-box" id="link-box"></div>
  </div>
</div>

<footer>AnyGen · anygen.ru</footer>

<script>
const SITE_URL = 'https://anygen.ru';
const GENERATORS = {{ generators|tojson }};
let currentId = null;
let currentUuid = null;

const grid = document.getElementById('grid');
const search = document.getElementById('search');
const modal = document.getElementById('modal');
const modalTitle = document.getElementById('modal-title');
const result = document.getElementById('result');
const shareBtn = document.getElementById('share-btn');
const linkBox = document.getElementById('link-box');

function render(list) {
  grid.innerHTML = '';
  list.forEach(g => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `<div class="emoji">${g.emoji}</div><div class="name">${g.name}</div><div class="desc">${g.desc}</div>`;
    card.onclick = () => openModal(g);
    grid.appendChild(card);
  });
}

function openModal(g) {
  currentId = g.id;
  currentUuid = null;
  modalTitle.textContent = g.emoji + ' ' + g.name;
  result.textContent = 'Нажми «Сгенерировать»';
  shareBtn.style.display = 'none';
  linkBox.classList.remove('show');
  modal.classList.add('open');
}

function closeModal() { modal.classList.remove('open'); }

async function generate() {
  if (!currentId) return;
  const res = await fetch('/gen/sgg/' + currentId);
  const data = await res.json();
  result.textContent = data.result;
  currentUuid = data.uuid;
  shareBtn.style.display = 'block';
  linkBox.classList.remove('show');
}

function share() {
  if (!currentUuid) return;
  const url = SITE_URL + '/gen/shgg/' + currentUuid;
  linkBox.innerHTML = '🔗 <a href="' + url + '" target="_blank">' + url + '</a>';
  linkBox.classList.add('show');
  navigator.clipboard.writeText(url);
}

search.addEventListener('input', () => {
  const q = search.value.toLowerCase();
  render(GENERATORS.filter(g => g.name.toLowerCase().includes(q) || g.desc.toLowerCase().includes(q)));
});

modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

render(GENERATORS);
</script>
</body>
</html>
"""

SHARE_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} — AnyGen</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'Segoe UI',Arial,sans-serif; background:#0d1117; color:#e6edf3; min-height:100vh; display:flex; align-items:center; justify-content:center; padding:20px; }
  .card { background:#161b22; border:1px solid #30363d; border-radius:16px; padding:40px; max-width:600px; width:100%; text-align:center; }
  .emoji { font-size:48px; }
  h1 { font-size:24px; margin:16px 0 8px; }
  .date { color:#8b949e; font-size:13px; }
  .value { margin:30px 0; padding:24px; background:#0d1117; border:1px solid #30363d; border-radius:12px; font-size:22px; word-break:break-all; }
  .btn { display:inline-block; padding:12px 30px; background:linear-gradient(90deg,#58a6ff,#bc8cff); border:none; border-radius:30px; color:#fff; font-size:15px; font-weight:600; text-decoration:none; }
  .uuid { margin-top:20px; font-size:11px; color:#484f58; word-break:break-all; }
</style>
</head>
<body>
  <div class="card">
    <div class="emoji">{{ emoji }}</div>
    <h1>{{ title }}</h1>
    <div class="date">{{ date }}</div>
    <div class="value">{{ value }}</div>
    <a href="/" class="btn">🎲 Сгенерировать ещё</a>
    <div class="uuid">ID: {{ uuid }}</div>
  </div>
</body>
</html>
"""

@app.route('/')
def index():
    gens = [{"id":g["id"],"emoji":g["emoji"],"name":g["name"],"desc":g["desc"]} for g in GENERATORS]
    return render_template_string(MAIN_HTML, generators=gens, count=len(gens))

@app.route('/gen/sgg/<gen_id>')
def gen_sgg(gen_id):
    g = GENERATORS_BY_ID.get(gen_id)
    if not g:
        return jsonify({"error": "Генератор не найден"}), 404

    result_value = generate_value(g)
    new_uuid = str(uuid.uuid4())

    db = load_db()
    db[new_uuid] = {
        "gen_id": gen_id,
        "emoji": g["emoji"],
        "title": g["name"],
        "value": result_value,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M")
    }
    save_db(db)

    return jsonify({
        "uuid": new_uuid,
        "result": result_value,
        "share_url": f"{SITE_URL}/gen/shgg/{new_uuid}"
    })

@app.route('/gen/shgg/<uuid_str>')
def gen_shgg(uuid_str):
    db = load_db()
    item = db.get(uuid_str)
    if not item:
        abort(404)
    return render_template_string(
        SHARE_HTML,
        emoji=item["emoji"],
        title=item["title"],
        value=item["value"],
        date=item["date"],
        uuid=uuid_str
    )

@app.errorhandler(404)
def not_found(e):
    return "<h1 style='font-family:sans-serif;text-align:center;margin-top:100px'>404 — не найдено</h1>", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
