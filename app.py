from flask import Flask, render_template

#Flask uygulamamızı oluşturuyoruz.
app = Flask(__name__)

#Ana sayfa rotasını tanımlıyoruz.
@app.route('/')
def home():
    #Flask, bu dosyayı otomatik olarak 'templates' klasöründe arayacak.
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)