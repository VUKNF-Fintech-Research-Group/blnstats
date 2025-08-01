############################################################
# Author:           Tomas Vanagas
# Updated:          2025-03-11
# Version:          1.0
# Description:      Authentication and user 
#                   management routes
############################################################


from flask import Blueprint, request, Response
from flask_login import login_user, login_required, current_user
import bcrypt
import json
from datetime import datetime

from .user import get_user_by_email
from ..database.db import get_db_connection




auth_bp = Blueprint('auth', __name__)





@auth_bp.route('/api/login', methods=['POST'])
def login_HTTPPOST():
    postData = request.get_json()

    # Preauth Checks
    if( not postData or (not postData.get('email') and not postData.get('password')) ):
        return "Please enter email and password."

    if( not postData.get('email') ):
        return "Please enter email."

    if( not postData.get('password') ):
        return "Please enter password."


    # Authentication
    thisUserObject = get_user_by_email(postData['email'].lower())
    if(thisUserObject is not None):
        # Login Check
        if( bcrypt.checkpw( str.encode(postData.get('password')), str.encode(thisUserObject.password) )):
            login_user(thisUserObject)
            return 'OK'
        return "Incorrect email or password."
    
    else:
        # Dummy check
        bcrypt.checkpw( str.encode("This Only Used to prevent time based user enumeration attack, so doing nothing there."), 
                        str.encode('$2b$12$37rvWwtdP/sb.pZwBklPFeUxoH.KWOXIDjTxiiC9awCYpXIB8EbmS') )
        return "Incorrect email or password."





@auth_bp.route('/api/checkauth', methods=['GET'])
@login_required
def checkauth_HTTPGET():
    with get_db_connection() as conn:

        # User Info
        user_info = {
            "id": current_user.id,
            "email": current_user.email,
            "admin": 1
        }

        # Update LastLogin
        timeNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute('UPDATE System_Users SET LastSeen = ? WHERE ID = ?', [timeNow, current_user.id])
        return Response(json.dumps(user_info, indent=4), mimetype='application/json')





@auth_bp.route('/api/admin/administrators', methods=['GET', 'POST'])
@login_required
# @admin_required
def usersList_HTTP():
    with get_db_connection() as conn:
        if request.method == "GET":
            sqlFetchData = conn.execute(f'''
                SELECT
                    json_group_array(
                        json_object(
                            'id',           System_Users.ID,
                            'email',        System_Users.Email,
                            'admin',        System_Users.Admin,
                            'enabled',      System_Users.Enabled,
                            'lastseen',     System_Users.LastSeen
                        )
                    ) AS UsersJSON
                FROM
                    System_Users
            ''')
            return Response(json.dumps(json.loads(sqlFetchData.fetchone()[0]), indent=4), mimetype='application/json')
        elif request.method == "POST":
            postData = request.get_json()

            if(postData['action'] == 'insertupdate'):
                passwordHash = bcrypt.hashpw(postData['password'].encode('utf-8'), bcrypt.gensalt(rounds=12)).decode("utf-8")

                if(postData['id'] == ''):
                    if(len(postData['password']) == 0):
                        return Response(json.dumps({'type': 'error', 'reason': 'Password must be at least 8 characters long'}), mimetype='application/json')
                    conn.execute(' INSERT OR IGNORE INTO System_Users (Email, Password, Admin, Enabled, LastSeen) VALUES (?,?,?,?,?) ',
                                    [ postData['email'], passwordHash, postData['admin'], postData['enabled'], '' ])
                else:    
                    if(len(postData['password']) != 0):
                        conn.execute(' UPDATE System_Users SET Password = ? WHERE ID = ? ', [ passwordHash,         postData['id'] ])
                    conn.execute(' UPDATE System_Users SET Email = ? WHERE ID = ? ',        [ postData['email'],    postData['id'] ])
                    conn.execute(' UPDATE System_Users SET Admin = ? WHERE ID = ? ',        [ postData['admin'],    postData['id'] ])
                    conn.execute(' UPDATE System_Users SET Enabled = ? WHERE ID = ? ',      [ postData['enabled'],  postData['id'] ])
                
                conn.commit()
                return Response(json.dumps({'type': 'ok'}), mimetype='application/json')
            

            elif(postData['action'] == 'delete'):
                conn.execute(' DELETE FROM System_Users WHERE ID = ? ', [ postData['id'] ])
                conn.commit()
                return Response(json.dumps({'type': 'ok'}), mimetype='application/json')
            return Response(json.dumps({'type': 'error'}), mimetype='application/json')

