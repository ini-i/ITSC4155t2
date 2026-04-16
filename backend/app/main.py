# app/main.py
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Security
from sqlalchemy.orm import Session, joinedload
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware

# Models
from app.models.user import User, Parents,Topic, Questions, AnswerChoices, UserAnswer, UserProgress, UserAchievement, Achievement, DifficultyLevel, QuestionAttempt

# Schemas
from app.schemas.user_schema import UserCreate, UserResponse, UserLogin
from app.schemas.parent_schema import ParentCreate, ParentLogin, ParentResponse
from app.schemas.questions_schema import QuestionsSchema, TopicSchema, QuestionSubmitSchema
from app.schemas.achievement_schema import AchievementSchema, UserAchievementSchema


from app.db.database import SessionLocal, engine, Base


# Auth helpers
from app.routes.auth import create_access_token, hash_password, verify_password, decode_access_token

# Create tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()
security = HTTPBearer()

# #-----------------------
# # Enable CORS
# #-----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
 )


# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ----------------------
# Root Route
# ----------------------
@app.get("/")
def read_root():
    return {"message": "Brainy Pop API is running!"}

@app.get("/debug/parents")
def debug_parents(db: Session = Depends(get_db)):
    return db.query(Parents).all()


# ----------------------
# Student Routes
# ----------------------

@app.post("/student/login")
def student_login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect Username or Password")

    access_token = create_access_token(data={"sub": db_user.username, "role": "student"})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "student",
        "username": db_user.username,
        "id": db_user.id 
    }


# ----------------------
# Parent Routes
# ----------------------
'''
@app.post("/parent/register", response_model=ParentResponse)
def parent_register(parent: ParentCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(Parents).filter(
            (Parents.username == parent.username) | (Parents.email == parent.email)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Parent already exists")

        new_parent = Parents(
            username=parent.username,
            email=parent.email,
            password_hash=hash_password(parent.password)
        )

        db.add(new_parent)
        db.commit()
        db.refresh(new_parent)
        return new_parent
    except Exception as e:
        print(f"Error during registration: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
'''

