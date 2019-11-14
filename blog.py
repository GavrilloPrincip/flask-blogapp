from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "login" in session:
            return f(*args, **kwargs)
        else:
            flash("Önce giriş yapmalısınız","danger")
            return redirect(url_for("login"))
    return decorated_function

class RegisterForm(Form):
    name = StringField("İsim Soyisim", validators=[validators.Length(min = 4, max = 20), validators.DataRequired(message="boş bırakamazsın")])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 5,max = 25)])
    email = StringField("E-Mail",validators=[validators.Email(message="gerçek bir e-mail giriniz")])
    password = PasswordField("Parola:", validators=[validators.DataRequired(message="Boş bırakamazsınız"),validators.Length(max=10), validators.EqualTo(fieldname = "confirm", message="Parolanız eşleşmiyor")])
    confirm = PasswordField("Parola doğrula")

class loginForm(Form):
    username = StringField("KUllanıcı Adı")
    password = PasswordField("Şifreniz")

class addart(Form):
    title = StringField("Title:", validators=[validators.DataRequired(message="boş bırakamazsınız")])
    content = TextAreaField("Content:", validators=[validators.Length(min=10,max=300), validators.DataRequired(message="boş bırakamazsınız")])

app = Flask(__name__)
app.secret_key = "abc"


app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "blog" 
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

@app.route("/")
def index():
    liste = [
        {"id":1, "title":"Deneme1", "content":"Deneme1 içerik"},
        {"id":2, "title":"Deneme2", "content":"Deneme2 içerik"},
        {"id":3, "title":"Deneme3", "content":"Deneme3 içerik"}
        ]
    return render_template("home.html", liste = liste)

@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    result = cursor.execute("select * from articles")
    if result > 0:
        result = cursor.fetchall()
        return render_template("articles.html", result = result)
    else:
        return render_template("articles.html")


@app.route("/login",methods = ["GET", "POST"])
def login():
    form = loginForm(request.form)
    if request.method == "POST":
        cursor = mysql.connection.cursor()
        result = cursor.execute("select password from users where username = %s",(form.username.data,))
        if result > 0:
            real_password = cursor.fetchone()["password"]
            if sha256_crypt.verify(form.password.data, real_password):
                flash("Giriş başarılı bloğa hoşgeldiniz","success")
                session["login"] = True
                session["user"] = form.username.data
                return redirect(url_for("index"))
        else:
            flash("Bilgilerinizi hatalı girdiniz!","danger")
            return redirect(url_for("login"))
    return render_template("login.html",form = form)

    


@app.route("/register", methods = ["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
        
        cursor = mysql.connection.cursor()
        cursor.execute("insert into users(name, email, username, password) values(%s, %s, %s, %s)",(name, email, username, password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarıyla Kayıt oldunuz..","success")
        return redirect(url_for("login"))

    else:
        return render_template("register.html", form = form)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    result = cursor.execute("select * from articles where author = %s",(session["user"],))
    if result > 0:
        result = cursor.fetchall()
        return render_template("dashboard.html",result = result)
    return render_template("dashboard.html")


@app.route("/addArticle", methods=["GET", "POST"])
@login_required
def addarticle():
    form = addart(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        cursor.execute("insert into articles(title, author, content) values(%s, %s, %s)",(title, session["user"], content))
        mysql.connection.commit()
        cursor.close()
        flash("Makaleniz oluşturuldu","success")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html", form= form)

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    result = cursor.execute("select * from articles where id=%s and author = %s",(id,session["user"]))
    if result > 0:
        cursor.execute("delete from articles where id= %s",(id,))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("dashboard"))
    else:
        flash("böyle bir makale bulunamadı","danger")
        return redirect(url_for("dashboard"))

@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    result = cursor.execute("select * from articles where id = %s",(id,))
    if result > 0:
        result = cursor.fetchone()
        return render_template("article.html",result = result)
    else:
        flash("böyle bir makale bulunamadı","danger")
        return redirect(url_for("dashboard"))

@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def edit(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        result = cursor.execute("select * from articles where id =%s and author = %s",(id, session["user"]))
        if result > 0 :
            result = cursor.fetchone()
            form = addart()
            form.title.data = result["title"]
            form.content.data = result["content"]
            return render_template("update.html",form = form)
    else:
        cursor = mysql.connection.cursor()
        form = addart(request.form)
        newtitle = form.title.data
        newcontent = form.content.data
        cursor.execute("update articles set title = %s, content = %s where id = %s",(newtitle, newcontent, id))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("dashboard"))

@app.route("/search", methods = ["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        result = cursor.execute("select * from articles where title like '"+"%"+keyword+"%'")
        if result == 0:
            flash("aranan kelimeye uygun makale bulunamadı","warning")
            return redirect(url_for("articles"))
        else:
            result = cursor.fetchall()
            return render_template("articles.html", result = result)

if __name__ == "__main__":
    app.run(debug=True)


