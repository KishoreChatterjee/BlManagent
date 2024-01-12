from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import *
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics,status,views,permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.core.mail import send_mail
from django.conf import settings

@api_view(['POST'])
def createAuthor(request):
    try:
        if not request.user.username:
            raise Exception("User is not signed in")
        if not request.user.canCreateAuthor:
            raise Exception("User is not authorized")
       
        # JSON parsing and validation
        try:
            requestBodyToDict = json.loads(request.body)
        except json.JSONDecodeError:
            raise Exception("Invalid JSON body")

        required_fields = ['name', 'email']
        for field in required_fields:
            if field not in requestBodyToDict:
                raise Exception(f"Missing field: {field}")

        # Author creation logic
        emailFromPostman = requestBodyToDict['email']
        checkEmailExists = Author.objects.filter(email=emailFromPostman).exists()

        if checkEmailExists:
            raise Exception("Author is already added to the database")
        else:
            nameFromPostmanBody = requestBodyToDict['name']
            email = requestBodyToDict['email']

            savingNameToDb = Author(name=nameFromPostmanBody, email=email)
            savingNameToDb.save()

            return JsonResponse({
                "message": f"{nameFromPostmanBody} added to Author table"
            })

    except Exception as ex:
        return JsonResponse({
            "message": str(ex),
            "status": "failed"
        }, status=status.HTTP_409_CONFLICT)

@csrf_exempt
def createBooks(request):
    try:
        requestBodyToDict = json.loads(request.body)
        authorId = requestBodyToDict['author_id']
        author = Author.objects.get(id=authorId)
        Books = requestBodyToDict['title']

        bookLists = []

        for book in Books:
            bookLists.append(book)
            newBook = Book.objects.create(title=book, author=author)

        return JsonResponse({
            "message": f"{bookLists} of {author.name} added successfully"
        })
    except KeyError:
        return JsonResponse({
            "Error": "Invalid request body. 'author_id' or 'title' field is missing."
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            "Error": "Invalid JSON in request body."
        }, status=400)
    except Author.DoesNotExist:
        return JsonResponse({
            "Error": "Author with the given ID does not exist."
        }, status=404)

def getBooknamesFromAuthor(request):
    try:
        authId = (json.loads(request.body))['authorId']
        author = Author.objects.get(id=authId)
        booksQuerySet = Book.objects.filter(author=author)
        bookLists = []

        for book in booksQuerySet:
            bookLists.append(book.title)

        return JsonResponse({
            "message": f"{bookLists} of {author.name} retrieved successfully"
        })
    except KeyError:
        return JsonResponse({
            "Error": "Invalid request body. 'authorId' field is missing."
        }, status=400)
    except json.JSONDecodeError:
        return JsonResponse({
            "Error": "Invalid JSON in request body."
        }, status=400)
    except Author.DoesNotExist:
        return JsonResponse({
            "Error": "Author with the given ID does not exist."
        }, status=404)

@csrf_exempt
def updateAuthor(request):
    try:
        data = json.loads(request.body)
        authId = data.get('authorId')
        new_name = data.get('changedName')

        if authId is not None and new_name is not None:
            try:
                authObj = Author.objects.get(id=authId)
                old_name = authObj.name
                Author.objects.filter(id=authId).update(name=new_name)

                return JsonResponse({
                    "message": f"{old_name} is replaced by {new_name}"
                })
            except Author.DoesNotExist:
                return JsonResponse({
                    "error": "Author with the given ID does not exist."
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse({
                "error": "Invalid request body. 'authorId' or 'changedName' field is missing."
            }, status=status.HTTP_400_BAD_REQUEST)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def deleteAuthor(request):
    try:
        data = json.loads(request.body)
        authId = data.get('authorId')

        if authId is not None:
            try:
                authObj = Author.objects.get(id=authId)
                name = authObj.name
                authObj.delete()

                return JsonResponse({
                    "message": f"{name} is deleted from the author table"
                })
            except Author.DoesNotExist:
                return JsonResponse({
                    "error": "Author with the given ID does not exist."
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return JsonResponse({
                "error": "Invalid request body. 'authorId' field is missing."
            }, status=status.HTTP_400_BAD_REQUEST)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def register(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "Method not supported",
            "status": "Failed"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    try:
        data = json.loads(request.body)
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        canCreateAutor = data.get("canCreateAuthor")

        if not username or not email or not password:
            return JsonResponse({
                "error": "Input fields should not be empty"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(email=email, username=username, password=password, canCreateAuthor = canCreateAutor)
        user.save()
        
        send_mail(
            "Congratualations",
            "We are so happy to have you onboard.",
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        return JsonResponse({
            "message": f"User {username} registered successfully"
        }, status=status.HTTP_201_CREATED)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "Method not supported",
            "status": "Failed"
        }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({
                "error": "Input fields should not be empty"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(request, username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)

            return JsonResponse({
                "access-token": str(refresh.access_token),
                "refresh-token": str(refresh)
            })
        else:
            return JsonResponse({
                "error": "Invalid username or password."
            }, status=status.HTTP_401_UNAUTHORIZED)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body."
        }, status=status.HTTP_400_BAD_REQUEST)