import sqlite3

from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form ,StringField ,TextAreaField,PasswordField,validators,form,ValidationError
from passlib.hash import sha256_crypt
import MySQLdb
from functools import  wraps





app = Flask(__name__)  # büyük flask olucak
app.secret_key = "yunusbaba"   #SECRET KEY YAPMAZSAK FLSH MESAJLARI CALIŞMAZ
#burada Flask ile MySQL arasındaki ilişkiyi kurmuş olduk.

app.config["MYSQL_HOST"]= "localhost"
app.config["MYSQL_USER"]= "root"
app.config["MYSQL_PASSWORD"]= ""
app.config["MYSQL_DB"]= "ybblog"
app.config['MYSQL_CURSORCLASS'] = "DictCursor"  #bu kod imleç oluşturuyor ve list ,dict,tuple üstünde gezmemizi sağlıyor.

mysql = MySQL(app)  #obje oluşturduk .Çünkü veritabnanında işimize lazım olucak.









#YUKARIDAKİ İŞLEMLERİ YAPTIGIMIZDA MYSQL ile FLASK artık birbirine baglanmış oldu.

#Regıster sınıfını Form dan oluşturucaz
class Regıster(Form):
    name = StringField("Name and surname:", validators=[validators.length(min=3,max=35),validators.DataRequired()])   #DataRequired zrunlu doldurulması lazım
    userName =StringField("UserName:",validators=[validators.length(min=5,max=30),validators.DataRequired()])
    email = StringField('Email Address', [validators.Length(min=6, max=35),validators.Email(message="lütfen geçerli bir email giriniz")])
    password = PasswordField("Password:",validators=[
        validators.DataRequired(message="parolayı giriniz"),
        validators.length(min=5,max=15),
        validators.EqualTo(fieldname="confirm",message="Lütfen geçerli bir parola giriniz"),
    ])
    confirm= PasswordField("Password:",validators=[validators.DataRequired()])



#DECORATOR KULLANIMI for ALL CODE
# Decorator ın amacı session yaptıktan sonra sayfalra giriş izni vermesi

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Lütfen görüntülemek için giriş yapınız...","danger")
            return  redirect(url_for("Logın"))
    return decorated_function


class LogınForm(Form):
    userName= StringField("UserName:",validators=[validators.DataRequired(message="Lütfen kullanıcı adınızı giriniz")])
    password = PasswordField("Password:",validators=[validators.DataRequired(message="Lütfen şifrenizi giriniz")])



@app.route("/dashboard")  #burada decorator kullanıyoz
@login_required  #Bunu yapmamızın nedeni  linkte direk girşişi önlemek
def Dashboard():
    cursor = mysql.connection.cursor()#bağlantı sağladık
    sorgu = "SELECT * FROM article WHERE  AUTHOR = %s "

    result = cursor.execute(sorgu,( session["userName"],))

    if result >0:
        articles =cursor.fetchall()
        cursor.close()

        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")



#SEARH URl
@app.route("/search",methods=["GET","POST"])
@login_required  # giriş izni vermicez
def Search():
    if request.method =="GET":
        return  redirect(url_for("shows")) #sorguda methods get ise direk ana sayfaya döndürdük
    else:
        keyword = request.form.get("keyword") #burada yaptığımız işlem arama çubuğu içindeki yazıyı alarak sonucuna götürmek

        cursor = mysql.connection.cursor() #veritabanı bağlantısı yaptık

        sorgu = "SELECT * FROM article WHERE TITLE LIKE '%" + keyword + "%'"  #burada article.html sayfasında inputa name ekliyerek sorguda kullandık
        # LIKE nasıl kullanılır burda onu öğrendik

        result = cursor.execute(sorgu)

        if result == 0:
            flash("There is not that artıcle","warning")
            return  redirect(url_for("Artıcle"))
        else:

            articles = cursor.fetchall()
            return render_template("article.html",articles=articles)








@app.route("/")
def shows():

    return render_template("index.html")

@app.route("/about")
@login_required
def About():
    return render_template("about.html")

@app.route("/register", methods = ["GET","POST"])
def register():

    form = Regıster(request.form)

    if request.method == "POST" and form.validate(): #form.validate kurallar doğru ise demek devam et diyor
        fullname = form.name.data
        userName = form.userName.data
        email = form.email.data
        password= sha256_crypt.encrypt(form.password.data)  # şifreyi encrypt ettik istersek gösteredebiliriz


        cursor =mysql.connection.cursor() #cursor imleç gibi düşün gezmek için kullanılır

        sorgu = "INSERT INTO kullanıcı(name,email,username,password) VALUES(%s,%s,%s,%s)"  #%s diyerek execute içindekileri buraya yerleştirdik

        cursor.execute(sorgu,(fullname,email,userName,password))  #values un içindek yerler bunları yerleştirdedik

        mysql.connection.commit()  #commit ise tekrardan güncelle

        cursor.close() #veritabanını kapat diyor

        flash("Register is succesfull", "success")
        return redirect(url_for("Logın")) #herharnagi bir sayfaya gitmek için redirect koullanıyoz



    else:
        return render_template("kayıt.html",form=form)

