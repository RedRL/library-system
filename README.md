# Library System

## Overview
The Library System is a microservices-based application designed to manage books and loans. The system includes the following services:
- Books Service
- Loans Service
- MongoDB for data storage
- NGINX for reverse proxy and load balancing

## Services
1. **Books Service**: Manages books and their ratings.
2. **Loans Service**: Manages book loans.
3. **MongoDB**: Stores data for the Books and Loans services.
4. **NGINX**: Acts as a reverse proxy and load balancer for the services.

## Features
- Persistent storage using MongoDB.
- Load balancing for Loans Service using NGINX.
- High availability with automatic restart on failure.
- Access control enforced by NGINX.

## Actors
- **Librarian**: Can manage books and ratings.
- **Member**: Can manage loans.
- **Public**: Can view books, ratings, top books, and loans.

## Accessing the Services

### Books Service (Librarian)
- **Base URL**: `http://localhost:5001`
- **Actions**:
  - **GET /books**
  - **POST /books**
  - **PUT /books/{id}**
  - **DELETE /books/{id}**
  - **GET /ratings**
  - **POST /ratings**

#### Example Book
```json
{
  "title": "Harry Potter and the Philosopher's Stone",
  "authors": "J. K. Rowling",
  "ISBN": "9781408855652",
  "genre": "Fantasy",
  "publisher": "Bloomsbury Publishing",
  "publishedDate": "2014-01-01",
  "id": "6679c66575e6aa5d0b6a46e9"
}
```

### Loans Service (Member)
- **Base URL**: `http://localhost:5002`
- **Actions**:
  - **GET /loans**
  - **POST /loans**
  - **DELETE /loans/{id}**

#### Example Loan
```json
{
  examplewle
  {
    "memberName":"RL",
    "ISBN":"9781408855652",
    "loanDate":"2024-06-30"
}```

### Public Access
- **Base URL**: `http://localhost:80`
- **Actions**:
  - **GET /books**
  - **GET /ratings**
  - **GET /top**
  - **GET /loans**
  - **POST /ratings/{id}/values**

## NGINX Configuration
The NGINX server is configured to:
- Route requests to the correct service.
- Enforce access control based on the actor.
- Load balance the Loans Service using weighted round-robin scheduling.
