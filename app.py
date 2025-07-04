# 1. Gerekli kütüphaneleri import ediyoruz
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import os


# 2. Flask uygulamamızı standart olarak başlatıyoruz
app = Flask(__name__)

app.secret_key = 'flort_whisper_icin_cok_gizli_bir_anahtar_12345'

# 3. MONGODB BAĞLANTI KISMI
# --------------------------------------------------------------------------
# BURASI ÇOK ÖNEMLİ!
# Birazdan MongoDB Atlas'tan kopyaladığın o uzun linki bu tırnakların arasına yapıştıracaksın.
MONGO_URI = os.environ.get('MONGO_URI')
# --------------------------------------------------------------------------

# MongoDB sunucusuna bağlanıyoruz
client = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)

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
            comment_doc = {
                '_id': ObjectId(),
                'text': new_comment_text, 'timestamp': datetime.now(),
                'timestamp': datetime.now()
            }
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

@app.route('/yorum_sil/<kisi_adi>/<yorum_id>')
def yorum_sil(kisi_adi, yorum_id):
    #GÜVENLİK KONTROLÜ
    if not session.get('is_admin'):
        return "Bu işlem için yetkiniz yok!", 403 #403 Forbidden hatası
    # URL'den gelen yorum_id'si bir string'dir.
    # Onu MongoDB'nin anlayacağı ObjectId formatına çeviriyoruz.
    yorum_id_obj = ObjectId(yorum_id)
  
    # MongoDB'nin '$pull' operatörünü kullanarak,
    # 'comments' dizisinin içinden, _id'si bizim verdiğimiz ID ile eşleşen objeyi söküp atıyoruz.
    people_collection.update_one(
        {'name': kisi_adi},
        {'$pull': {'comments': {'_id': yorum_id_obj}}}
    )

    # İşlem bittikten sonra kullanıcıyı profil sayfasına geri yönlendiriyoruz.
    return redirect(url_for('kisi_profili', kisi_adi=kisi_adi))


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    #Eğer admin zaten giriş yapmışsa ve tekrar bu sayfaya gelirse, ana sayfaya yönlendir.
    if 'is_admin' in session and session['is_admin']:
        return redirect(url_for('home'))

    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'Kkirca123*':
            session['is_admin'] = True
            return redirect(url_for('home'))
        else:
            return "Hatalı şifre!", 401
    
    return render_template('admin_login.html')
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