from flask import Blueprint, request, jsonify
from py2neo import Graph
from datetime import datetime

graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))

routes = Blueprint('routes', __name__)

# ========================== Utilisateurs ========================== #

@routes.route('/users', methods=['GET'])
def get_users():
    query = "MATCH (u:User) RETURN ID(u) AS id, u.name AS name, u.email AS email"
    return jsonify(graph.run(query).data()), 200


@routes.route('/users', methods=['POST'])
def create_user():
    data = request.json
    if not data.get('name') or not data.get('email'):
        return jsonify({"error": "Name and email are required"}), 400

    query = "CREATE (u:User {name: $name, email: $email, created_at: timestamp()}) RETURN ID(u) AS id"
    result = graph.run(query, name=data['name'], email=data['email']).data()
    return jsonify({"message": "User created", "id": result[0]["id"]}), 201


@routes.route('/users/<int:user_id>', methods=['GET'])
def get_user_by_id(user_id):
    query = "MATCH (u:User) WHERE ID(u) = $user_id RETURN ID(u) AS id, u.name AS name, u.email AS email"
    result = graph.run(query, user_id=user_id).data()
    return jsonify(result[0] if result else {"error": "User not found"}), 200 if result else 404


@routes.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    if not data.get('name') or not data.get('email'):
        return jsonify({"error": "Name and email are required"}), 400

    query = """
    MATCH (u:User) WHERE ID(u) = $user_id
    SET u.name = $name, u.email = $email
    RETURN ID(u) AS id, u.name AS name, u.email AS email
    """
    result = graph.run(query, user_id=user_id, name=data['name'], email=data['email']).data()
    return jsonify(result[0] if result else {"error": "User not found"}), 200 if result else 404


@routes.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    graph.run("MATCH (u:User) WHERE ID(u) = $user_id DELETE u", user_id=user_id)
    return jsonify({"message": "User deleted"}), 204


# ========================== Amis ========================== #

@routes.route('/users/<int:user_id>/friends', methods=['GET'])
def get_friends(user_id):
    query = """
    MATCH (u:User)-[:FRIENDS_WITH]->(friend:User)
    WHERE ID(u) = $user_id
    RETURN ID(friend) AS id, friend.name AS name, friend.email AS email
    """
    return jsonify(graph.run(query, user_id=user_id).data()), 200


@routes.route('/users/<int:user_id>/friends', methods=['POST'])
def add_friend(user_id):
    data = request.json
    if not data.get('friend_id'):
        return jsonify({"error": "Friend ID is required"}), 400

    query = """
    MATCH (u:User), (f:User)
    WHERE ID(u) = $user_id AND ID(f) = $friend_id
    MERGE (u)-[:FRIENDS_WITH]->(f)
    """
    graph.run(query, user_id=user_id, friend_id=data['friend_id'])
    return jsonify({"message": "Friend added"}), 201


@routes.route('/users/<int:user_id>/friends/<int:friend_id>', methods=['DELETE'])
def remove_friend(user_id, friend_id):
    graph.run("MATCH (u:User)-[r:FRIENDS_WITH]->(f:User) WHERE ID(u) = $user_id AND ID(f) = $friend_id DELETE r",
              user_id=user_id, friend_id=friend_id)
    return jsonify({"message": "Friend removed"}), 204


@routes.route('/users/<int:user_id>/friends/<int:friend_id>', methods=['GET'])
def check_friendship(user_id, friend_id):
    query = """
    MATCH (u:User)-[:FRIENDS_WITH]-(f:User)
    WHERE ID(u) = $user_id AND ID(f) = $friend_id
    RETURN COUNT(f) AS count
    """
    result = graph.run(query, user_id=user_id, friend_id=friend_id).data()
    is_friend = result[0]["count"] > 0
    return jsonify({"are_friends": is_friend}), 200

@routes.route('/users/<int:user_id>/mutual-friends/<int:other_id>', methods=['GET'])
def get_mutual_friends(user_id, other_id):
    query = """
    MATCH (u:User)-[:FRIENDS_WITH]->(mutual:User)<-[:FRIENDS_WITH]-(o:User)
    WHERE ID(u) = $user_id AND ID(o) = $other_id
    RETURN ID(mutual) AS id, mutual.name AS name, mutual.email AS email
    """
    result = graph.run(query, user_id=user_id, other_id=other_id).data()
    return jsonify(result), 200


# ========================== Posts ========================== #

@routes.route('/posts', methods=['GET'])
def get_posts():
    query = """
    MATCH (p:Post) 
    RETURN ID(p) AS id, p.title AS title, p.content AS content, p.created_at AS created_at
    ORDER BY p.created_at DESC
    """
    result = graph.run(query).data()

    for post in result:
        post["created_at"] = datetime.utcfromtimestamp(post["created_at"] / 1000).strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(result), 200

