
from datetime import datetime
from flask import redirect,url_for
from flask import Flask,json
from flask import render_template
from flask import request
import matplotlib.pyplot as plt
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api 
from flask_restful import fields, marshal_with
from flask_restful import reqparse
from flask import current_app as app1
from sqlalchemy import ForeignKey
from validation import BusinessValidationError
from werkzeug.exceptions import HTTPException
from flask import abort, json
from flask import Flask, render_template, redirect, request, session
from flask_session import Session
from flask_cors import CORS

 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.sqlite3' 
db = SQLAlchemy()
app.jinja_env.add_extension('jinja2.ext.do')
db.init_app(app)
app.app_context().push()
api = Api(app)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
CORS(app)
create_user_parser = reqparse.RequestParser()
create_user_parser.add_argument("username")
create_user_parser.add_argument("listname")
create_user_parser.add_argument("description")

class ListAPI(Resource):
    def get(self,username,listname):
        user_id = db.session.query(user).filter(user.name==username).first()
        if not user_id:
            raise BusinessValidationError(status_code=400,error_code='U001',error_message="User not found")
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        list_name = None
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).filter(lists.listname==listname).first()
            if list_query is not None:
                list_name = list_query.listname
                break

        db.session.close()
        if list_name:
            return {'listname':list_name,'description':list_query.description}
        else:
            raise BusinessValidationError(status_code=400,error_code='LI001',error_message="List not found")
    
    def delete(self,username,listname):
        user_id = db.session.query(user).filter(user.name==username).first()
        if not user_id:
            return "User not found", 400
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).filter(lists.listname==listname).first()
            if list_query is not None:
                break

        db.session.close()
        if list_query:
            relation_listid = db.session.query(relation).filter(relation.list_id==list_query.list_id).first()
            cards = db.session.query(card).filter(card.list_id==list_query.list_id).all()
            for i in cards:
                db.session.delete(i)
            db.session.delete(relation_listid)
            db.session.delete(list_query)
        else:
            return "List no found", 400
        db.session.commit()
        return "successfully deleted", 200

    def put(self,username,listname):

        user_id = db.session.query(user).filter(user.name==username).first()
        if user_id is None:
            raise BusinessValidationError(status_code=400,error_code="U001",error_message="User not found")
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).filter(lists.listname==listname).first()
            if list_query is not None:
                break
        if list_query is None:
            raise BusinessValidationError(status_code=400,error_code="LI002",error_message="List not found")
        args = create_user_parser.parse_args()
        new_listname = args.get("listname",None)
        new_description = args.get("description",None)
        if not new_listname:
            raise BusinessValidationError(status_code=400,error_code="LI003",error_message="List name required")
        db.session.query(lists).filter(lists.list_id==list_query.list_id).update({'listname':new_listname,'description':new_description})
        db.session.commit()
        return "Updated successfully", 200


    def post(self):
        args = create_user_parser.parse_args()
        username = args.get("username",None)
        listname = args.get("listname",None)
        description = args.get("description",None)
        if not username:
            raise BusinessValidationError(status_code=400,error_code="U002",error_message="Username is required")
        query = db.session.query(user).filter(user.name==username).first()
        if not query:
            raise BusinessValidationError(status_code=400,error_code="U001",error_message="User not found")
        relation_query = db.session.query(relation).filter(relation.user_id==query.id).all()
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).filter(lists.listname==listname).first()
            if list_query is not None:
                break
        if list_query:        
            raise BusinessValidationError(status_code=400,error_code="LI003",error_message="List already exist")
        else:
            list_val = lists(listname=listname,description=description)
            db.session.add(list_val)
            listid = db.session.query(lists).filter(lists.listname==listname).filter(lists.description==description).first()
            relation_val = relation(user_id=query.id,list_id=listid.list_id)
            db.session.add(relation_val)
            db.session.commit()
            return "Success", 200

