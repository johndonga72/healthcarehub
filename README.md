# Healthcare Website

A Flask-based Healthcare Web Application that provides healthcare-related information and AI-powered assistance. The application integrates Groq AI and YouTube Data API to deliver intelligent responses and relevant healthcare resources.

## Features

* AI-powered healthcare chatbot using Groq API
* Healthcare information and guidance
* YouTube video recommendations related to healthcare topics
* User-friendly web interface
* Flask backend with integrated frontend (HTML, CSS, JavaScript)
* Static assets support (CSS, Images, JS)
* Responsive design

## Tech Stack

### Backend

* Python
* Flask

### APIs

* Groq API
* YouTube Data API

### Libraries

* Requests
* NetworkX
* Matplotlib
* RDFLib
* Pillow
* Google API Python Client
* ReportLab
* BeautifulSoup4

### Frontend

* HTML
* CSS
* JavaScript

## Project Structure

```text
healthcare_website/
│
├── app.py
├── requirements.txt
├── README.md
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   └── index.html
│
└── venv/
```

## Installation

### Clone the Repository

```bash
git clone <repository-url>
cd healthcare_website
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux/macOS

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python app.py
```

The application will start locally at:

```text
http://127.0.0.1:5000
```

## Deployment

This project can be deployed on:

* Render
* Railway
* Heroku
* AWS
* Azure

### Render Deployment

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn app:app
```

## API Configuration

Configure the following API keys before running the application:

* Groq API Key
* YouTube Data API Key

It is recommended to use environment variables for production deployments.

## Future Enhancements

* User authentication
* Patient dashboard
* Appointment booking
* Medical report analysis
* Advanced AI health assistant
* Cloud database integration

## Author

John Babu

Python Full Stack Developer | Data Analysis Enthusiast

## License

This project is developed for learning and educational purposes.