@routes.route('/posts/<int:post_id>', methods=['GET'])
def get_post_by_id(post_id):
    query = """
    MATCH (p:Post)
    WHERE ID(p) = $post_id
    RETURN ID(p) AS id, p.title AS title, p.content AS content, p.created_at AS created_at
    """
    result = graph.run(query, post_id=post_id).data()

    if not result:
        return jsonify({"error": "Post not found"}), 404

    post = result[0]
    post["created_at"] = datetime.utcfromtimestamp(post["created_at"] / 1000).strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(post), 200


@routes.route('/users/<int:user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    query = """
    MATCH (u:User)-[:CREATED]->(p:Post)
    WHERE ID(u) = $user_id
    RETURN ID(p) AS id, p.title AS title, p.content AS content, p.created_at AS created_at
    ORDER BY p.created_at DESC
    """
    result = graph.run(query, user_id=user_id).data()

    for post in result:
        post["created_at"] = datetime.utcfromtimestamp(post["created_at"] / 1000).strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(result), 200

@routes.route('/users/<int:user_id>/posts', methods=['POST'])
def create_post(user_id):
    data = request.json
    if not data.get('title') or not data.get('content'):
        return jsonify({"error": "Title and content are required"}), 400

    query = """
    MATCH (u:User) WHERE ID(u) = $user_id
    CREATE (u)-[:CREATED]->(p:Post {
        title: $title, 
        content: $content, 
        created_at: datetime().epochMillis  // Stocke en millisecondes
    })
    RETURN ID(p) AS id, p.title AS title, p.content AS content, p.created_at AS created_at
    """
    result = graph.run(query, user_id=user_id, title=data['title'], content=data['content']).data()

    if not result:
        return jsonify({"error": "User not found"}), 404

    post = result[0]

    post["created_at"] = datetime.utcfromtimestamp(post["created_at"] / 1000).strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(post), 201


@routes.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.json
    if not data.get('title') and not data.get('content'):
        return jsonify({"error": "At least one field (title or content) is required"}), 400

    set_clauses = []
    params = {"post_id": post_id}

    if data.get('title'):
        set_clauses.append("p.title = $title")
        params["title"] = data['title']
    if data.get('content'):
        set_clauses.append("p.content = $content")
        params["content"] = data['content']

    query = f"""
    MATCH (p:Post) WHERE ID(p) = $post_id
    SET {', '.join(set_clauses)}
    RETURN ID(p) AS id, p.title AS title, p.content AS content, p.created_at AS created_at
    """
    result = graph.run(query, **params).data()

    if not result:
        return jsonify({"error": "Post not found"}), 404

    post = result[0]
    post["created_at"] = datetime.utcfromtimestamp(post["created_at"] / 1000).strftime('%Y-%m-%d %H:%M:%S')

    return jsonify(post), 200

@routes.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    query = """
    MATCH (p:Post) WHERE ID(p) = $post_id
    OPTIONAL MATCH (p)-[r]-()
    DELETE r, p
    """
    graph.run(query, post_id=post_id)
    return jsonify({"message": "Post deleted"}), 204

@routes.route('/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    data = request.json
    if not data.get('user_id'):
        return jsonify({"error": "User ID is required"}), 400

    query = "MATCH (u:User), (p:Post) WHERE ID(u) = $user_id AND ID(p) = $post_id MERGE (u)-[:LIKES]->(p)"
    graph.run(query, user_id=data['user_id'], post_id=post_id)
    return jsonify({"message": "Post liked"}), 200



@routes.route('/posts/<int:post_id>/like', methods=['DELETE'])
def unlike_post(post_id):
    data = request.json
    if not data.get('user_id'):
        return jsonify({"error": "User ID is required"}), 400

    result = graph.run("MATCH (u:User)-[r:LIKES]->(p:Post) WHERE ID(u) = $user_id AND ID(p) = $post_id DELETE r",
                       user_id=data['user_id'], post_id=post_id)
    summary = result.summary()
    counters = summary.get('counters', None)
    if counters and counters.get('nodes_deleted', 0) == 0:
        return jsonify({"message": "Like not found"}), 404

    return jsonify({"message": "Like removed"}), 200



# ========================== Commentaires ========================== #
@routes.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_comments_by_post(post_id):
    query = """
    MATCH (p:Post)-[:HAS_COMMENT]->(c:Comment)<-[:CREATED]-(u:User)
    WHERE ID(p) = $post_id
    RETURN ID(c) AS id, c.content AS content, c.created_at AS created_at, ID(u) AS user_id, u.name AS user_name
    ORDER BY c.created_at ASC
    """
    result = graph.run(query, post_id=post_id).data()
    for comment in result:
        comment["created_at"] = datetime.utcfromtimestamp(comment["created_at"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(result), 200


@routes.route('/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    data = request.json
    if not data.get('content') or not data.get('user_id'):
        return jsonify({"error": "Content and user ID are required"}), 400

    query = """
    MATCH (u:User), (p:Post)
    WHERE ID(u) = $user_id AND ID(p) = $post_id
    CREATE (c:Comment {content: $content, created_at: timestamp()})
    MERGE (u)-[:CREATED]->(c)
    MERGE (p)-[:HAS_COMMENT]->(c)
    RETURN ID(c) AS id
    """
    result = graph.run(query, user_id=data['user_id'], post_id=post_id, content=data['content']).data()
    return jsonify({"message": "Comment added", "id": result[0]["id"]}), 201


@routes.route('/posts/<int:post_id>/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment_from_post(post_id, comment_id):
    query = """
    MATCH (p:Post)-[r1:HAS_COMMENT]->(c:Comment)<-[r2:CREATED]-(u:User)
    WHERE ID(p) = $post_id AND ID(c) = $comment_id
    OPTIONAL MATCH (c)-[r3]-()
    DELETE r1, r2, r3, c
    """
    graph.run(query, post_id=post_id, comment_id=comment_id)
    return jsonify({"message": "Comment deleted successfully"}), 200

@routes.route('/comments', methods=['GET'])
def get_all_comments():
    query = """
    MATCH (c:Comment)<-[:CREATED]-(u:User)
    RETURN ID(c) AS id, c.content AS content, c.created_at AS created_at, ID(u) AS user_id, u.name AS user_name
    ORDER BY c.created_at DESC
    """
    result = graph.run(query).data()
    for comment in result:
        comment["created_at"] = datetime.utcfromtimestamp(comment["created_at"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(result), 200


@routes.route('/comments/<int:comment_id>', methods=['GET'])
def get_comment_by_id(comment_id):
    query = """
    MATCH (c:Comment)<-[:CREATED]-(u:User)
    WHERE ID(c) = $comment_id
    RETURN ID(c) AS id, c.content AS content, c.created_at AS created_at, ID(u) AS user_id, u.name AS user_name
    """
    result = graph.run(query, comment_id=comment_id).data()
    if not result:
        return jsonify({"error": "Comment not found"}), 404
    comment = result[0]
    comment["created_at"] = datetime.utcfromtimestamp(comment["created_at"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(comment), 200


@routes.route('/comments/<int:comment_id>', methods=['PUT'])
def update_comment(comment_id):
    data = request.json
    if not data.get('content'):
        return jsonify({"error": "Content is required"}), 400

    query = """
    MATCH (c:Comment)
    WHERE ID(c) = $comment_id
    SET c.content = $content
    RETURN ID(c) AS id, c.content AS content, c.created_at AS created_at
    """
    result = graph.run(query, comment_id=comment_id, content=data['content']).data()
    if not result:
        return jsonify({"error": "Comment not found"}), 404

    comment = result[0]
    comment["created_at"] = datetime.utcfromtimestamp(comment["created_at"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
    return jsonify(comment), 200

@routes.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    query = """
    MATCH (c:Comment)
    WHERE ID(c) = $comment_id
    OPTIONAL MATCH (c)-[r]-()
    DELETE r, c
    """
    graph.run(query, comment_id=comment_id)
    return jsonify({"message": "Comment deleted successfully"}), 200


# ========================== Like ========================== #


@routes.route('/comments/<int:comment_id>/like', methods=['POST'])
def like_comment(comment_id):
    data = request.json
    if not data.get('user_id'):
        return jsonify({"error": "User ID is required"}), 400

    query = """
    MATCH (u:User), (c:Comment)
    WHERE ID(u) = $user_id AND ID(c) = $comment_id
    MERGE (u)-[:LIKES]->(c)
    """
    graph.run(query, user_id=data['user_id'], comment_id=comment_id)
    return jsonify({"message": "Comment liked"}), 200


@routes.route('/comments/<int:comment_id>/like', methods=['DELETE'])
def unlike_comment(comment_id):
    data = request.json
    if not data.get('user_id'):
        return jsonify({"error": "User ID is required"}), 400

    query = """
    MATCH (u:User)-[r:LIKES]->(c:Comment)
    WHERE ID(u) = $user_id AND ID(c) = $comment_id
    DELETE r
    """
    graph.run(query, user_id=data['user_id'], comment_id=comment_id)
    return jsonify({"message": "Like removed successfully"}), 200
