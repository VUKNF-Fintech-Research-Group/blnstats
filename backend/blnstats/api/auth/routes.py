############################################################
# Author:           Tomas Vanagas
# Updated:          2025-03-11
# Version:          1.0
# Description:      Authentication and user 
#                   management routes (MySQL)
############################################################


from flask import Blueprint, request, Response
from flask_login import login_user, login_required, current_user
import bcrypt
import json
from datetime import datetime

from .user import get_user_by_email
from ...database.utils import get_db_connection



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
        with conn.cursor() as cursor:
            # User Info
            user_info = {
                "id": current_user.id,
                "email": current_user.email,
                "admin": 1
            }

            # Update LastLogin
            timeNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('UPDATE System_Users SET LastSeen = %s WHERE ID = %s', [timeNow, current_user.id])
            conn.commit()
            return Response(json.dumps(user_info, indent=4), mimetype='application/json')




@auth_bp.route('/api/admin/administrators', methods=['GET', 'POST'])
@login_required
# @admin_required
def usersList_HTTP():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            if request.method == "GET":
                cursor.execute('''
                    SELECT
                        JSON_ARRAYAGG(
                            JSON_OBJECT(
                                'id',           System_Users.ID,
                                'email',        System_Users.Email,
                                'admin',        System_Users.Admin,
                                'enabled',      System_Users.Enabled,
                                'lastseen',     DATE_FORMAT(System_Users.LastSeen, '%Y-%m-%d %H:%i:%s')
                            )
                        ) AS UsersJSON
                    FROM
                        System_Users
                ''')
                result = cursor.fetchone()[0]
                users_data = json.loads(result)
                return Response(json.dumps(users_data, indent=4), mimetype='application/json')
            elif request.method == "POST":
                postData = request.get_json()

                if(postData['action'] == 'insertupdate'):
                    passwordHash = bcrypt.hashpw(postData['password'].encode('utf-8'), bcrypt.gensalt(rounds=12)).decode("utf-8")

                    if(postData['id'] == ''):
                        if(len(postData['password']) == 0):
                            cursor.close()
                            return Response(json.dumps({'type': 'error', 'reason': 'Password must be at least 8 characters long'}), mimetype='application/json')
                        cursor.execute(' INSERT IGNORE INTO System_Users (Email, Password, Admin, Enabled, LastSeen) VALUES (%s,%s,%s,%s,%s) ',
                                        [ postData['email'], passwordHash, postData['admin'], postData['enabled'], '' ])
                    else:    
                        if(len(postData['password']) != 0):
                            cursor.execute(' UPDATE System_Users SET Password = %s WHERE ID = %s ', [ passwordHash,         postData['id'] ])
                        cursor.execute(' UPDATE System_Users SET Email = %s WHERE ID = %s ',        [ postData['email'],    postData['id'] ])
                        cursor.execute(' UPDATE System_Users SET Admin = %s WHERE ID = %s ',        [ postData['admin'],    postData['id'] ])
                        cursor.execute(' UPDATE System_Users SET Enabled = %s WHERE ID = %s ',      [ postData['enabled'],  postData['id'] ])
                    
                    conn.commit()
                    cursor.close()
                    return Response(json.dumps({'type': 'ok'}), mimetype='application/json')
                

                elif(postData['action'] == 'delete'):
                    cursor.execute(' DELETE FROM System_Users WHERE ID = %s ', [ postData['id'] ])
                    conn.commit()
                    cursor.close()
                    return Response(json.dumps({'type': 'ok'}), mimetype='application/json')
                cursor.close()
                return Response(json.dumps({'type': 'error'}), mimetype='application/json')

