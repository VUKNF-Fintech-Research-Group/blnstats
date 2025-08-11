############################################################
# Author:           Tomas Vanagas
# Updated:          2025-08-07
# Version:          1.0
# Description:      System settings routes (MySQL)
############################################################


from flask import Blueprint, jsonify
import json

from ...database.utils import get_db_connection
from flask_login import login_required

settings_bp = Blueprint('settings', __name__)



@login_required
@settings_bp.route('/api/settings', methods=['GET'])
def get_settings_HTTPGET():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT JSON_OBJECTAGG(`Key`, `Value`) FROM System_Settings')
            result = cursor.fetchone()[0]
    
    settings_dict = json.loads(result) if result else {}
    return jsonify(settings_dict)