class CardAPI(Resource):
    def get(self,username,listname,cardname):
        user_id = db.session.query(user).filter(user.name==username).first()
        if user_id is None:
            raise BusinessValidationError(status_code=404,error_code="U001",error_message="User not found")
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).filter(lists.listname==listname).first()
            if list_query is not None:
                break
        if list_query is None:
            raise BusinessValidationError(status_code=404,error_code="LI002",error_message="List not found")
        card_query = db.session.query(card).filter(card.list_id==list_query.list_id).filter(card.name==cardname).first()
        if not card_query:
            raise BusinessValidationError(status_code=404,error_code="CA001",error_message="Card not found")
        js = {'card_id':card_query.card_id,'name':card_query.name,'decription':card_query.description,'parent_list':list_query.listname,'deadline':card_query.deadline,"status":card_query.status}
        return js, 200


api.add_resource(ListAPI,"/api/list","/api/<string:username>/<string:listname>")
api.add_resource(CardAPI,"/api/card","/api/<string:username>/<string:listname>/<string:cardname>")

class user(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String,unique=True)

class card(db.Model):
    __tablename__ = 'card'
    card_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    name = db.Column(db.String)
    description = db.Column(db.String)
    list_id = db.Column(db.Integer,ForeignKey('lists.list_id',ondelete='CASCADE'))
    deadline = db.Column(db.String)
    status = db.Column(db.String)
    completed_on = db.Column(db.String)

class relation(db.Model):
    __tablename__ = 'relation'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    list_id = db.Column(db.Integer,ForeignKey('lists.list_id',ondelete='CASCADE'))
    user_id = db.Column(db.Integer,ForeignKey('user.id'))

class lists(db.Model):
    __tablename__ = 'lists'
    list_id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    listname = db.Column(db.String)
    description = db.Column(db.String)
    child = db.relationship(card, backref="parent", passive_deletes=True)
    child2 = db.relationship(relation,backref="parent", passive_deletes=True)

@app.route('/favicon.ico')
def favicon():
    pass


@app.route("/",methods=["POST", "GET"])
def board():
    if not session.get("name"):
        print(session.get("name"))
        return redirect("/login")
    elif request.method=='GET' and session.get('name'):
        curr_date = str(datetime.now())
        curr_date = curr_date[:10]
        user_id = db.session.query(user).filter(user.name==session.get('name')).first()
        exists = db.session.query(relation).filter(relation.user_id==user_id.id).first() is not None  
        if not exists:
            return render_template('board1.html',result=exists,name=session.get('name'))
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        lst = []
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).first()
            lst.append(list_query)
        lst2 = []
        for j in lst:
            card_query = db.session.query(card).filter(card.list_id==j.list_id).all()
            for k in card_query:
                lst2.append(k)
        return render_template('board1.html',result=exists,name=session.get('name'),lst=lst,lst2=lst2,date=curr_date)


@app.route("/login", methods=["POST", "GET"])
def login():
    exists = db.session.query(user).filter(user.name==session.get('name')).first() is not None
    if request.method == "POST" and exists:
        session["name"] = request.form["name"]
        user_value = user(name=session['name'])
        db.session.add(user_value)
        db.session.commit()
        return redirect("/")
    elif request.method=="POST" and not exists:
        session["name"] = request.form["name"]
        return redirect('/')
    return render_template("home.html")


@app.route("/home",methods=['GET','POST'])
def home():
    if request.method=="GET":
        return render_template('home.html',status=10)
    elif request.method=="POST":
        global user_name
        global result
        user_name = request.form['name']
        query = db.session.query(user).filter(user.name==user_name)
        if query.first() is None:
            print('if part')
            result = 'not_exist'
            return redirect(url_for('board'))
        else:
            result = 'exist'
            return redirect("/board")

@app.route("/addlist",methods=['GET','POST'])
def addlist():
    if not session.get("name"):
        return redirect("/login")
    elif request.method=="GET" and session.get('name'):
        return render_template("addlist.html",name = session.get('name'))
    elif request.method=="POST":
        name,desp = request.form['name'],request.form['description']
        lists_value = lists(listname=name,description=desp)
        db.session.add(lists_value)
        userid = db.session.query(user).filter(user.name==session.get('name')).first()
        listid = db.session.query(lists).filter(lists.listname==name).filter(lists.description==desp).first()
        relation_value = relation(list_id=listid.list_id,user_id=userid.id)
        db.session.add(relation_value)
        db.session.commit()
        return redirect('/')

