# python3 -m venv venv
# source venv/bin/activate
# pip3 install Flask
# pip3 install flask_debugtoolbar
# pip3 freeze > requirements.txt
# flask run --reload

# git init
# nano .gitignore (add venv/ , __pycache__/)
# git add .
# git commit -m '...'
# git remote add origin https://github...
# git push -u origin main

from flask import Flask, session, request, render_template, redirect, make_response, flash
from flask_debugtoolbar import DebugToolbarExtension

class Question:
    def __init__(self, question, choices=None, allow_text=False):
        if not choices:choices = ["Yes", "No"]
        self.question = question
        self.choices = choices
        self.allow_text = allow_text
class Survey:
    def __init__(self, title, instructions, questions):
        self.title = title
        self.instructions = instructions
        self.questions = questions
satisfaction_survey = Survey(
    "Customer Satisfaction Survey",#title
    "Fill out a survey about your experience with us",#instructions
   [Question("Have you shopped here before?"),
    Question("Did someone else shop with you today?"),
    Question("On average, how much do you spend a month on frisbees?",
                ["Less than $10K", "$10K or more"]),
    Question("Are you likely to shop here again?"),
   ]
)
personality_quiz = Survey(
    "Rithm Personality Test",
    "Learn more about yourself",
   [Question("Do you ever dream about code?"),
    Question("Do you ever have nightmares about code?"),
    Question("Do you prefer porcupines or hedgehogs?",
                ["Porcupines", "Hedgehogs"]),
    Question("Which is the worst function name, and why?",
                ["do_stuff()", "run_me()", "wtf()"],
                allow_text=True),
    ]
)
surveys={"satisfaction":satisfaction_survey,"personality":personality_quiz}

# key names will use to store some things in session
# put here as constants so we're guaranteed to be consistent in our spelling of these
CURRENT_SURVEY_KEY = 'current_survey'
RESPONSES_KEY = 'responses'

app = Flask(__name__)
app.debug=True#for debug tool
app.config['SECRET_KEY'] = "123"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

debug = DebugToolbarExtension(app)

@app.route("/")
def show_pick_survey_form():
    return render_template("pickSurvey.html",surveys=surveys)

@app.route("/", methods=["POST"])
def pick_survey():
    survey_id = request.form['survey_code']
    #can't re-take survey until cookie times out
    if request.cookies.get(f"completed_{survey_id}"):return render_template("alreadyDone.html")
    survey = surveys[survey_id]
    session[CURRENT_SURVEY_KEY] = survey_id
    return render_template("surveyStart.html",survey=survey)

@app.route("/begin", methods=["POST"])
def start_survey():
    session[RESPONSES_KEY] = []#clear session of responses
    return redirect("/questions/0")

@app.route("/answer", methods=["POST"])
def handle_question():#Save response and redirect to next question
    choice = request.form['answer']
    text = request.form.get("text", "")
    responses = session[RESPONSES_KEY]# add this response to list in session
    responses.append({"choice": choice, "text": text})
    session[RESPONSES_KEY] = responses# add this response to session
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]
    if (len(responses) == len(survey.questions)):return redirect("/complete")
    else:return redirect(f"/questions/{len(responses)}")

@app.route("/questions/<int:qid>")
def show_question(qid):#Display current question
    responses = session.get(RESPONSES_KEY)
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]
    if (responses is None):return redirect("/")#if try to access question page too soon
    if (len(responses) == len(survey.questions)):return redirect("/complete")
    if (len(responses) != qid):# Trying to access questions out of order
        flash(f"Invalid question id: {qid}.")
        return redirect(f"/questions/{len(responses)}")
    question = survey.questions[qid]
    return render_template("question.html", question_num=qid, Q=question)

@app.route("/complete")
def say_thanks():
    survey_id = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_id]
    responses = session[RESPONSES_KEY]
    html = render_template("completion.html",survey=survey,responses=responses)
    response = make_response(html)# Set cookie noting this survey is done so user can't re-do it
    response.set_cookie(f"completed_{survey_id}", "yes", max_age=60)
    return response
