# Booking System

A Django REST API for managing service providers, services, time slots, customer bookings, payments, and administrative operations.

The project is designed as a backend-focused service booking platform with **JWT authentication, role-based access control, transactional booking logic, API documentation, PDF reporting, filtering/searching, and automated testing**.

## Key Features

*  JWT-based authentication
*  Role-based access control
    * Customer
    * Service Provider
    * Admin
*  Service and time-slot management
*  Customer booking management
*  Booking lifecycle management
    * Pending
    * Confirmed
    * Rejected
    * Canceled
    * Completed
*  Simulated payment workflow
*  PDF invoice and booking reports
*  Filtering, searching, and ordering
*  Customer, provider, and admin statistics
*  Swagger / OpenAPI API documentation
*  Automated test suite
*  Transactional booking creation with database locking
*  Role- and ownership-based API permissions

---

##  Technical Highlights

This project demonstrates practical backend development concepts including:

* **Django & Django REST Framework**
* RESTful API design
* Custom Django User model
* JWT authentication
* Custom permission classes
* Role-based authorization
* Object-level ownership checks
* `transaction.atomic()` for transactional operations
* `select_for_update()` for protecting booking operations from race conditions
* Django ORM relationships and query optimization
* Filtering, searching, and ordering with DRF
* API documentation with Swagger / OpenAPI
* PDF generation with ReportLab
* Automated testing with Django's Test Framework
* Git and GitHub project organization

---

##  Tech Stack

| Technology            | Usage                           |
| --------------------- | ------------------------------- |
| Python                | Backend programming             |
| Django                | Web framework                   |
| Django REST Framework | REST API development            |
| Simple JWT            | Authentication                  |
| SQLite                | Development database            |
| drf-yasg              | Swagger / OpenAPI documentation |
| ReportLab             | PDF report generation           |
| django-filter         | API filtering                   |
| Git / GitHub          | Version control                 |

---

##  Project Structure

```text
booking-system/
│
├── bookingsys/
│   ├── manage.py
│   │
│   ├── bookingsys/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   ├── users/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py
│   │   ├── filters.py
│   │   ├── admin.py
│   │   └── tests.py
│   │
│   ├── services/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── tests.py
│   │
│   └── bookings/
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       ├── reports.py
│       └── tests.py
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

##  Installation

### 1. Clone the repository

```bash
git clone https://github.com/nioovns/booking-system.git
cd booking-system
```

### 2. Create a virtual environment

#### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply migrations

```bash
cd bookingsys
python manage.py migrate
```

### 5. Create an admin account

```bash
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

---

##  API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/swagger/
```

ReDoc:

```text
http://127.0.0.1:8000/redoc/
```

Django Admin:

```text
http://127.0.0.1:8000/admin/
```

Swagger provides an interactive interface for exploring and testing the API endpoints.

### Authentication

The API uses JWT authentication.

After logging in, obtain an access token and authorize requests through Swagger using:

```text
Bearer <access_token>
```

---

##  User Roles

### Customer

Customers can:

* Register and log in
* Browse services
* View available time slots
* Create bookings
* View their bookings
* Cancel eligible bookings
* Make simulated payments
* View booking/payment information
* Export their booking reports

### Service Provider

Service providers can:

* Manage their services
* Create and manage time slots
* View customer bookings
* Confirm or reject bookings
* View provider statistics
* Export provider reports

### Admin

Administrators have access to:

* User management
* Role management
* Service and booking management
* Platform statistics
* Administrative reports
* PDF exports

---

##  Booking Workflow

A typical booking flow is:

```text
Customer
   │
   ▼
Browse Services
   │
   ▼
Select Available Time Slot
   │
   ▼
Create Booking
   │
   ▼
Pending
   │
   ├──► Rejected
   │
   └──► Confirmed
             │
             ▼
          Payment
             │
             ▼
           Paid
             │
             ▼
        Completed