@app.route("/addcard",methods=['GET','POST'])
def addcard():
    if not session.get("name"):
        return redirect("/login")
    if request.method=='GET' and session.get('name'):
        user_id = db.session.query(user).filter(user.name==session.get('name')).first()
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        lst = []
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).first()
            lst.append(list_query)
        return render_template('addcard.html',name = session.get('name'),lists=lst)
    elif request.method=='POST':
        cardname = request.form['cardname']
        desp = request.form['description']
        parent_list = request.form['Parent list']
        deadline = request.form['deadline']
        try:
            status = request.form['checkbox']
            status = 'Completed'
        except:
            status = 'Pending'
        if status == 'Completed':
            curr_date = str(datetime.now())
            completed_on = curr_date[:10]
        else:
            completed_on = None
        user_id = db.session.query(user).filter(user.name==session.get('name')).first()
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).filter(lists.listname==parent_list).first()
            if list_query is not None:
                break
        card_val = card(name=cardname,description=desp,list_id=list_query.list_id,deadline=deadline,status=status,completed_on=completed_on)
        db.session.add(card_val)
        db.session.commit()
        return redirect('/')

@app.route("/<string:listname>",methods=["GET","POST"])
def editlist(listname):
    if request.method=="GET" and session.get('name'):
        user_id = db.session.query(user).filter(user.name==session.get('name')).first()
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).filter(lists.listname==listname).first()
            if list_query is not None:
                break
        return render_template('editlist.html',name=session.get('name'),listname=listname,description=list_query.description)
    elif request.method=='POST':
        user_id = db.session.query(user).filter(user.name==session.get('name')).first()
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).filter(lists.listname==listname).first()
            if list_query is not None:
                break
        name,desp = request.form['name'],request.form['description']
        db.session.query(lists).filter(lists.list_id==list_query.list_id).update({'listname':name,'description':desp})
        db.session.commit()
        return redirect('/')

@app.route('/<string:listname>/<string:cardname>',methods=['GET','POST'])
def editcard(listname,cardname):
    if request.method=='GET' and session.get('name'):
        user_id = db.session.query(user).filter(user.name==session.get('name')).first()
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).filter(lists.listname==listname).first()
            if list_query is not None:
                break 
        card_query = db.session.query(card).filter(card.list_id==list_query.list_id).first()
        lst = []
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).first()
            lst.append(list_query)
        return render_template('editcard.html',name=session.get('name'),card_name=cardname,description=card_query.description,parent_list=listname,deadline=card_query.deadline,status=card_query.status,lists=lst)
    elif request.method=='POST':
        card_name = request.form['cardname']
        desp = request.form['description']
        parent_list = request.form['Parent list']
        deadline = request.form['deadline']
        delete_card = request.form['delete_card']
        print(request.form)
        try:
            status = request.form['checkbox']
            status = 'Completed'
            curr_date = str(datetime.now())
            completed_on = curr_date[:10]            
        except:
            completed_on = None
            status = 'Pending'
        user_id = db.session.query(user).filter(user.name==session.get('name')).first()
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).filter(lists.listname==listname).first()
            if list_query is not None:
                break 
        for j in relation_query:
            list_query1 = db.session.query(lists).filter(lists.list_id==j.list_id).filter(lists.listname==parent_list).first()
            if list_query1 is not None:
                break
        if request.form['delete_card'] == 'OK' :
            card_val = db.session.query(card).filter(card.name==cardname).filter(card.list_id==list_query.list_id).first()
            db.session.delete(card_val)
        else:        
            db.session.query(card).filter(card.name==cardname).filter(card.list_id==list_query.list_id).update({'name':card_name,'description':desp,'list_id':list_query1.list_id,'deadline':deadline,'status':status,'completed_on':completed_on})
        db.session.commit()
        return redirect('/')            
@app.route('/delete/<string:listname>/<string:cardname>',methods=['GET','POST'])
def delete(listname,cardname):
    if request.method=="GET":
        user_id = db.session.query(user).filter(user.name==session.get('name')).first()
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).filter(lists.listname==listname).first()
            if list_query is not None:
                break 
        card_val = db.session.query(card).filter(card.name==cardname).filter(card.list_id==list_query.list_id).first()
        db.session.delete(card_val)
        db.session.commit()
        return redirect('/')        

