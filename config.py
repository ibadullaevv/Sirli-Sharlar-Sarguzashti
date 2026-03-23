import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

GAME_DURATION_MINUTES = 60

# Aylanma marshrut variantlari (har jamoa turli bosqichdan boshlaydi)
ROUTE_VARIANTS = [
    [1, 2, 3, 4, 5],
    [2, 3, 4, 5, 1],
    [3, 4, 5, 1, 2],
    [4, 5, 1, 2, 3],
    [5, 1, 2, 3, 4],
]

# Bosqichlar konfiguratsiyasi
STAGES = {
    1: {
        "name": "Axborot markazi oldi",
        "ball": 2,
        "secret_code": "BILIM2024",
        "location": "Axborot markazi binosi oldidagi maydon",
        "tasks": (
            "📍 1-BOSQICH: AXBOROT MARKAZI OLDI\n"
            "Ball: 2\n\n"
            "Topshiriqlar:\n"
            "1️⃣ Guruh selfisi — barcha a'zolar + bino ko'rinsin\n"
            "2️⃣ 5 ta mantiqiy savolga javob (video yoki matn):\n"
            "   • Bu tarixiy bino qachon qurilgan?\n"
            "   • Binoning me'mori kim?\n"
            "   • Bino dastlab nima maqsadda qurilgan?\n"
            "   • Bino nechta qavatdan iborat?\n"
            "   • Bino atrofida nechta ustun bor?\n\n"
            "🔑 Marbleverse'dan maxfiy kodni toping va yuboring!\n"
            "📸 Selfi + 🎥 Video + 🔑 Kodni yuboring."
        ),
    },
    2: {
        "name": "Tarixiy xiyobon",
        "ball": 3,
        "secret_code": "TABIAT2024",
        "location": "Daraxtlar qatori / xiyobon",
        "tasks": (
            "📍 2-BOSQICH: TARIXIY XIYOBON\n"
            "Ball: 3\n\n"
            "Topshiriqlar:\n"
            "1️⃣ Jamoaviy sakrash selfisi — hammasi havoda, 3+ daraxt ko'rinsin\n"
            "2️⃣ Hudud haqida 10 ta fakt aytish (video, 60 soniyagacha)\n\n"
            "🔑 Marbleverse'dan maxfiy kodni toping va yuboring!\n"
            "📸 Selfi + 🎥 Video + 🔑 Kodni yuboring."
        ),
    },
    3: {
        "name": "Asosiy bino kirish qismi",
        "ball": 2,
        "secret_code": "ILMDARVO",
        "location": "Asosiy bino eshigi / peshtoqi",
        "tasks": (
            "📍 3-BOSQICH: ASOSIY BINO KIRISH QISMI\n"
            "Ball: 2\n\n"
            "Topshiriqlar:\n"
            "1️⃣ Tartibli jamoa selfisi — bino nomi/yozuvi ko'rinsin\n"
            "2️⃣ Tezkor bilim sinovi (video):\n"
            "   • 10 soniyada 5 ta fan nomini ayting\n"
            "   • 15 soniyada inglizcha 5 ta gap ayting\n\n"
            "🔑 Marbleverse'dan maxfiy kodni toping va yuboring!\n"
            "📸 Selfi + 🎥 Video + 🔑 Kodni yuboring."
        ),
    },
    4: {
        "name": "Sport maydoni",
        "ball": 3,
        "secret_code": "SPORT2024",
        "location": "Sport maydoni / stadion",
        "tasks": (
            "📍 4-BOSQICH: SPORT MAYDONI\n"
            "Ball: 3\n\n"
            "Topshiriqlar:\n"
            "1️⃣ Estafeta yugurish videosi (30 soniyagacha)\n"
            "   — Navbatma-navbat 20m yugurish, oxirida \"TUGATDIK!\" deyish\n"
            "2️⃣ Jamoaviy mashq selfisi — sport maydoni ko'rinsin\n\n"
            "🔑 Marbleverse'dan maxfiy kodni toping va yuboring!\n"
            "📸 Selfi + 🎥 Video + 🔑 Kodni yuboring."
        ),
    },
    5: {
        "name": "Oshxona / Tarixiy bino atrofi",
        "ball": 2,
        "secret_code": "FINAL2024",
        "location": "Oshxona yoki tarixiy bino yonidagi maydon",
        "tasks": (
            "📍 5-BOSQICH: OSHXONA ATROFI\n"
            "Ball: 2\n\n"
            "Topshiriqlar:\n"
            "1️⃣ Kulgili jamoaviy selfi — oshxona nomi ko'rinsin\n"
            "2️⃣ Shifrlangan so'zni yeching:\n"
            "   18-1-26-9-13\n"
            "   (har raqam = alifbo tartibidagi harf)\n\n"
            "🔑 Marbleverse'dan maxfiy kodni toping va yuboring!\n"
            "📸 Selfi + 🔑 Kod + 💬 Shifr javobini yuboring."
        ),
    },
}
