from flask import Blueprint
from decorators.auth import auth
from decorators.errors import errors
import settings
status = Blueprint('status', __name__)


@status.route("/machinekit/status", endpoint='get_machine_status', methods=["GET"])
@auth
@errors
def get_machinekit_status():
    return settings.controller.get_all_vitals()
