# squareHack

Make sure to update requirements txt

#Create a virtual env after installing virtualenv ->
virtualenv venv
#Then
source venv/bin/activate


#To install requirements ->
pip3 install -r requirements.txt 

#update requirements ->
pip3 freeze > requirements.txt



#Running the app ->
FLASK_APP=app.py flask run


#how database was made in the terminal ->
1. activate virtual env
2. activate python3 shell
3. from app import db
4. db.create_all()
5. (to turn off sqlalchemy layering) SQLALCHEMY_TRACK_MODIFICATIONS = False



<!-- action = "{{ url_for('search') }}" -->