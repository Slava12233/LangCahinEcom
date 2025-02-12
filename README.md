# LangCahinEcom - חנות חכמה עם בוט טלגרם 🤖

מערכת ניהול חנות חכמה המשלבת בוט טלגרם עם יכולות AI מתקדמות.

## תכונות עיקריות 🌟

- בוט טלגרם אינטראקטיבי 💬
- אינטגרציה עם WooCommerce 🛍️
- מערכת לוגים מתקדמת 📊
- תמיכה במספר מודלי AI 🧠
- מטמון תשובות לביצועים משופרים ⚡
- טיפול בשגיאות חכם 🛡️

## דרישות מערכת 🔧

- Python 3.8+
- Telegram Bot Token
- DeepSeek API Key
- WooCommerce חנות פעילה עם מפתחות API

## התקנה 🚀

1. שכפל את הרפוזיטורי:
```bash
git clone https://github.com/Slava12233/LangCahinEcom.git
cd LangCahinEcom
```

2. התקן את הדרישות:
```bash
pip install -r requirements.txt
```

3. העתק את קובץ `.env.example` ל-`.env` והגדר את המשתנים הנדרשים:
```bash
cp .env.example .env
```

4. הפעל את הבוט:
```bash
python src/main.py
```

## מבנה הפרויקט 📁

```
LangCahinEcom/
├── src/
│   ├── agents/
│   │   ├── orchestrator.py
│   │   └── woocommerce_agent.py
│   ├── utils/
│   │   └── logger.py
│   ├── bot.py
│   └── main.py
├── logs/
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

## רישיון 📄

MIT License

## תרומה 🤝

מוזמנים לתרום לפרויקט! אנא צרו issue או שלחו pull request. 