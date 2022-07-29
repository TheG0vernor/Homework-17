# app.py

from flask import Flask, request, jsonify
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['JSON_SORT_KEYS'] = False
app.config['JSON_AS_ASCII'] = False
db = SQLAlchemy(app)

api = Api(app)
movie_ns = api.namespace('movies')


class Movie(db.Model):  # таблица (модель) фильмов
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


class Director(db.Model):  # таблица директоров фильмов
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class Genre(db.Model):  # таблица жанров фильмов
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


class MovieSchema(Schema):  # "Схема" фильмов, которая, в том числе укажет жанр и режиссёра
    id = fields.Int(dump_only=True)
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre = fields.Nested("GenreSchema")
    director = fields.Nested("DirectorSchema")


class DirectorSchema(Schema):  # "Схема" директоров фильмов
    id = fields.Int(dump_only=True)
    name = fields.Str()


class GenreSchema(Schema):  # "Схема" жанров фильмов
    id = fields.Int(dump_only=True)
    name = fields.Str()


@movie_ns.route('/')  # роут, который вернёт все фильмы, в том числе по фильтрам: режиссёру и жанру. С постраничным выводом.
@movie_ns.doc(params={'page': 'Номер страницы',  # пояснительная документация
                      'director_id': 'ID режиссера',
                      'genre_id': 'ID жанра'})
class MoviesView(Resource):
    def get(self):
        try:
            page = 1
            movie_session = db.session.query(Movie)

            if request.args.get('director_id'):
                movie_session = movie_session.filter(Movie.director_id == request.args.get('director_id'))
            if request.args.get('genre_id'):
                movie_session = movie_session.filter(Movie.genre_id == request.args.get('genre_id'))
            if request.args.get('page'):
                page = int(request.args.get('page'))

            movies = movie_session\
                .join(Genre)\
                .join(Director)\
                .paginate(page=page, per_page=5, error_out=False).items
            return jsonify(MovieSchema(many=True).dump(movies))
        except Exception as e:
            return e, 400


@movie_ns.route('/<int:pk>')  # роут, который вернёт определённый фильм по id
class MovieView(Resource):
    def get(self, pk):
        if not MovieSchema().dump(Movie.query.get(pk)):
            return "Нет такого фильма", 404
        return MovieSchema().dump(Movie.query.get(pk)), 200


if __name__ == '__main__':
    app.run(debug=True)