@app.post("/parent/register", response_model=ParentResponse)
def parent_register(parent: ParentCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(Parents).filter(
            (Parents.username == parent.username) | (Parents.email == parent.email)
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Parent already exists")

        new_parent = Parents(
            username=parent.username,
            email=parent.email,
            password_hash=hash_password(parent.password)
        )

        db.add(new_parent)
        db.commit()
        db.refresh(new_parent)

        return new_parent

    except Exception as e:
        print("🔥 REGISTER ERROR:", repr(e))   # 👈 shows error in Render logs
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/parent/login")
def parent_login(parent: ParentLogin, db: Session = Depends(get_db)):
    db_parent = db.query(Parents).filter(Parents.username == parent.username).first()
    if not db_parent or not verify_password(parent.password, db_parent.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect Username or Password")

    access_token = create_access_token(data={"sub": db_parent.username, "role": "parent"})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": "parent",
        "username": db_parent.username
    }


# ----------------------
# Protected Route
# ----------------------
def get_current_user(token=Security(security)):
    print(f"🔑 Token received: {token.credentials[:20]}...") 
    payload = decode_access_token(token.credentials)
    print(f"📝 Payload decoded: {payload}")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

def get_current_parent(
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    if current["role"] != "parent":
        raise HTTPException(status_code=403, detail="Only parents allowed")

    parent = db.query(Parents).filter(
        Parents.username == current["sub"]
    ).first()

    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    return parent

@app.get("/dashboard")
def dashboard(user:dict=Depends(get_current_user)):
    return {
        "message": f"Welcome {user['role']} {user['sub']}!",
        "role": user["role"]
    }

@app.get("/parent/me")
def get_parent(parent:Parents = Depends(get_current_parent)):
    return parent

@app.post("/parent/create-child", response_model=UserResponse)
def create_child(
    user: UserCreate,
    db: Session = Depends(get_db),
    parent:Parents = Depends(get_current_parent)
):
    existing = db.query(User).filter(
        User.username == user.username).first()

    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username = user.username,
        password_hash = hash_password(user.password),
        parent_id = parent.id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# ----------------------
# View Point
# ----------------------
@app.get("/parent/children", response_model=List[UserResponse])
def get_children(parent:Parents=Depends(get_current_parent)):
    return parent.children


@app.get("/parent/child/{child_id}/progress")
def get_child_progress(
    child_id: int,
    db: Session = Depends(get_db),
    parent=Depends(get_current_parent)
):
    child = db.query(User).filter(
        User.id == child_id,
        User.parent_id == parent.id
    ).first()

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == child.id
    ).all()

    return [
        {
            "topic": p.topic.name, 
            "Attempted": p.times_attempted,
            "Correct": p.times_correct,
            "Accuracy": round(
                (p.times_correct / p.times_attempted * 100)
                if p.times_attempted > 0 else 0,
                2
            ),
            "Difficulty": p.difficulty_level,
            "Streak": p.current_streak
        }
        for p in progress
    ]

#-----------------------
# Question Answer
#-----------------------
@app.post("/questions/answer")
def answer_question(
    question_id: int,
    answer: str,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    if current["role"] != "student":
        raise HTTPException(status_code=403, detail="Only student allowed")
    
    question = db.query(Questions).filter(Questions.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    is_correct = question.correct_ans.lower() == answer.lower()
    score = 10 if is_correct else 0

    student = db.query(User).filter(User.username==current["sub"]).first()

    progress = db.query(UserProgress).filter(
        UserProgress.user_id == student.id,
        UserProgress.topic_id == question.topic_id
    ).first()

    if not progress:
        progress = UserProgress(
            user_id = student.id,
            topic_id = question.topic_id
        )
        db.add(progress)

    if not progress.difficulty_level:
        progress.difficulty_level = DifficultyLevel.easy


    progress.times_attempted += 1

    if is_correct:
        progress.times_correct += 1
        progress.current_streak += 1
        progress.wrong_streak = 0
    else:
        progress.wrong_streak += 1
        progress.current_streak = 0

    # Increase difficulty
    if progress.current_streak >= 5:
        if progress.difficulty_level == DifficultyLevel.easy:
            progress.difficulty_level = DifficultyLevel.medium
        elif progress.difficulty_level == DifficultyLevel.medium:
            progress.difficulty_level = DifficultyLevel.hard
        progress.current_streak = 0

# Decrease difficulty
    if progress.wrong_streak >= 2:
        if progress.difficulty_level == DifficultyLevel.hard:
            progress.difficulty_level = DifficultyLevel.medium
        elif progress.difficulty_level == DifficultyLevel.medium:
            progress.difficulty_level = DifficultyLevel.easy
        progress.wrong_streak = 0


    progress.last_attempted = datetime.utcnow() #changed..took out double datetime
    db.commit()

    return {
        "Correct": is_correct,
        "Score": score,
        "Streak": progress.current_streak,
        "Difficulty": progress.difficulty_level
    }

@app.get("/topics", response_model=List[TopicSchema])
def get_topics(db: Session = Depends(get_db)):
    return db.query(Topic).all()

@app.get("/topics/{topic_id}/questions", response_model=List[QuestionsSchema])
def get_questions_by_topic(
    topic_id: int,
    difficulty: Optional[str] = None,
    limit: int = 10, 
    db: Session = Depends(get_db),
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    query = (
        db.query(Questions)
        .options(joinedload(Questions.choices))
        .filter(Questions.topic_id == topic_id)
    )

    if difficulty:
        query = query.filter(Questions.difficulty == difficulty)

    return query.limit(limit).all()

#-----------------
#Progress Tracking
#-----------------
@app.get("/student/progress/topics")
def get_topic_progress(
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    if current["role"] != "student":
        raise HTTPException(status_code=403, detail="Not a child")

    student = db.query(User).filter(User.username == current["sub"]).first()
    progress = db.query(UserProgress).filter(UserProgress.user_id == student.id).all()

    return [
        {
            "topic": p.topic.name,
            "Attempted": p.times_attempted,
            "Correct": p.times_correct,
            "Accuracy": round(
            (p.times_correct / p.times_attempted * 100)
            if p.times_attempted > 0 else 0,
            2
            ),
            "Difficulty": p.difficulty_level,
            "Streak": p.current_streak
        }
        for p in progress
    ]

@app.post("/questions/submit")
def submit_question(
    payload: QuestionSubmitSchema,
    db: Session = Depends(get_db),
    #current_user = Depends(get_current_user)
):
    question = db.query(Questions).filter(Questions.id == payload.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    choice = db.query(AnswerChoices).filter(AnswerChoices.id == payload.answer_choice_id).first()
    if not choice:
        raise HTTPException(status_code=404, detail="Choice not found")
    
    is_correct = choice.is_correct == True
    difficulty = question.difficulty

    #user_id = db.query(User).filter(User.username == current_user["sub"]).first().id
    user_submission = UserAnswer(
        user_id = payload.user_id,
        questions_id = payload.question_id,
        is_correct = is_correct
    )

    db.add(user_submission)

    attempt = QuestionAttempt(
        user_id=payload.user_id,
        question_id=question.id,
        topic_id=question.topic_id,
        is_correct=is_correct,
        difficulty=difficulty
    )
    db.add(attempt)
    db.commit()
    db.refresh(user_submission)

    return {
        "message": "Answer Submitted!",
        "is_correct":  is_correct
    }

@app.get("/parent/child/{child_id}/summary")
def get_child_summary(child_id: int, db: Session = Depends(get_db), parent=Depends(get_current_parent)):
    child = db.query(User).filter(
        User.id == child_id,
        User.parent_id == parent.id
    ).first()

    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    
    progress = db.query(UserProgress).filter(UserProgress.user_id == child.id).all()

    total_attempts = sum(p.times_attempted for p in progress)
    total_correct = sum(p.times_correct for p in progress)

    accuracy = round((total_correct / total_attempts * 100) if total_attempts > 0 else 0, 2)

    return {
        "child_id": child.id, 
        "username": child.username,
        "total_attempts": total_attempts,
        "accuracy": accuracy,
        "topics_tracked": len(progress),
        "last_active": max([p.last_attempted for p in progress]) if progress else None
    }

#-----------------
#Achievement Routes
#-----------------
#used to get all the achievements that the kid can earn
@app.get("/achievements", response_model=List[AchievementSchema])
def get_all_achievements(db: Session = Depends(get_db)):
    return db.query(Achievement).all()

#be specfic when fetching achievements for each kid
@app.get("/student/achievements", response_model=List[UserAchievementSchema])
def get_student_achievements(
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    if current["role"] != "student":
        raise HTTPException(status_code=403, detail="Students only")
    
    student = db.query(User).filter(User.username == current["sub"]).first()

    return(
        db.query(UserAchievement)
        .options(joinedload(UserAchievement.achievement))
        .filter(UserAchievement.user_id == student.id)
        .all()
    )

@app.post("/student/achievements/{achievement_id}")
def award_achievement(
    achievement_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user)
):
    if current["role"] != "student":
        raise HTTPException(status_code=403, detail="Student only")
    
    student = db.query(User).filter(User.username == current["sub"]).first()

    #be sure they don't already have it
    already_earned = db.query(UserAchievement).filter(
        UserAchievement.user_id == student.id,
        UserAchievement.achievement_id ==achievement_id
    ).first()

    if already_earned:
        return{"message:": "Achievement already earned!"}
    
    new_achievement = UserAchievement(
        user_id=student.id,
        achievement_id=achievement_id
    )
    db.add(new_achievement)
    db.commit()

    return{"message": "Achievement unlocked!"}

