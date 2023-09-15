from flask import Flask, request, jsonify, render_template
import sqlite3
import requests
import datetime

app = Flask(__name__)
DATABASE = 'words.db'

def init_db():
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS words (word TEXT, date TEXT)")

def get_translation(word):
    url = f"https://dict.youdao.com/fsearch?q={word}"
    response = requests.get(url)
    if response.status_code == 200:
        from xml.etree import ElementTree
        tree = ElementTree.fromstring(response.content)
        phonetic_symbol = tree.find('.//phonetic-symbol').text
        translation = tree.find('.//custom-translation/translation/content').text
        return phonetic_symbol, translation
    return None, None

@app.route('/')
def index():
    return render_template("word_list.html")

@app.route('/add_word', methods=['get'])
def add_word():
    word = request.args.get('word')
    phonetic_symbol, translation = get_translation(word)
    if not phonetic_symbol:
        return jsonify({"error": "Failed to fetch translation"}), 400
    
    # Save to database
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("INSERT INTO words (word, date) VALUES (?, ?)", (word, date))
        con.commit()

    pronunciation_url = f"http://dict.youdao.com/dictvoice?audio={word}&type=0"
    return jsonify({"word": word, "translation": translation, "pronunciation_url": pronunciation_url})

@app.route('/get_words', methods=['GET'])
def get_words():
    date = request.args.get('date', datetime.datetime.now().strftime("%Y-%m-%d"))
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        rows = cur.execute("SELECT word FROM words WHERE date=?", (date,)).fetchall()

    words_list = []
    for row in rows:
        word = row[0]
        phonetic_symbol, translation = get_translation(word) # Assume you have get_translation function from previous code
        words_list.append({
            "word": word, 
            "translation": translation, 
            "phonetic": phonetic_symbol
        })
    return jsonify({"date": date, "words": words_list})

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