@app.route("/login",methods =["GET","POST"])
def Logın():
    form = LogınForm(request.form)

    if request.method =="POST":
        username1= form.userName.data
        password1 = form.password.data

        cursor =mysql.connection.cursor()  #Burada mysql ile bağlantı sağladık ve veritabanınıa girdik
        sormak = "SELECT * FROM kullanıcı WHERE USERNAME =%s"  # burada kullancı tablosundan ismi username1 olanı al dedik

        result = cursor.execute(sormak,(username1,)) #VİRGÜL KOYDUK TEK ELEMANLI DEMET

        if result>0:
            data = cursor.fetchone()  #kullanıcının tum bilgilerini aldık
            real_password = data["PASSWORD"]  #burada kullanıcıtablosundan bilgiyi çektik

            if sha256_crypt.verify(password1,real_password):
                flash("Giriş başarılı...","success")
                #SESSION I AYARLADIK BURDA
                session["logged_in"] =True

                session["userName"]=username1



                return redirect(url_for("shows"))
            else:
                flash("Lütfen kullanıcı adını ve şifreyi kontrol ediniz","danger")
                return redirect(url_for("Logın")) #yanlış oldugu çin aynı sayfaya döndük




        else:
            flash("Lütfen kullanıcı adını ve şifreyi kontrol ediniz","danger")
            return  redirect(url_for("Logın"))

    else:

        return render_template("login.html",form = form)

#Logout için yazıyoz
@app.route("/logout")
@login_required
def LogOut():
    session.clear()
    return redirect(url_for("Logın"))

#AddArtıcle class
class AddArtıcleForm(Form):
    tıtle = StringField("TITLE:",validators=[validators.DataRequired(message="Lütfen istenilen bilgiyi giriniz.")])
    content = TextAreaField("CONTENT:",validators=[validators.DataRequired(message="Lütfen istenilen bilgiyi giriniz.")])



#AddArtıcle
@app.route("/addarticle",methods=["GET","POST"])
@login_required
def AddArtıcle():

    form = AddArtıcleForm(request.form)

    if request.method =="POST" and form.validate():
        tıtle1 = form.tıtle.data
        content1 = form.content.data

        cursor = mysql.connection.cursor()

        sorgula = "INSERT INTO article(TITLE,AUTHOR,CONTENT) VALUES(%s,%s,%s)"

        cursor.execute(sorgula,(tıtle1,session["userName"],content1))
        mysql.connection.commit()
        cursor.close()

        flash("Article added ","success")

        return redirect(url_for("Dashboard"))





    else:
        return render_template("addarticle.html",form=form)



# Delete Artıcle
@app.route("/delete/<string:ID>")
@login_required
def Delete(ID):
    cursor = mysql.connection.cursor()
    sorgu = "DELETE FROM article WHERE ID = %s" #burda sorgu yaptık veritabanından ve o ıd Yİ SİL DEDİK

    result = cursor.execute(sorgu,(ID,))

    if result>0:
        mysql.connection.commit()# burada veritabanını değiştirdik eski haliyle
        cursor.close()
        flash("Artıcle deleted", "success")
        return redirect(url_for("shows"))

    else:
        flash("NOT Deleted this ID","warning")
        return render_template("detail.html")


#ArtıclepageShow
@app.route("/makaleler")
@login_required
def Artıcle():

    cursor= mysql.connection.cursor()  #imleç oluşturudk
    sorgu ="SELECT * FROM article"  #bütün blgileri select yaparak aldık
    result= cursor.execute(sorgu) #burda uygula dedik


    if result>0:
        articles= cursor.fetchall()  #tüm bilgileri alıp tutuyoduk
        cursor.close()
        return render_template("article.html",articles=articles)


    else:

        return render_template("article.html")

#Artıcle Update
@app.route("/edit/<string:ID>", methods = ["GET","POST"]) #burada dinamik url kullandık ona göre sayfaya yönlendirdik.
@login_required  #BURADA  giriş yapmadan sayfaya yönlendirmemek için bu işlemi kullandık.
def update(ID):
    if request.method =="GET":
        cursor = mysql.connection.cursor()  #veritabanıyla bağlantı kurduk.

        sorgu = "SELECT * FROM article where AUTHOR =%s  and  ID =%s"

        result = cursor.execute(sorgu,(session["userName"],ID))

        if result==0:

            flash("ID olmadığı için güncelleme yapılamaz", "danger")
            return redirect(url_for("shows"))

        else:
            article = cursor.fetchone()  # burada articlea aldıgımız değeri atadık
            form = AddArtıcleForm()  #addartıcle formdan bılgılerı aldık.

            form.tıtle.data = article["TITLE"]
            form.content.data = article["CONTENT"]
            return render_template("update.html", form=form)

    else:
        form = AddArtıcleForm(request.form)

        newtıtle = form.tıtle.data
        newcontent=form.content.data



        sorgula = "Update article Set TITLE=%s,CONTENT=%s Where ID = %s"

        cursor=mysql.connection.cursor()  #burda tekrar bunu kullanma nedeni bağlantı kurup güncellemek


        cursor.execute(sorgula,(newtıtle,newcontent,ID))

        mysql.connection.commit()  #burda veritabanında değişiklikleri kaydettik

        flash("Artıcle was UPDATE","success")

        return redirect(url_for("Dashboard"))


#Artıcle OTHER PAGE
@app.route("/article/<string:ID>")  #Bız burada Dınamık Url kullandık ve dınamık url de Strıng olarak alıyoruz
@login_required
def Detaıl(ID):

    cursor= mysql.connection.cursor()

    sorgu ="SELECT * FROM article WHERE ID = %s"


    result = cursor.execute(sorgu,(ID,))
    #biz burda sorgularken sonuç 0 mı değimi diye bakıyoz

    if result >0:
        article =cursor.fetchone()
        cursor.close()
        return render_template("detail.html",article=article)

    else:
        return render_template("detail.html")










if __name__ == "__main__":
    app.run(debug=True)