@app.route('/delete_list/<string:listname>',methods=['GET','POST'])
def delete_list(listname):
    if request.method=='GET':
        user_id = db.session.query(user).filter(user.name==session.get('name')).first()
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()        
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).filter(lists.listname==listname).first()
            if list_query is not None:
                break
        relation_val = db.session.query(relation).filter(relation.list_id==list_query.list_id).filter(relation.user_id==user_id.id).first()
        card_val = db.session.query(card).filter(card.list_id==list_query.list_id).all()
        for i in card_val:
            db.session.delete(i)
        db.session.delete(list_query)
        db.session.delete(relation_val)
        db.session.commit()
        return redirect('/')

@app.route("/logout")
def logout():
    session["name"] = None
    return redirect("/login")


@app.route('/styles')
def styles():
    return render_template('styles.css')

@app.route('/summary')
def summary():
    curr_date = str(datetime.now())
    curr_date = curr_date[:10]
    cards = card.query.all()
    plt.switch_backend('agg')
    if cards is not None:
        user_id = db.session.query(user).filter(user.name==session.get('name')).first()
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        lst3 = []
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).first()
            lst3.append(list_query)
        lst4 = {}
        i = 0
        for j in lst3:
            x = []
            y = []
            card_query = db.session.query(card).filter(card.list_id==j.list_id).filter(card.status=='Completed').all()
            if card_query != []:
                print(card_query)
                for card_q in card_query:
                    if card_q.completed_on not in x:
                        date = str(card_q.completed_on)
                        datem = datetime.strptime(date, "%Y-%m-%d")  
                        month_num = str(datem.month)
                        datetime_object = datetime.strptime(month_num, "%m")
                        full_month_name = datetime_object.strftime("%B")
                        full_date = str(datem.day) + ' ' + str(full_month_name)
                        x.append(full_date)
                        card_query1 = db.session.query(card).filter(card.list_id==j.list_id).filter(card.completed_on==card_q.completed_on).count()
                        y.append(card_query1)
                print(x)
                print(y)
                plt.figure(figsize=(5,3))
                plt.bar(x,y)
                plt.title(j.listname)
                plt.ylabel('Tasks complted')
                fig_name = 'figure' +str(i)+'.png'
                plt.savefig("static/%s" %(fig_name))
                lst4[j.list_id] = [fig_name]
                i+=1
                tot_tasks = db.session.query(card).filter(card.list_id==j.list_id).count()
                com_tasks = sum(y)
                pen_tasks = db.session.query(card).filter(card.list_id==j.list_id).filter(card.status=='Pending').filter(card.deadline>=curr_date).count()
                dead_tasks = db.session.query(card).filter(card.list_id==j.list_id).filter(card.status=='Pending').filter(card.deadline<curr_date).count()
                lst4[j.list_id] = lst4[j.list_id] + [tot_tasks,com_tasks,pen_tasks,dead_tasks]
                print(lst4)
            else:
                tot_tasks = db.session.query(card).filter(card.list_id==j.list_id).count()
                com_tasks = card_query = db.session.query(card).filter(card.list_id==j.list_id).filter(card.status=='Completed').count()
                pen_tasks = db.session.query(card).filter(card.list_id==j.list_id).filter(card.status=='Pending').filter(card.deadline>=curr_date).count()
                dead_tasks = db.session.query(card).filter(card.list_id==j.list_id).filter(card.status=='Pending').filter(card.deadline<curr_date).count()
                lst4[j.list_id] = [tot_tasks,com_tasks,pen_tasks,dead_tasks]
                i += 1
        user_id = db.session.query(user).filter(user.name==session.get('name')).first()
        exists = db.session.query(relation).filter(relation.user_id==user_id.id).first() is not None  
        if not exists:
            return render_template('board1.html',result=exists,name=session.get('name'))
        relation_query = db.session.query(relation).filter(relation.user_id==user_id.id).all()
        lst = []
        for i in relation_query:
            list_query = db.session.query(lists).filter(lists.list_id==i.list_id).first()
            lst.append(list_query)
        lst2 = []
        for j in lst:
            card_query = db.session.query(card).filter(card.list_id==j.list_id).all()
            for k in card_query:
                lst2.append(k)
        return render_template('board1.html',result=exists,name=session.get('name'),lst=lst,lst2=lst2,date=curr_date,plot_dict=lst4)

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response


if __name__=='__main__':
    app.run(debug=True)