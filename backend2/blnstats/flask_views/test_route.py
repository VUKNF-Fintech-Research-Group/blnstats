from flask import Blueprint

bp = Blueprint('test', __name__, url_prefix='/test')


@bp.route('/test123', methods=('GET', 'POST'))
def test_route():
    return 'Test route works!'

