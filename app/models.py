from py2neo.ogm import GraphObject, Property, RelatedTo, RelatedFrom


class User(GraphObject):
    __primarykey__ = 'email'

    name = Property()
    email = Property()
    created_at = Property()

    friends = RelatedTo('User', 'FRIENDS_WITH')
    created_posts = RelatedFrom('Post', 'CREATED')
    created_comments = RelatedFrom('Comment', 'CREATED')


class Post(GraphObject):
    __primarykey__ = 'title'

    title = Property()
    content = Property()
    created_at = Property()

    creator = RelatedFrom(User, 'CREATED')
    comments = RelatedTo('Comment', 'HAS_COMMENT')
    likes = RelatedTo(User, 'LIKES')


class Comment(GraphObject):
    __primarykey__ = 'content'

    content = Property()
    created_at = Property()

    creator = RelatedFrom(User, 'CREATED')
    post = RelatedTo(Post, 'HAS_COMMENT')
    likes = RelatedTo(User, 'LIKES')
