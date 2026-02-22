from flask import Flask, render_template, redirect, request, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime , timedelta
#orm means object relational mapping between python and database
import seaborn as sns
import matplotlib
matplotlib.use('Agg')  # Corrected here
import matplotlib.pyplot as plt



curr_dir = os.path.dirname(os.path.abspath(__file__))

# Initialize Flask app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///quizmaster.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "PROJECT_SECRET_KEY"
app.config["UPLOAD_FOLDER"]= os.path.join(curr_dir, "static", "imgs")

# Initialize database
db = SQLAlchemy(app)

# Models
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    qualification = db.Column(db.String(120), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    scores = db.relationship('Scores', back_populates='user', cascade='all, delete-orphan')

class Subjects(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(120), nullable=False)
    chapters = db.relationship('Chapters', back_populates='subject', cascade='all, delete-orphan')

class Chapters(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(120), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    subject = db.relationship('Subjects', back_populates='chapters')
    quizzes = db.relationship('Quizzes', back_populates='chapter', cascade='all, delete-orphan')

class Quizzes(db.Model):
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    date_of_quiz = db.Column(db.Date, nullable=False)
    time_duration = db.Column(db.Integer, nullable=False)
    remarks = db.Column(db.String(120), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey("chapters.id"), nullable=False)
    chapter = db.relationship('Chapters', back_populates='quizzes')
    questions = db.relationship('Questions', back_populates='quiz', cascade='all, delete-orphan')
    scores = db.relationship('Scores', back_populates='quiz', cascade='all, delete-orphan')

class Questions(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(120), nullable=False)
    option_1 = db.Column(db.String(120), nullable=False)
    option_2 = db.Column(db.String(120), nullable=False)
    option_3 = db.Column(db.String(120), nullable=False)
    option_4 = db.Column(db.String(120), nullable=False)
    correct_answer = db.Column(db.Integer, nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    quiz = db.relationship('Quizzes', back_populates='questions')

class Scores(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id"), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_scored = db.Column(db.Integer, nullable=False)
    user = db.relationship('Users', back_populates='scores')  
    quiz = db.relationship('Quizzes', back_populates='scores')

# Helper function to create admin user
def create_admin():
    admin_user = Users.query.filter_by(email="admin@gmail.com").first()
    if not admin_user:
        admin = Users(
            name="Admin",
            email="admin@gmail.com",
            password="0000",
            qualification="BS Data Science, IIT Madras",
            dob=datetime(2000, 1, 1).date(),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

# Routes
@app.route("/")
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Users.query.filter_by(email=email).first()
        
        if user and user.password == password:
            session['admin' if user.is_admin else 'user'] = user.id
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        
        flash('Invalid credentials!', 'danger')
    
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if 'admin' in session:
        subjects = Subjects.query.all()
        scores = Scores.query.order_by(Scores.timestamp.desc()).limit(50).all()
        users_count = Users.query.filter_by(is_admin=False).count()
        quizzes_count = Quizzes.query.count()
        return render_template('admin_dashboard.html', 
                             all_subjects=subjects, 
                             scores=scores,
                             users_count=users_count,
                             quizzes_count=quizzes_count)
    return redirect(url_for('login'))


@app.route('/view_subjects/<int:subject_id>')
def view_subject(subject_id):
    if 'admin' in session:
        subject = Subjects.query.filter_by(id=subject_id).first()
        chapters = Chapters.query.filter_by(subject_id=subject_id).all()
        return render_template('view_subject.html', subject=subject, chapters=chapters)
    return redirect(url_for('login'))


@app.route('/view_chapter/<int:chapter_id>')
def view_chapter(chapter_id):
    if 'admin' in session:
        chapter = Chapters.query.filter_by(id=chapter_id).first()
        quizzes = Quizzes.query.filter_by(chapter_id=chapter_id).all()
        return render_template('view_chapter.html', chapter=chapter, quizzes=quizzes)
    return redirect(url_for('login'))


@app.route('/view_quiz/<int:quiz_id>')
def view_quiz(quiz_id):
    if 'admin' in session:
        quiz = Quizzes.query.filter_by(id=quiz_id).first()
        questions = Questions.query.filter_by(quiz_id=quiz_id).all()
        return render_template('view_quiz.html', quiz=quiz, questions=questions)
    return redirect(url_for('login'))

@app.route('/create_subject', methods=['GET', 'POST'])
def create_subject():
    if 'admin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if name and description:
            new_subject = Subjects(name=name, description=description)
            db.session.add(new_subject)
            db.session.commit()
            flash("Subject created successfully!", "success")
            return redirect(url_for('admin_dashboard'))
        
        flash("All fields are required!", "danger")

    return render_template('create_subject.html')

@app.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
def edit_subject(subject_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    subject = Subjects.query.get(subject_id)
    if not subject:
        flash("Subject not found!", "danger")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        subject.name = request.form.get('name')
        subject.description = request.form.get('description')

        if subject.name and subject.description:
            db.session.commit()
            flash("Subject updated successfully!", "success")
            return redirect(url_for('admin_dashboard'))

        flash("All fields are required!", "danger")

    return render_template('edit_subject.html', subject=subject)

@app.route('/delete_subject/<int:subject_id>', methods=['GET', 'POST'])
def delete_subject(subject_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    subject = Subjects.query.get(subject_id)
    # if request.method == 'POST':
    db.session.delete(subject)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))
    flash("Subject deleted successfully!", "success")
    
    return redirect(url_for('admin_dashboard'))


# CRUD : Create Read Update Delete : Chapter
@app.route('/create_chapter/<int:subject_id>', methods=['GET', 'POST'])
def create_chapter(subject_id):
    if 'admin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if name and description:
            new_chapter = Chapters(name=name, description=description, subject_id=subject_id)
            db.session.add(new_chapter)
            db.session.commit()
            return redirect(url_for('view_subject', subject_id=subject_id))
            flash("Subject created successfully!", "success")
            return redirect(url_for('admin_dashboard'))
        
        flash("All fields are required!", "danger")

    return render_template('create_chapter.html', subject_id=subject_id)


@app.route('/edit_chapter/<int:chapter_id>', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    if 'admin' in session:
        chapter = Chapters.query.filter_by(id=chapter_id).first()
        if not chapter:
            return redirect(url_for('view_subject', subject_id=chapter.Subject_id))
        
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            chapter.name = name
            chapter.description = description
            db.session.commit()
            return redirect(url_for('view_subject', subject_id=chapter.subject_id))
        else:
            return render_template('edit_chapter.html', chapter=chapter)
    return redirect('/login')

    


@app.route('/delete_chapter/<int:chapter_id>', methods = ['GET','POST'])
def delete_chapter(chapter_id):
    if 'admin' in session:
        chapter = Chapter.query.filter_by(id=chapter_id).first()
        if not chapter:
             return redirect('/admin')
        
        if request.method == 'POST':
            Subject_id = chapter.Subject_id
            db.session.delete(chapter)
            db.session.commit()
            return redirect(url_for('view_subject', subject_id=chapter.Subject_id))
        return render_template('del_confirm.html', chapter=chapter)
    return redirect('/login')



# CRUD : Create Read Update Delete : Quizzes

@app.route('/create_quiz/<int:chapter_id>', methods = ['GET', 'POST'])
def create_quiz(chapter_id):
    if 'admin' in session:
            if request.method == 'POST':
                name = request.form['name']
                date_of_quiz = request.form['date_of_quiz']
                time_duration = request.form['time_duration']
                remarks = request.form['remarks']

                doq = datetime.strptime(date_of_quiz, '%Y-%m-%d').date()

                new_quiz = Quizzes(name=name, date_of_quiz=doq, time_duration=time_duration, remarks=remarks, chapter_id=chapter_id)
                db.session.add(new_quiz)
                db.session.commit()
                flash("Quiz created successfully!", "success")
                return redirect(url_for('view_chapter', chapter_id=chapter_id))
            else:
                return render_template('create_quiz.html', chapter_id=chapter_id)
    return redirect('/login')


@app.route('/edit_quiz/<int:_id>', methods=['GET', 'POST'])
def edit_quiz(chapter_id):
    if 'admin' in session:
        if request.method == 'POST':
            name = request.form['name']
            date_of_quiz = request.form['date_of_quiz']
            time_duration = request.form['time_duration']
            remarks = request.form['remarks']

            doq = datetime.strptime(date_of_quiz, '%Y-%m-%d').date()

            new_quiz = Quizzes(name=name, date_of_quiz=doq, time_duration=time_duration, remarks=remarks, Chapters_id=chapter_id)
            db.session.add(new_quiz)
            db.session.commit()
            flash("Quiz created successfully!", "success")
            return redirect(url_for('view_chapter', chapter_id=chapter_id))
        else:
            return render_template('create_quiz.html', chapter_id=chapter_id)
    return redirect('/login')


@app.route('/delete_quiz/<int:quiz_id>', methods = ['GET','POST'])
def delete_quiz(quiz_id):
    if 'admin' in session:
        quiz = Quizzes.query.filter_by(id=quiz_id).first()
        if not quiz:
             return redirect('/admin')
        
        # if request.method == 'POST':
        chapter_id = quiz.chapter_id
        db.session.delete(quiz)
        db.session.commit()
        return redirect(url_for('view_chapter', chapter_id=chapter_id))
        # return render_template('del_confirm.html', quiz=quiz)
    return redirect('/login')
    


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        qualification = request.form['qualification']
        dob_str = request.form.get("dob")

        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            new_user = Users(name=name, email=email, password=password, qualification=qualification, dob=dob)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful!", "success")
            return redirect(url_for('login'))
        except ValueError:
            flash("Invalid date format!", "danger")

    return render_template('register.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('login'))



# CRUD : Create Read Update Delete : Question

@app.route('/create_question/<int:quiz_id>', methods = ['GET', 'POST'])
def create_question(quiz_id):
    if 'admin' in session:
            if request.method == 'POST':
                question_statement = request.form['question_statement']
                option_1 = request.form['option_1']
                option_2 = request.form['option_2']
                option_3 = request.form['option_3']
                option_4 = request.form['option_4']
                correct_option = request.form['correct_option']

                new_question = Questions(question_text=question_statement, option_1=option_1, option_2=option_2, option_3=option_3, option_4=option_4, correct_answer=correct_option, quiz_id=quiz_id)
                db.session.add(new_question)
                db.session.commit()
                flash("Question created successfully!", "success")
                return redirect(url_for('view_quiz', quiz_id=quiz_id))
            else:
                return render_template('create_question.html', quiz_id=quiz_id)
    return redirect('/login')




@app.route('/edit_question/<int:question_id>', methods = ['GET', 'POST'])
def edit_question(question_id):
    if 'admin' in session:
            question = Questions.query.filter_by(id=question_id).first()
            if request.method == 'POST':
                question_statement = request.form['question_statement']
                option_1 = request.form['option_1']
                option_2 = request.form['option_2']
                option_3 = request.form['option_3']
                option_4 = request.form['option_4']
                correct_option = request.form['correct_option']

                question.question_text = question_statement
                question.option_1 = option_1
                question.option_2 = option_2
                question.option_3 = option_3
                question.option_4 = option_4
                question.correct_answer = correct_option

                db.session.commit()
                flash("Question updated successfully!", "success")
                return redirect(url_for('view_quiz', quiz_id=question.quiz_id))
            else:
                return render_template('edit_question.html', question=question)
    return redirect('/login')



@app.route('/delete_question/<int:question_id>', methods = ['GET','POST'])
def delete_question(question_id):
    if 'admin' in session:
        question = Questions.query.filter_by(id=question_id).first()
        if not question:
             return redirect('/admin')
        
        # if request.method == 'POST':
        quiz_id = question.quiz_id
        db.session.delete(question)
        db.session.commit()
        return redirect(url_for('view_quiz', quiz_id=quiz_id))
        # return render_template('del_confirm.html', question=question)
    return redirect('/login')
                

@app.route('/user_logout')
def user_logout():
    session.pop('user')
    return redirect(url_for('login'))


#creating user dashboard for showcasing all the quizzes

@app.route('/user')
def user_dashboard():
    if 'user' in session:
        quizzes = Quizzes.query.all()
        user = Users.query.filter_by(id=session['user']).first()
        subjects_count = Subjects.query.count()
        attempted_count = Scores.query.filter_by(user_id=session['user']).count()
        return render_template('user_dashboard.html', 
                             quizzes=quizzes, 
                             user=user,
                             subjects_count=subjects_count,
                             attempted_count=attempted_count)
    return redirect('/login')



#creating start quiz routes for a particular quiz



@app.route('/start_quiz/<int:quiz_id>')
def start_quiz(quiz_id):
    if 'user' in session:
        quiz = Quizzes.query.filter_by(id=quiz_id).first()
        questions = Questions.query.filter_by(quiz_id=quiz_id).all()

        # Ensure quiz exists
        if not quiz:
            flash("Quiz not found!", "warning")
            return redirect("/user")

        # Check if quiz is expired
        if (datetime.now() - timedelta(days=1)).date() >= quiz.date_of_quiz:
            flash("This quiz is expired", "info")
            return redirect("/user")

        # Check if quiz has questions
        if not questions:
            flash("No questions found for this quiz!", "info")
            return redirect("/user")

        # Store timestamp in session
        session["timestamp"] = datetime.now().isoformat()

        return redirect(f"/quiz/{quiz_id}")

    flash("You need to log in first.", "warning")
    return redirect('/login')





@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def quiz_page(quiz_id):
    if 'user' in session:
        quiz = Quizzes.query.filter_by(id=quiz_id).first()
        questions = Questions.query.filter_by(quiz_id=quiz_id).all()
        user = Users.query.filter_by(id=session['user']).first()
        return render_template('quiz.html', quiz=quiz, questions=questions, user=user)
    return redirect('/login')



#creating route submit quiz for sumbmitted a quiz

@app.route('/submit_quiz/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    if 'user' in session:
        questions = Questions.query.filter_by(quiz_id=quiz_id).all()
        user = Users.query.filter_by(id=session['user']).first()
        score = 0
        tot_score = 0
        for question in questions:
            # print("hhhhhhhhhhhh ----", type(question.correct_answer) , type(request.form[str(question.id)] ) )
            if request.form[str(question.id)] == str(question.correct_answer):
                score += 1
            tot_score += 1
        
        new_score = Scores(score=score,total_scored=tot_score, user_id=user.id, quiz_id=quiz_id, timestamp=datetime.fromisoformat(session['timestamp']))
        db.session.add(new_score)
        db.session.commit()

        return render_template('result.html',score=score, total_score=tot_score, user=user)


 
        #if request.form["2"]:
            #print("question id:", questions[0].id,"your answer is", request.form["2"],"and correct answer is", questions[0].correct_option)
        #if request.form["3"]:
            #print("question id:", questions[1].id,"your answer is", request.form["3"],"and correct answer is", questions[1].correct_option)
        #if "4" in request.form:
            #print("question id:", questions[2].id,"your answer is", request.form["4"],"and correct answer is", questions[2].correct_option)
        #if request.form["5"]:
            #print("question id:", questions[3].id,"your answer is", request.form["5"],"and correct answer is", questions[3].correct_option)

        return redirect("/user")
    


#creating user/history route to show all the previous attempted quizzes to thr user

@app.route('/user/history')
def user_history():
    if 'user' in session:
        user = Users.query.filter_by(id=session['user']).first()
        scores = Scores.query.filter_by(user_id=user.id).all()
        return render_template('history.html', scores=scores, user=user)
    return redirect('/login')




#craeting routee for admin search for users, subjects, chapters and quizzes based on their names

@app.route('/admin/search', methods=['GET'])
def admin_search():
    search_query = request.args.get('query', '')  # Use request.args for GET requests
    if not search_query:
        return render_template("admin_search.html", users=[], subjects=[], chapters=[], quizzes=[])

    # Implement your search logic here
    users = Users.query.filter(Users.name.ilike(f"%{search_query}%")).all()
    subjects = Subjects.query.filter(Subjects.name.ilike(f"%{search_query}%")).all()
    chapters = Chapters.query.filter(Chapters.name.ilike(f"%{search_query}%")).all()
    quizzes = Quizzes.query.filter(Quizzes.name.ilike(f"%{search_query}%")).all()

    return render_template("admin_search.html", users=users, subjects=subjects, chapters=chapters, quizzes=quizzes)
    


#creating route for admin summary to show no of quizzes in each subject in bargraph, and showing subject wise user attempts in pie chart

@app.route('/admin/summary')
def admin_summary():
    if 'admin' in session:
        subjects = Subjects.query.all()
        users = Users.query.all()
        img_1 = os.path.join(curr_dir, "static", "imgs", "img_1.png")
        quiz_count_dict = {}
        for subject in subjects:
            quiz_count_dict[subject.name] = 0
            subject_chapters = Chapters.query.filter_by(subject_id=subject.id).all()
            for chapter in subject_chapters:
                quiz_count_dict[subject.name] += len(Quizzes.query.filter_by(chapter_id=chapter.id).all())
        subject_names = [key for key in quiz_count_dict]
        quiz_count = [value for value in quiz_count_dict]
        plt.figure(figsize=(6,4))
        sns.barplot(x= subject_names, y=quiz_count)
        plt.title("Quiz per subject")
        plt.xlabel("Subjects name")
        plt.ylabel("No of quizzes")
        plt.savefig(img_1, format="png")

        img_2 = os.path.join(curr_dir, "static", "imgs", "img_2.png")
        user_attempts_dict = {}
        for user in users:
            user_attempts_dict[user.name] = 0
            scores = Scores.query.filter_by(user_id=user.id).all()
            for score in scores:
                user_attempts_dict[user.name] += 1
        labels = user_attempts_dict.keys()
        sizes = user_attempts_dict.values()
        plt.figure(figsize=(6,4))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', shadow=True, startangle=90)
        plt.title("User attempts per subject")
        plt.savefig(img_2, format="png")
        return render_template('admin_summary.html', img_1=img_1, img_2=img_2)
    return redirect('/login')


        
@app.route('/quiz_chart')
def quiz_chart():
    return render_template('quiz_chart.html')
      
                                             
            


from flask import  jsonify  # Import your Scores model  # Import your database instance

@app.route('/quiz_scores')
def quiz_scores():
    # Fetch quiz scores grouped by quiz_id
    scores_data = Scores.query.filter_by(user_id=session['user'])

    # Convert the data to a dictionary for JSON response

    scores_list = [{"quiz_id": row.quiz_id, "attempts": idx, "total_score": row.total_scored} for idx,row in enumerate(scores_data)]

    return jsonify(scores_list)




if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()
    app.run(debug=True)






