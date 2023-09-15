from flask import Flask, request, jsonify, render_template
import sqlite3
import requests
import datetime
from xml.etree import ElementTree

app = Flask(__name__)
DATABASE = 'words.db'

def get_translation(word):
    url = f"https://dict.youdao.com/fsearch?q={word}"
    response = requests.get(url)
    if response.status_code == 200:
        from xml.etree import ElementTree
        tree = ElementTree.fromstring(response.content)
        phonetic_symbol = tree.find('.//phonetic-symbol').text
        translations = [] 
        custom_translations = tree.findall(".//custom-translation/translation/content")
        for custom_translation in custom_translations:
            translations.append(custom_translation.text)

        return phonetic_symbol, translations
    return None, None

@app.route('/')
def index():
    return render_template("word_list.html")

@app.route('/add_word', methods=['get'])
def add_word():
    word = request.args.get('word')
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Get data from the third-party API
    phonetic_symbol, translations = get_translation(word)
    translation_text = '; '.join([trans for trans in translations])
    audio_link = f"http://dict.youdao.com/dictvoice?audio={word}&type=0"

    # Save to the database
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        cur.execute("INSERT OR REPLACE INTO words (word, phonetic, translation, audio_link, date) VALUES (?, ?, ?, ?, ?)",
                    (word, phonetic_symbol, translation_text, audio_link, date))
        con.commit()

    return jsonify({"message": "Word added successfully"})


@app.route('/get_words', methods=['GET'])
def get_words():
    date = request.args.get('date', datetime.datetime.now().strftime("%Y-%m-%d"))
    
    with sqlite3.connect(DATABASE) as con:
        cur = con.cursor()
        rows = cur.execute("SELECT word, phonetic, translation, audio_link FROM words WHERE date=?", (date,)).fetchall()

    words_list = [{"word": row[0], "phonetic": row[1], "translations": row[2].split('; '), "audio_link": row[3]} for row in rows]

    return jsonify({"date": date, "words": words_list})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
