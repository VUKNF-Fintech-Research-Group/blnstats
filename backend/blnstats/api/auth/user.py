############################################################
# Author:           Tomas Vanagas
# Updated:          2025-03-11
# Version:          1.0
# Description:      User model
############################################################


from flask_login import UserMixin, LoginManager
from ..database.db import get_db_connection


login_manager = LoginManager()


class User(UserMixin):
    def __init__(self, id, email, password, admin):
        self.id = id
        self.email = email
        self.password = password
        self.admin = admin
        self.authenticated = False

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    with get_db_connection() as conn:
        sqlFetchData = conn.execute(''' 
            SELECT
                ID,
                Email,
                Password,
                Admin
            FROM
                System_Users
            WHERE 
                ID = ?
        ''', [user_id]).fetchall()
        
        if len(sqlFetchData) != 1:
            return None

        sqlFetchData = sqlFetchData[0]
        return User(sqlFetchData[0], sqlFetchData[1], sqlFetchData[2], sqlFetchData[3])


def get_user_by_email(email):
    with get_db_connection() as conn:
        sqlFetchData = conn.execute(''' 
            SELECT
                ID,
                Email,
                Password,
                Admin
            FROM
                System_Users
            WHERE 
                Email = ?
        ''', [email]).fetchall()
        
        if len(sqlFetchData) != 1:
            return None

        sqlFetchData = sqlFetchData[0]
        return User(sqlFetchData[0], sqlFetchData[1], sqlFetchData[2], sqlFetchData[3])

