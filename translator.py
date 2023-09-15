from flask import Flask, request, jsonify, render_template
import sqlite3
import requests
import datetime
from xml.etree import ElementTree
import logging

app = Flask(__name__)
DATABASE = 'words.db'

def get_translation(word):
    url = f"https://dict.youdao.com/fsearch?q={word}"
    response = requests.get(url)

     # Check the response code
    if response.status_code != 200:
        logger.error(f'Error while retrieving translation for word {word}. Status Code: {response.status_code}. Response Text: {response.text}')
        raise Exception(f"Failed to retrieve translation for word {word}. Status Code: {response.status_code}")

    tree = ElementTree.fromstring(response.content)
    phonetic_symbol = tree.find('.//phonetic-symbol').text
    translations = [] 
    custom_translations = tree.findall(".//custom-translation/translation/content")
    for custom_translation in custom_translations:
        translations.append(custom_translation.text)

    return phonetic_symbol, translations


@app.route('/')
def index():
    return render_template("word_list.html")

@app.route('/add_word', methods=['get'])
def add_word():
    word = request.args.get('word')
    try:
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
    except Exception as e:
        logger.error(f'Error while adding word {word}. Exception: {e}')
        return jsonify({"message": "Error while adding word."}), 500            

    return jsonify({"message": "Word added successfully"})


@app.route('/get_words', methods=['GET'])
def get_words():
    date = request.args.get('date', get_latest_date())
    if not date:
        return jsonify({"message": "Error retrieving words from database."}), 500

    try:
    
        with sqlite3.connect(DATABASE) as con:
            cur = con.cursor()
            rows = cur.execute("SELECT word, phonetic, translation, audio_link FROM words WHERE date=?", (date,)).fetchall()

        words_list = [{"word": row[0], "phonetic": row[1], "translations": row[2].split('; '), "audio_link": row[3]} for row in rows]
        logger.info(f'Retrieved words for date: {date}.')
    except Exception as e:
        logger.error(f'Error while retrieving words for date {date}. Exception: {e}')
        return jsonify({"message": "Error while retrieving words."}), 500   

    return jsonify({"date": date, "words": words_list})

def get_latest_date():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Query to fetch the latest date from the database
        cursor.execute("SELECT MAX(date) FROM words")
        date = cursor.fetchone()[0]
        
        conn.close()
        return date
    except Exception as e:
        logger.error(f"Error while fetching latest date from database: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler()])

    logger = logging.getLogger('flask_server')

    app.run(debug=True, port=5001)
