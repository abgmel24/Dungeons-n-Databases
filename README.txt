Name: Abhi Gudimella, Nate Moss
Date: 12/14/2024
Class: CPSC-408-2

Source Files:
- dmdatabase-dump.sql
- finalproject.sql
- app.py
- db_operations.py
- templates (folder with .html files)
- static (folder with .css files)

Additional Files:
- FinalProject.sql (contains background info such as queries that were used in app.py)

Instructions To Run:
-Import datadump to create database with data
-Import dependencies to run the project in Python 3.13 with mysql-connector-python:
flask (can be installed by doing "pip install flask" in terminal)
bcrypt (can be installed by doing "pip install bcrypt" in terminal)
>python app.py
-Click on generated link in console, output should look like below:
-"Database created or already exists.
connection made..
 

    Serving Flask app 'app'
    Debug mode: on

WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 

    Running on http://127.0.0.1:5000/

Press CTRL+C to quit
 

    Restarting with stat

Database created or already exists.
connection made..
and you ctrl+click on the link"

References:
MySQL:
-https://stackoverflow.com/questions/3316950/create-if-not-exists-view
-https://stackoverflow.com/questions/28755505/how-to-convert-sql-query-results-into-a-python-dictionary
-https://www.geeksforgeeks.org/how-to-save-a-python-dictionary-to-a-csv-file/
-https://stackoverflow.com/questions/3316950/create-if-not-exists-view
CSV:
-https://docs.python.org/3/library/csv.html
Flask:
-https://www.youtube.com/watch?v=Z1RJmh_OqeA
-https://www.youtube.com/watch?v=0Qxtt4veJIc&list=PLCC34OHNcOtolz2Vd9ZSeSXWc8Bq23yEz&index=1
Python:
-https://stackoverflow.com/questions/28755505/how-to-convert-sql-query-results-into-a-python-dictionary