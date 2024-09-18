from flask_restful import Resource,reqparse
from model import *
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import json ,jsonify ,request
from datetime import datetime, timedelta
from sqlalchemy.orm import Session


class SectionResource(Resource):
    @jwt_required()
    def get(self, section_id=None):
        if section_id:
            section = Section.query.get_or_404(section_id)
            return {
                "id": section.id,
                "name": section.name,
                "description": section.description
            }, 200
        else:
            sections = Section.query.all()
            section_list = [{"id": section.id, "name": section.name, "description": section.description} for section in sections]
            return {"sections": section_list}, 200
    # def get(self):
    #     sections = Section.query.all()
    #     section_list = [
    #         {
    #             "id": section.id,
    #             "name": section.name,
    #             "description": section.description
    #         } for section in sections
    #     ]
    #     return {"sections": section_list}, 200
        
    @jwt_required()
    def post(self):
        section_args = reqparse.RequestParser()
        section_args.add_argument('name', type=str, required=True, help="Name of the section is required")
        section_args.add_argument('description', type=str, required=False)
        args = section_args.parse_args()
        
        new_section = Section(name=args['name'], description=args.get('description'))
        db.session.add(new_section)
        db.session.commit()
        
        return {"message": "Section created", "section_id": new_section.id}, 201

    @jwt_required()
    def put(self, section_id):
        section_args = reqparse.RequestParser()
        section_args.add_argument('name', type=str, required=True, help="Name of the section is required")
        section_args.add_argument('description', type=str, required=False)
        args = section_args.parse_args()
        section = Section.query.get(section_id)
        if not section:
            return {"message": "Section not found"}, 404

        section.name = args['name']
        section.description = args.get('description')
        db.session.commit()
        return {"message": "Section updated"}

    @jwt_required()
    def delete(self, section_id):
        section = Section.query.get(section_id)
        if not section:
            return {"message": "Section not found"}, 404
        db.session.delete(section)
        db.session.commit()
        return {"message": "Section deleted"}, 200

class BookResource(Resource):
    @jwt_required()
    def get(self, section_id, book_id=None):
        if book_id:
            book = Book.query.filter_by(id=book_id, section_id=section_id).first()
            if not book:
                return {"message": "No book found"}, 404
            return {
                "id": book.id,
                "title": book.title,
                "authors": book.authors,
                "content": book.content,
                "rating": book.rating
            }, 200

        user_id = get_jwt_identity()
        books = Book.query.filter_by(section_id=section_id).all()
        if not books:
            return {"message": "No books found in this section"}, 404
        return {
            "books": [
                {
                    "id": book.id,
                    "title": book.title,
                    "authors": book.authors,
                    "content": book.content,
                    "rating": book.rating,
                    "status": BookStatus.query.filter_by(book_id=book.id, user_id=user_id).first().status if BookStatus.query.filter_by(book_id=book.id, user_id=user_id).first() else 'request'
                }
                for book in books
            ]
        }, 200
        

    @jwt_required()
    def post(self, section_id):
        book_args = reqparse.RequestParser()
        book_args.add_argument('title', type=str, required=True, help="Title of the book is required")
        book_args.add_argument('content', type=str, required=True, help="Content of the book is required")
        book_args.add_argument('authors', type=str, required=True, help="Authors of the book are required")
        book_args.add_argument('rating', type=float, required=False, help="Rating of the book is optional")

        args = book_args.parse_args()
        print("Received book arguments:", args)

        section = Section.query.get(section_id)
        if not section:
            return {"message": "Section not found"}, 404

        if not args['title'] or not args['content'] or not args['authors']:
            return {"message": "Missing required fields"}, 400
        
        if args['rating'] is not None and not isinstance(args['rating'], float):
            return {"message": "Rating must be a float"}, 400

        new_book = Book(
            title=args['title'],
            content=args['content'],
            authors=args['authors'],
            rating=args.get('rating'),
            section_id=section_id
        )

        print("New book to add:", new_book)
        db.session.add(new_book)
        db.session.commit()

        return {"message": "Book added successfully", "book_id": new_book.id}, 201
    
    @jwt_required()
    def put(self, section_id, book_id):
        book = Book.query.filter_by(id=book_id, section_id=section_id).first()
        if not book:
            return {"message": "Book not found"}, 404

        data = request.get_json()
        book.title = data.get('title', book.title)
        book.authors = data.get('authors', book.authors)
        book.content = data.get('content', book.content)
        book.rating = data.get('rating', book.rating)

        db.session.commit()
        return jsonify({"message": "Book updated", "book": {
            "id": book.id,
            "title": book.title,
            "authors": book.authors,
            "content": book.content,
            "rating": book.rating
        }})

    @jwt_required()
    def delete(self, section_id, book_id):
        book = Book.query.filter_by(id=book_id, section_id=section_id).first()
        if not book:
            return {"message": "Book not found"}, 404
        
        BookStatus.query.filter_by(book_id=book_id).delete()
        BookIssued.query.filter_by(book_id=book_id).delete()

        db.session.delete(book)
        db.session.commit()
        return {"message": "Book deleted"}

