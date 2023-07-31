import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

'''
@TODO uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES

@app.route('/')
def check_server():
    return "server running"

'''

@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks')
def get_drinks():
    try:
        all_drinks = Drink.query.order_by(Drink.id).all()
        drinks = [drink.short() for drink in all_drinks]
        return jsonify(
            {
                "success": True, 
                "drinks": drinks
            }
        )
    except Exception:
        abort(422)

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_details(payload):
    try:
        all_drinks = Drink.query.order_by(Drink.id).all()
        drinks = [drink.long() for drink in all_drinks]
        return jsonify(
            {
                "success": True, 
                "drinks": drinks
            }
        ), 200
    except Exception:
        abort(422)


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(payload):
    body = request.get_json()
    title = body['title']
    recipe = body['recipe']
    if not title and not recipe:
        abort(400)
    try:
        new_drink = Drink(title = title, recipe = json.dumps(recipe))
        new_drink.insert()
        drinks = Drink.query.order_by(Drink.id.desc()).all()
        drink = [drink.long() for drink in drinks]
        return jsonify(
            {
                "success": True, 
                "drinks": drink
            }
        ),200
    except Exception:
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    """Updates an existing drink and returns it to the client"""
    try:
        # Get the body from the request
        body = request.get_json()

        if not body:
            abort(400)

        # Find the drink to update by ID
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

        # Check which fields should be updated
        title = body.get('title', None)
        recipe = body.get('recipe', None)

        # Update the drink fields if they are provided
        if title:
            drink.title = title

        if recipe:
            drink.recipe = json.dumps(recipe)

        drink.update()

        return jsonify({
            'success': True,
            'drink': [drink.long()]
        })
    except Exception:
        abort(422)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    """Deletes a drink with a given ID"""
    try:
        if not drink_id:
            abort(400)

        # Find the drink to delete by ID
        drink = Drink.query.get(drink_id)

        if not drink:
            abort(404)

        drink.delete()

        return jsonify({
            'success': True,
            'delete': drink_id
        })
    except Exception:
        abort(422)


# Error Handling

@app.errorhandler(400)
def invalid_request(error):
    return (
            jsonify({
                "success": False,
                "error": 400,
                "message": "Invalid request"
                }), 400
    )

@app.errorhandler(AuthError)
def authentication_failed(error):
    """Handles authentication failed error (403)"""
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error
    }), error.status_code

@app.errorhandler(404)
def not_found(error):
    return (
            jsonify({
                "success": False,
                "error": 404,
                "message": "Resource not found"
                }), 404
    )

@app.errorhandler(422)
def unprocessable(error):
    return (
            jsonify({
                "success": False,
                "error": 422,
                "message": "Unprocessable"
                }), 422
    )

@app.errorhandler(500)
def internal_error(error):
    return (
            jsonify({
                "success": False,
                "error": 500,
                "message": "Internal Server Error"
                }), 500
    )


# $env:FLASK_APP='api.py'
# $env:FLASK_ENV='development'
# python -m flask run --reload