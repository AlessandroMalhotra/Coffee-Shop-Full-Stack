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

# db_drop_and_create_all()


@app.after_request
def after_request(response):
    response.headers.add(
    'Access-control-Allow-Headers',
     'Content-Type, Authorization')
    response.headers.add(
    'Access-control-Allow-Methods',
     'GET, POST, PATCH, DELETE, OPTIONS')

    return response


# ROUTES


""" 
Public permission. 
This API fetches all drinks with a short description. 
Return the drinks array or the error handler 

"""

@app.route('/drinks', methods=['GET'])
def drinks_menu():
    all_drinks = Drink.query.all()

    if all_drinks is None:
        abort(404)

    drinks = [drink.short() for drink in all_drinks]

    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200



 """ 
 get:drinks-detail permission.
 This API fetches all drinks with a long description. 
 Returns the drinks array or the error handler 
 
 """

@app.route('/drinks-detail', methods=['GET'])
@requires_auth('get:drinks-detail')
def drink_details(payload):
    all_drinks = Drink.query.order_by(Drink.id).all()
    
    if all_drinks is None:
        abort(404)
    
    drinks = [drink.long() for drink in all_drinks]

    return jsonify({
        'success': True,
        'drinks': drinks
    }), 200



""" 
post:drinks permission.
This API creates a new drink and returns its long description. 
Return the created drink info or the error handler 

"""
     
@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(payload):
    req = request.get_json()
    
    title = req.get('title')
    recipe = req.get('recipe')

    try:
        new_drink = Drink(title=title, recipe=json.dumps(recipe))
        new_drink.insert()

        return jsonify({
            'success': True,
            'drinks': [new_drink.long()]
        }), 200

    except Exception:
        abort(405)



""" 
patch:drinks permission.
This API updates a drink if it exists. 
Return the updated drink info or the error handler

"""

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drinks(payload, id):
    req = request.get_json()
    title = req.get('title')
    recipe = req.get('recipe')

    drink = Drink.query.get(id)

    if drink is None:
        abort(404)
    
    try:
        drink.title = title
        drink.recipe = json.dumps(recipe)

        drink.update()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200

    except Exception as e:
        abort(422)
        

""" 
delete:drinks permission.This API deletes a drink if it exists. 
Return the deleted drink info or the error handler.

"""

@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drinks(payload, id):
    drink = Drink.query.get(id)

    if drink is None:
        abort(404)
    
    try:
        drink.delete()

        return jsonify({
            'success': True,
            'drink': id
        })

    except BaseException:
        abort(422)


# Error Handling
'''
Example error handling for unprocessable entity
'''
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False, 
        "error": 422,
        "message": "unprocessable"
    }), 422


''' Propagates the formatted 404 error to the response '''
@app.errorhandler(404)
def unprocessable(error):
    return jsonify({
         "success": False, 
         "error": 404,
         "message": "resource not found"
    }), 404



''' Error handler for incorrect method type ''''
@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 405,
        'message': 'method not allowed'
    }), 405



 ''' Receive the raised authorization error and propagates it as response '''
@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response