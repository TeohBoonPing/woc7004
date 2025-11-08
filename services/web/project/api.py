import os
import sqlalchemy.exc
import redis
import json
from urllib.parse import quote
from datetime import datetime as dt
from flask import Blueprint, request, jsonify

from .models import db, ShortLink

api = Blueprint('api', __name__)

redis_client = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Ensure all API routes are authenticated
@api.before_request
def before_request():
    # Ensure an auth key is set
    if not os.environ.get('API_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401
    # Ensure header is present
    if not request.headers.get('Authorization'):
        return jsonify({'error': 'Unauthorized'}), 401

    auth_key = request.headers.get('Authorization')
    if auth_key != os.environ.get('API_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401


@api.route('/test')
def test():
    return jsonify({'message': 'Hello World!'})


@api.route('/links/active', methods=['GET'])
def get_active_links():
    # Get all links where expired is False and deleted is False
    links = ShortLink.query.filter_by(expired=False, deleted=False).all()
    return jsonify({'links': [link.to_dict() for link in links]})


@api.route('/links/expired', methods=['GET'])
def get_expired_links():
    # Get all links where expired is True
    links = ShortLink.query.filter_by(expired=True).all()
    return jsonify({'links': [link.to_dict() for link in links]})


@api.route('/links/deleted', methods=['GET'])
def get_deleted_links():
    # Get all links where deleted is True
    links = ShortLink.query.filter_by(deleted=True).all()
    return jsonify({'links': [link.to_dict() for link in links]})


@api.route('/links/<int:link_id>', methods=['GET'])
def get_link(link_id):
    # Get the link
    link = ShortLink.query.filter_by(id=link_id).first()
    if not link:
        return jsonify({'error': 'Link not found'}), 404
    return jsonify({'link': link.to_dict()})


@api.route('/links', methods=['POST'])
def create_link():
    # Get the json body
    body = request.get_json()
    # Ensure the body is present
    if not body:
        return jsonify({'error': 'Missing body'}), 400

    # Needed info
    url = body.get('url', None)
    alias = body.get('alias', None)
    created_by = int(os.environ.get('API_USER_ID', "1"))  # Default to user with id 1
    # Optional info
    max_click_count = body.get('max_click_count', -1)  # Unlimited by default
    expiration_date = body.get('expiration_date', None)  # Never expires by default
    if expiration_date:
        try:
            expiration_date = dt.fromtimestamp(int(expiration_date))
        except ValueError:
            return jsonify({'error': 'Invalid expiration date. Must be unix timestamp.'}), 400

    # Ensure the needed info is present
    if not url or not alias or not created_by:
        return jsonify({'error': 'Missing url or alias or created_by'}), 400

    # Ensure the alias is not taken
    if ShortLink.query.filter_by(short_url=alias).first():
        return jsonify({'error': 'Alias is taken'}), 400

    # Create the link
    try:
        link = ShortLink(original_url=url, short_url=alias, max_clicks=max_click_count, expiration_date=expiration_date, created_by=created_by)
        db.session.add(link)
        db.session.commit()
    except sqlalchemy.exc.DataError as e:
        return jsonify({'error': str(e)}), 400

    return jsonify({'link': link.to_dict()}), 201


@api.route('/links/<int:link_id>', methods=['PUT'])
def update_link(link_id):
    # Get the link
    link = ShortLink.query.filter_by(id=link_id).first()
    if not link:
        return jsonify({'error': 'Link not found'}), 404

    # Get the json body
    body = request.get_json()
    # Ensure the body is present
    if not body:
        return jsonify({'error': 'Missing body'}), 400

    # Needed info
    url = body.get('url', None)
    alias = body.get('alias', None)
    # Optional info
    max_click_count = body.get('max_click_count', -1)
    expiration_date = body.get('expiration_date', None)
    if expiration_date:
        try:
            expiration_date = dt.fromtimestamp(int(expiration_date))
        except ValueError:
            return jsonify({'error': 'Invalid expiration date. Must be unix timestamp.'}), 400

    # Ensure the needed info is present
    if not url or not alias:
        return jsonify({'error': 'Missing url or alias'}), 400

    # Ensure the alias is not taken
    if link.short_url != alias and ShortLink.query.filter_by(short_url=alias).first():
        return jsonify({'error': 'Alias is taken'}), 400

    # Update the link
    try:
        link.original_url = url
        link.short_url = alias
        link.max_clicks = max_click_count
        link.expiration_date = expiration_date
        db.session.commit()
    except sqlalchemy.exc.DataError as e:
        return jsonify({'error': str(e)}), 400

    return jsonify({'link': link.to_dict()})


@api.route('/links/<int:link_id>', methods=['DELETE'])
def delete_link(link_id):
    # Get the link
    link = ShortLink.query.filter_by(id=link_id).first()
    if not link:
        return jsonify({'error': 'Link not found'}), 404

    # Delete the link
    link.deleted = True
    link.expired = True
    db.session.commit()

    return jsonify({'link': link.to_dict()}), 200


@api.route('/links/<int:link_id>/restore', methods=['PUT'])
def restore_link(link_id):
    # Get the link
    link = ShortLink.query.filter_by(id=link_id).first()
    if not link:
        return jsonify({'error': 'Link not found'}), 404

    # Restore the link
    link.deleted = False
    link.expired = False
    db.session.commit()

    return jsonify({'link': link.to_dict()}), 200


@api.route('/links/<int:link_id>/hard', methods=['DELETE'])
def hard_delete_link(link_id):
    # Get the link
    link = ShortLink.query.filter_by(id=link_id).first()
    if not link:
        return jsonify({'error': 'Link not found'}), 404

    # Delete the link
    db.session.delete(link)
    db.session.commit()

    return jsonify({'message': 'Link deleted'}), 200


@api.route('/links/by_long', methods=['POST'])
def get_link_by_longurl():
    body = request.get_json()
    if not body or 'original_url' not in body:
        return jsonify({'error': 'Missing original_url'}), 400

    original_url = body['original_url']
    link = ShortLink.query.filter_by(original_url=original_url, deleted=False).first()
    if not link:
        return jsonify({'error': 'Link not found'}), 404

    return jsonify({'short_url': link.short_url, 'cached': False})


@api.route('/links/redis', methods=['POST'])
def search_link_by_longurl_redis():
    body = request.get_json()
    if not body or 'original_url' not in body:
        return jsonify({'error': 'Missing original_url'}), 400

    original_url = body['original_url']
    cache_key = f"longurl:{original_url}"

    cached_short = redis_client.get(cache_key)
    if cached_short:
        return jsonify({'short_url': cached_short, 'cached': True})

    link = ShortLink.query.filter_by(original_url=original_url, deleted=False).first()
    if not link:
        return jsonify({'error': 'Link not found'}), 404

    redis_client.setex(cache_key, 3600, link.short_url)
    return jsonify({'short_url': link.short_url, 'cached': False})