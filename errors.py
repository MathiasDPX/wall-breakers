from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from requests import HTTPError

from providers.exceptions import *


def error_response(code, name, message):
    if request.path.startswith("/api/"):
        return jsonify({
            "success": False,
            "error": {
                "code": code,
                "name": name,
                "message": message
            }
        }), code
        
    return render_template(
        "error.html",
        code=code,
        name=name,
        description=message,
    ), code


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_exception(e):
        return error_response(e.code, e.name, e.description)

    @app.errorhandler(HTTPError)
    def handle_api_exception(e):
        return error_response(e.response.status_code, e.response.reason, e.response.reason)

    @app.errorhandler(DataDomeCookieExpiredError)
    def handle_datadome_exception(e):
        return error_response(503, "Service Unavailable", "The service is temporarily unavailable due to an expired DataDome token.")

    @app.errorhandler(OuestFranceDisabledException)
    def handle_ouestfrance_disabled_exception(e):
        return error_response(501, "Not Implemented", "Ouest-France is disabled because the <code>OUESTFRANCE_REFRESH_TOKEN</code> environment variable is not set.")

    @app.errorhandler(OuestFranceMissingSubscriptionException)
    def handle_ouestfrance_missingsubscription_exception(e):
        return error_response(402, "Payment Required", "The Ouest-France account does not has any active subscription.")
    
    @app.errorhandler(MediapartDisabledException)
    def handle_mediapart_disabled_exception(e):
        return error_response(501, "Not Implemented", "Mediapart is disabled because the <code>PIERREVIVES_USERNAME</code> or  <code>PIERREVIVES_PASSWORD</code> environment variable is not set.")
    
    @app.errorhandler(MediapartInvalidLogin)
    def handle_mediapart_invalidlogin_exception(e):
        return error_response(402, "Payment Required", "The Mediapart account does not has any active subscription.")
    
    @app.errorhandler(NotImplementedError)
    def handle_notimplemented_exception(e):
        return error_response(501, "Not Implemented", "This page isn't implemented yet")