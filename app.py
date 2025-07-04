# 1. Gerekli kütüphaneleri import ediyoruz
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import certifi
from datetime import datetime


# 2. Flask uygulamamızı standart olarak başlatıyoruz
app = Flask(__name__)


# 3. MONGODB BAĞLANTI KISMI
# --------------------------------------------------------------------------
# BURASI ÇOK ÖNEMLİ!
# Birazdan MongoDB Atlas'tan kopyaladığın o uzun linki bu tırnakların arasına yapıştıracaksın.
MONGO_URI = "mongodb+srv://kaankirca2019:9dybK4U5t2FsKdfb@flortwhispercluster.zlqvgea.mongodb.net/?retryWrites=true&w=majority&appName=FlortWhisperCluster"
# --------------------------------------------------------------------------

ca =certifi.where()

# MongoDB sunucusuna bağlanıyoruz
client = MongoClient(MONGO_URI, tlsCAFile=ca)

# 'flort_whisper_db' adında bir veritabanı seçiyoruz (yoksa kendi oluşturur)
db = client['flort_whisper_db']
# O veritabanının içinde 'people' adında bir koleksiyon (tablo gibi) seçiyoruz
people_collection = db['people']


# 4. ANA SAYFA ROUTE'UNU GÜNCELLEMEK
@app.route('/')
def home():
    # Veriyi artık elle yazmıyoruz, doğrudan veritabanından çekiyoruz.
    # .find({}) komutu, koleksiyondaki tüm belgeleri (kişileri) bulur.
    all_people = list(people_collection.find({}))
    
    # Bulduğumuz veriyi 'people' adıyla HTML'e gönderiyoruz.
    return render_template('index.html', people=all_people)

@app.route('/ara', methods=['POST'])
def arama_yap():
    #Formdan gelen arama terimini al
    query = request.form.get('query')

    #Veritabanında bu isimde bir kişi var mı diye kontrol et
    person = people_collection.find_one({'name': query})

    if person:
        #Kişi varsa onun profil sayfasına yönlendir
        return redirect(url_for('kisi_profili', kisi_adi=query))
    else:
        #Kişi yoksa, yeni kişi oluşturma sayfasına yönlendir
        return redirect(url_for('yeni_kisi_olustur', kisi_adi=query))


# KİŞİ PROFİLİ ROUTE'U (YORUM GÖSTERME VE EKLEME)
@app.route('/kisi/<kisi_adi>', methods=['GET', 'POST'])
def kisi_profili(kisi_adi):
    person = people_collection.find_one({'name': kisi_adi})

    if not person:
        return "Bu kişi bulunamadı."

    # Eğer form gönderilerek (POST) gelinmişse...
    if request.method == 'POST':
        new_comment_text = request.form.get('comment')
        if new_comment_text:
            comment_doc = {'text': new_comment_text, 'timestamp': datetime.now()}
            people_collection.update_one(
                {'name': kisi_adi},
                {'$push': {'comments': comment_doc}}
            )
        return redirect(url_for('kisi_profili', kisi_adi=kisi_adi))

    # Eğer sayfa normal ziyaret edilmişse (GET)...
    return render_template('kisi_profili.html', person=person)

@app.route('/olustur/<kisi_adi>', methods=['GET', 'POST'])
def yeni_kisi_olustur(kisi_adi):
    #Eğer Evet butonuna basılmışsa (POST)
    if request.method == 'POST':
        existing_person = people_collection.find_one({'name': kisi_adi})
        if not existing_person:
            people_collection.insert_one({'name': kisi_adi, 'comments': []})
        return redirect(url_for('kisi_profili', kisi_adi=kisi_adi))
    
    #Eğer sayfa ilk kez ziyaret ediliyorsa (GET), onay sayfasını göster
    return render_template('yeni_kisi_formu.html', kisi_adi=kisi_adi)

# 6. VERİTABANINI İLK VERİLERLE DOLDURMAK (Bir kerelik)
# Eğer 'people' koleksiyonumuzun içinde hiç veri yoksa, bu kod çalışır.
if people_collection.count_documents({}) == 0:
    # Başlangıç verilerimizi tanımlıyoruz
    initial_people = [
        {'name': 'Tarkan', 'comments': []},
        {'name': 'Cem Yılmaz', 'comments': []},
        {'name': 'Sezen Aksu', 'comments': []}
    ]
    # Bu verileri toplu halde veritabanına ekliyoruz
    people_collection.insert_many(initial_people)
    # Eklendiğine dair terminale bir mesaj yazdırıyoruz
    print("Veritabanına başlangıç verileri eklendi!")


# 7. UYGULAMAYI ÇALIŞTIRMAK
if __name__ == '__main__':
    app.run(debug=True)