```

Booking creation is handled transactionally. The selected time slot is locked during the booking operation to reduce the possibility of two customers booking the same slot concurrently.

---

##  Payment System

The project includes a **simulated payment workflow** for demonstrating backend payment logic.

The payment process includes:

* Payment validation
* Transaction ID generation
* Booking payment status management
* Successful payment handling
* Payment history

> This project does not process real financial transactions.

---

##  PDF Reports

The backend generates PDF documents for different use cases, including:

* Customer booking reports
* Provider booking reports
* Administrative statistics
* Booking invoices

PDF generation is implemented using **ReportLab**.

---

##  API Filtering & Search

Several endpoints support:

* Filtering
* Searching
* Ordering

For example, bookings can be filtered by:

* Status
* Payment status
* Service
* Provider
* Customer

Search can also be performed using relevant service and user information.

---

##  Testing

The project includes automated tests covering the main application components.

Current test result:

```text
80 tests
80 passed
0 failed
```

Run the complete test suite with:

```bash
python manage.py test
```

Tests can also be executed separately:

```bash
python manage.py test users
python manage.py test services
python manage.py test bookings
```

---

##  Security & Authorization

The API uses several layers of authorization:

* JWT authentication
* Role-based permissions
* User ownership checks
* Provider/service ownership validation
* Booking ownership validation
* Protected administrative operations

Sensitive development files such as environment variables, SQLite databases, virtual environments, IDE configuration files, and Python cache files are excluded through `.gitignore`.

---

##  Backend Design Considerations

One of the main goals of the project was to go beyond basic CRUD operations and implement realistic backend behavior.

Examples include:

* Transactional booking creation
* Database row locking for time-slot allocation
* Role-specific querysets
* Custom permission classes
* Booking state transitions
* Automatic time-slot availability management
* Validation of service and time-slot relationships
* Separate serializers for different API operations
* PDF report generation
* Automated testing of application behavior

---

##  API Endpoint Overview

### Users

```text
POST   /api/users/register/
POST   /api/users/login/
GET    /api/users/me/
PATCH  /api/users/update_me/
POST   /api/users/change_password/
```

### Services

```text
GET    /api/services/services/
POST   /api/services/services/
GET    /api/services/services/{id}/
PATCH  /api/services/services/{id}/
DELETE /api/services/services/{id}/
GET    /api/services/services/{id}/available_slots/
```

### Time Slots

```text
GET    /api/services/time-slots/
POST   /api/services/time-slots/
PATCH  /api/services/time-slots/{id}/
DELETE /api/services/time-slots/{id}/
```

### Bookings

```text
GET    /api/bookings/bookings/
POST   /api/bookings/bookings/
GET    /api/bookings/bookings/{id}/
PATCH  /api/bookings/bookings/{id}/
POST   /api/bookings/bookings/{id}/confirm/
POST   /api/bookings/bookings/{id}/reject/
POST   /api/bookings/bookings/{id}/cancel/
POST   /api/bookings/bookings/{id}/payment_info/
```

### Payments

```text
GET    /api/bookings/payments/
POST   /api/bookings/payments/create_payment/
GET    /api/bookings/payments/{id}/
```

For the complete list of endpoints and request/response schemas, see the Swagger documentation.

---

##  Future Improvements

Possible future improvements include:

* PostgreSQL for production deployment
* Redis and Celery for asynchronous tasks
* Real payment gateway integration
* Email/SMS notifications
* Docker containerization
* CI/CD with GitHub Actions
* Production deployment
* Improved API throttling and rate limiting
* More extensive integration and concurrency tests

---

##  Project Goals

This project was developed to strengthen practical backend development skills with Django and Django REST Framework, with particular focus on:

* REST API architecture
* Authentication and authorization
* Database design
* Business logic
* Concurrency handling
* Testing
* API documentation
* Backend security
* Clean project structure

---

##  License

This project is developed for educational and portfolio purposes.
