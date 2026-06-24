# Install required packages (run this in your environment if needed)
import os
import requests
import networkx as nx
import matplotlib.pyplot as plt
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from groq import Groq
import datetime
import time
import re
import io
import tempfile
from PIL import Image
import googleapiclient.discovery
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from flask_migrate import Migrate
from models import db, Appointment
from flask import request, jsonify
from datetime import datetime
load_dotenv()
# Setup Flask
app = Flask(__name__)
database_url = os.getenv("DATABASE_URL")
# Render sometimes provides postgres://
if not database_url:
    raise ValueError("DATABASE_URL environment variable is not set.")
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1
    )
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
# Setup Groq API (replace with your actual key)
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
print(os.getenv("GROQ_API_KEY"))
# Setup YouTube API (replace with your actual key)
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))

# Initialize RDF Knowledge Graph
g = Graph()
EX = Namespace("http://example.org/ontology#")
g.bind("ex", EX)

# Expanded Keyword Lists
DISEASES = []  # Will be populated from load_disease_dataset
SYMPTOMS = ["fever", "cough", "fatigue", "headache", "nausea", "chest pain", "shortness of breath", "rash", "dizziness", "joint pain", "increased thirst", "frequent urination", "blurry vision", "slow healing wounds", "tiredness", "high blood sugar", "body pains"]
TREATMENTS = ["insulin therapy", "vaccination", "antibiotics", "chemotherapy", "surgery", "physiotherapy", "inhalers", "antiviral therapy", "painkillers", "lifestyle changes", "metformin", "diet control", "blood sugar monitoring"]
MEDICINES = ["paracetamol", "ibuprofen", "aspirin", "metformin", "insulin", "amoxicillin", "azithromycin", "oseltamivir", "prednisone", "albuterol"]
CAUSES = ["obesity", "virus", "smoking", "genetics", "stress", "bacteria", "poor diet", "pollution", "injury", "aging", "sedentary lifestyle", "sugar intake"]
DIET = ["diet", "nutrition", "food", "meal plan", "calories", "vitamins", "minerals", "supplements"]
HEALTH = ["health", "wellness", "fitness", "exercise", "workout", "physical activity", "bmi"]
LIFESTYLE = ["lifestyle", "habits", "sleep", "stress management", "mental health"]
SKIN_CARE = ["skin care", "dermatology", "acne", "eczema", "psoriasis", "moisturizer", "sunscreen"]

# Add blocked keywords for non-medical inputs
BLOCKED_KEYWORDS = [
    # Movie-related
    "movie", "film", "cinema", "bollywood", "hollywood", "titanic", "avengers", "inception",
    # Hero/celebrity names (sample)
    "salman", "shahrukh", "deepika", "ranbir", "brad pitt", "tom cruise", "angelina jolie",
    # Places (sample)
    "paris", "london", "new york", "tokyo", "delhi", "mumbai", "california", "beach", "mountain"
]

# New disease dataset for visualization
disease_data = {
    "diabetes": {
        "hasInfo": "Diabetes (Type 1 and Type 2)",
        "hasSymptom": ["high blood sugar", "increased thirst", "fatigue", "blurry vision", "slow healing wounds"],
        "treated_by": ["insulin therapy", "metformin", "lifestyle changes", "blood sugar monitoring"],
        "causing_by": ["obesity", "genetics", "poor diet", "sedentary lifestyle"]
    },
    "covid": {
        "hasInfo": "COVID-19 (Coronavirus Disease)",
        "hasSymptom": ["fever", "cough", "shortness of breath", "loss of taste", "fatigue"],
        "treated_by": ["vaccination", "antiviral therapy", "oxygen therapy", "rest"],
        "causing_by": ["SARS-CoV-2", "virus", "close contact"]
    },
    "hypertension": {
        "hasInfo": "High Blood Pressure",
        "hasSymptom": ["headache", "dizziness", "nosebleeds", "blurred vision"],
        "treated_by": ["beta blockers", "lifestyle changes", "diuretics", "ACE inhibitors"],
        "causing_by": ["stress", "poor diet", "obesity", "smoking"]
    },
    "asthma": {
        "hasInfo": "Asthma",
        "hasSymptom": ["wheezing", "shortness of breath", "chest tightness", "coughing"],
        "treated_by": ["inhalers", "steroids", "bronchodilators", "allergy management"],
        "causing_by": ["allergies", "pollution", "exercise", "cold air"]
    },
    "cancer": {
        "hasInfo": "Cancer (General)",
        "hasSymptom": ["weight loss", "fatigue", "pain", "lumps", "skin changes"],
        "treated_by": ["chemotherapy", "surgery", "radiation therapy", "immunotherapy"],
        "causing_by": ["genetics", "smoking", "radiation", "chemical exposure"]
    },
    "flu": {
        "hasInfo": "Influenza",
        "hasSymptom": ["fever", "cough", "sore throat", "muscle aches", "fatigue"],
        "treated_by": ["antiviral therapy", "rest", "hydration", "vaccination"],
        "causing_by": ["influenza virus", "close contact", "poor immunity"]
    },
    "pneumonia": {
        "hasInfo": "Pneumonia",
        "hasSymptom": ["fever", "cough", "chest pain", "shortness of breath", "chills"],
        "treated_by": ["antibiotics", "oxygen therapy", "rest", "hydration"],
        "causing_by": ["bacteria", "virus", "fungi", "aspiration"]
    },
    "tuberculosis": {
        "hasInfo": "Tuberculosis (TB)",
        "hasSymptom": ["cough", "weight loss", "night sweats", "fever", "chest pain"],
        "treated_by": ["antibiotics", "long-term therapy", "isolation"],
        "causing_by": ["mycobacterium tuberculosis", "close contact", "poor immunity"]
    },
    "malaria": {
        "hasInfo": "Malaria",
        "hasSymptom": ["fever", "chills", "headache", "nausea", "muscle pain"],
        "treated_by": ["antimalarial drugs", "mosquito control", "supportive care"],
        "causing_by": ["plasmodium parasite", "mosquito bites"]
    },
    "hepatitis": {
        "hasInfo": "Hepatitis (A, B, C)",
        "hasSymptom": ["jaundice", "fatigue", "nausea", "abdominal pain", "dark urine"],
        "treated_by": ["antiviral therapy", "vaccination", "lifestyle changes"],
        "causing_by": ["virus", "alcohol", "toxins", "contaminated food/water"]
    },
    "arthritis": {
        "hasInfo": "Arthritis",
        "hasSymptom": ["joint pain", "swelling", "stiffness", "reduced mobility"],
        "treated_by": ["painkillers", "physiotherapy", "anti-inflammatory drugs", "surgery"],
        "causing_by": ["aging", "autoimmune response", "injury", "genetics"]
    },
    "stroke": {
        "hasInfo": "Stroke",
        "hasSymptom": ["sudden weakness", "confusion", "slurred speech", "vision loss"],
        "treated_by": ["clot-busting drugs", "surgery", "rehabilitation", "blood thinners"],
        "causing_by": ["hypertension", "smoking", "blood clots", "heart disease"]
    },
    "heart disease": {
        "hasInfo": "Heart Disease",
        "hasSymptom": ["chest pain", "shortness of breath", "fatigue", "palpitations"],
        "treated_by": ["statins", "surgery", "lifestyle changes", "beta blockers"],
        "causing_by": ["obesity", "smoking", "high cholesterol", "hypertension"]
    },
    "alzheimer's": {
        "hasInfo": "Alzheimer's Disease",
        "hasSymptom": ["memory loss", "confusion", "difficulty speaking", "mood changes"],
        "treated_by": ["cholinesterase inhibitors", "therapy", "lifestyle changes"],
        "causing_by": ["aging", "genetics", "brain plaque buildup"]
    }
}
# Load the new disease dataset with extended relationships
def load_disease_dataset():
    dataset = {
        "Diabetes": "Diabetes is a chronic endocrine condition where the body struggles to regulate blood sugar levels due to insufficient insulin production or resistance. Common symptoms include increased thirst, frequent urination, fatigue, blurry vision, slow healing wounds, tiredness, and high blood sugar. It is often caused by obesity, poor diet, genetics, sedentary lifestyle, and sugar intake. Treatments typically involve insulin therapy, metformin, lifestyle changes, diet control, and blood sugar monitoring. Diabetes includes Type 1 and Type 2 variants.",
        "Hypertension": "Hypertension, or high blood pressure, is a common cardiovascular condition where the force of blood against artery walls is consistently elevated, often showing no clear symptoms initially. Over time, it may cause headaches, fatigue, or chest pain, increasing risks of heart disease and stroke. Management includes medications like ACE inhibitors or beta-blockers, coupled with reduced salt intake and stress management techniques.",
        "Asthma": "Asthma is a chronic respiratory disorder characterized by inflamed airways, leading to breathing difficulties, wheezing, coughing, and chest tightness, often triggered by allergens or exercise. Symptoms can vary in intensity and frequency, requiring careful monitoring. Treatments include inhalers with bronchodilators or corticosteroids to open airways and reduce inflammation, alongside avoiding known triggers.",
        "Migraine": "Migraine is an acute neurological condition marked by intense, throbbing headaches, often accompanied by nausea, vomiting, and sensitivity to light or sound. Symptoms may include visual disturbances like auras, lasting hours to days if untreated. Painkillers such as ibuprofen or triptans are common treatments, along with rest in a quiet, dark environment to alleviate discomfort.",
        "Arthritis": "Arthritis is a chronic musculoskeletal condition involving inflammation of the joints, causing pain, stiffness, and swelling, particularly in older adults or after injury. Symptoms often worsen with activity or weather changes, limiting mobility over time. Treatments range from painkillers like NSAIDs to physical therapy and, in severe cases, joint replacement surgery to restore function.",
        # Placeholder diseases (example subset; replace with full 368 entries)
        "Disease_1": "Disease_1 is a condition with unspecified symptoms and treatments. Common symptoms include generic symptom 1, generic symptom 2. Treatments typically involve generic treatment 1, generic treatment 2.",
        "Disease_2": "Disease_2 is a condition with unspecified symptoms and treatments. Common symptoms include generic symptom 3, generic symptom 4. Treatments typically involve generic treatment 3, generic treatment 4.",
        # ... Add remaining Disease_3 to Disease_368 as needed ...
    }
    return dataset
# Parse disease descriptions for the knowledge graph with extended relationships
def parse_disease_description(description):
    symptoms = []
    treatments = []
    causes = []
    symptom_match = re.search(r"symptoms include (.*?)(?:\.|$)", description, re.IGNORECASE)
    if symptom_match:
        symptoms = [s.strip() for s in symptom_match.group(1).split(",")]
    treatment_match = re.search(r"treatments (?:typically )?(?:include|involve) (.*?)(?:\.|$)", description, re.IGNORECASE)
    if treatment_match:
        treatments = [t.strip() for t in treatment_match.group(1).split(",")]
    cause_match = re.search(r"caused by (.*?)(?:\.|$)", description, re.IGNORECASE)
    if cause_match:
        causes = [c.strip() for c in cause_match.group(1).split(",")]
    return symptoms, treatments, causes
# Populate DISEASES from the dataset with case-insensitive handling
disease_dataset = load_disease_dataset()
DISEASES = [disease.lower() for disease in disease_dataset.keys()]
MEDICAL_KEYWORDS = DISEASES + SYMPTOMS + TREATMENTS + MEDICINES + CAUSES + DIET + HEALTH + LIFESTYLE + SKIN_CARE
# Static Dosage Data
DEFAULT_DOSAGE = {
    "paracetamol": "500-1000 mg every 4-6 hours, max 4000 mg/day",
    "ibuprofen": "200-400 mg every 4-6 hours, max 3200 mg/day",
    "aspirin": "325-650 mg every 4-6 hours, max 4000 mg/day",
    "metformin": "500-1000 mg twice daily with meals",
    "insulin": "Dosage varies, consult a doctor",
    "amoxicillin": "250-500 mg every 8 hours",
    "azithromycin": "500 mg on day 1, then 250 mg daily for 4 days",
    "oseltamivir": "75 mg twice daily for 5 days",
    "prednisone": "5-60 mg daily, varies by condition",
    "albuterol": "2 puffs every 4-6 hours as needed"
}
medicine_data = DEFAULT_DOSAGE.copy()

# Medicine Uses
MEDICINE_USES = {
    "paracetamol": "Relieves pain and reduces fever",
    "ibuprofen": "Reduces inflammation, pain, and fever",
    "aspirin": "Relieves pain, reduces inflammation, prevents clots",
    "metformin": "Controls blood sugar in type 2 diabetes",
    "insulin": "Manages blood sugar levels in diabetes",
    "amoxicillin": "Treats bacterial infections",
    "azithromycin": "Treats bacterial infections",
    "oseltamivir": "Treats influenza (flu)",
    "prednisone": "Reduces inflammation and suppresses immune response",
    "albuterol": "Relieves asthma symptoms and bronchospasm"
}

# Online Pharmacy Links
ONLINE_PHARMACIES = {
    "Apollo Pharmacy": "https://www.apollopharmacy.in/search-medicines/",
    "Netmeds": "https://www.netmeds.com/catalogsearch/result?q=",
    "1mg": "https://www.1mg.com/search/all?name=",
    "PharmEasy": "https://pharmeasy.in/search/all?name="
}

# Global list for user-submitted news
user_news = []

# Default news articles as fallback
DEFAULT_NEWS = [
    "- [Breakthrough in Cancer Research Announced](https://example.com/cancer-breakthrough) (April 5, 2025)",
    "- [New Guidelines for Diabetes Management Released](https://example.com/diabetes-guidelines) (April 4, 2025)"
]

# College info and about section
college_info = """
<h2 style="text-align: center;">Sir. C. R. Reddy College of Engineering(AUTONOMOUS)</h2>
<p><strong>Address:</strong> Vattluru Railway gate, Eluru, Andhra Pradesh 534007</p>
<p><strong>About:</strong> Sir C.R. Reddy College of Engineering(A) is the first Engineering College in Andhra Pradesh sanctioned and recognized by All India Council for Technical Education (AICTE).</p>
<p><strong>Department:</strong> ARTIFICIAL INTELLIGENCE AND DATA SCIENCE</p>
<p><strong>Project Guide:</strong> MADHAVI LATHA MADAM[M.Tech]</p>
"""
team_members = [
    {"name": "Bhavana", "role": "Frontend Developer", "description": "Responsible for UI/UX design and implementation"},
    {"name": "John", "role": "Backend Developer", "description": "Handled the knowledge graph integration"},
    {"name": "Sowmya", "role": "AI Specialist", "description": "Implemented the NLP components"},
    {"name": "Samuel", "role": "Data Engineer", "description": "Managed data collection and preprocessing"},
    {"name": "Bharath", "role": "Testing & Deployment", "description": "Ensured system reliability and deployment"}
]
about_section = """
<h2 style="text-align: center;">About Hybrid Healthcare Assistant</h2>
<div style="text-align: justify;">
<p>The Hybrid Healthcare Assistant (HHA) is a final year project developed by our team at Sir. C. R. Reddy College of Engineering(AUTONOMOUS). This system combines advanced AI technologies with an extended medical knowledge graph and practical healthcare tools.</p>
<p>The assistant offers a hybrid approach by:</p>
<ul>
    <li>Providing AI-driven answers validated by an extended knowledge graph</li>
    <li>Calculating BMI, Body Fat, and Ideal Weight for personal health tracking</li>
    <li>Offering an AI-powered symptom checker with severity prediction</li>
    <li>Generating personalized health reports in PDF format</li>
    <li>Delivering real-time health news updates</li>
    <li>Locating nearby hospitals</li>
    <li>Delivering educational medical videos</li>
    <li>Visualizing health-related knowledge graphs</li>
    <li>Facilitating interactive health conversations</li>
    <li>Checking medicine availability with online purchase links</li>
</ul>
</div>
"""

# Modified initialize_graph with only 4 RDF relationships
def initialize_graph(query=None):
    g.remove((None, None, None))
    # Define 4 RDF relationships
    g.bind("ex", EX)
    EX.hasSymptom = URIRef(EX + "hasSymptom")
    EX.treated_by = URIRef(EX + "treated_by")
    EX.causing_by = URIRef(EX + "causing_by")
    EX.hasInfo = URIRef(EX + "hasInfo")
    
    if not query:
        return
    query = query.lower().strip()
    matched_disease = next((d for d in disease_dataset.keys() if d.lower() == query), None)
    if matched_disease:
        description = disease_dataset[matched_disease]
        symptoms, treatments, causes = parse_disease_description(description)
        g.add((EX[query], RDF.type, EX["Disease"]))
        g.add((EX[query], EX["hasInfo"], Literal(description)))
        for symptom in symptoms:
            g.add((EX[query], EX["hasSymptom"], Literal(symptom)))
        for treatment in treatments:
            g.add((EX[query], EX["treated_by"], Literal(treatment)))
        for cause in causes:
            g.add((EX[cause.lower()], EX["causing_by"], EX[query]))

def extract_entities(text):
    text_lower = text.lower()
    for keyword in MEDICAL_KEYWORDS:
        if keyword in text_lower:
            entity_type = (
                "Disease" if keyword in DISEASES else
                "Symptom" if keyword in SYMPTOMS else
                "Treatment" if keyword in TREATMENTS else
                "Medicine" if keyword in MEDICINES else
                "Cause" if keyword in CAUSES else
                "Diet" if keyword in DIET else
                "Health" if keyword in HEALTH else
                "Lifestyle" if keyword in LIFESTYLE else
                "Skin Care" if keyword in SKIN_CARE else
                "Unknown"
            )
            return [(keyword, entity_type)]
    return []

def query_knowledge_graph(entity):
    query = """
    PREFIX ex: <http://example.org/ontology#>
    SELECT ?predicate ?info
    WHERE {
        ex:%s ?predicate ?info .
        FILTER(?predicate IN (ex:hasSymptom, ex:treated_by, ex:hasInfo, ex:causing_by))
    }
    """ % entity
    results = g.query(query)
    return [(str(row.predicate).split('#')[-1], str(row.info)) for row in results] if results else [("info", "No data found for " + entity)]

def calculate_bmi(weight, height):
    try:
        weight = float(weight)
        height = float(height) / 100
        bmi = weight / (height * height)
        category = "Underweight" if bmi < 18.5 else "Normal" if bmi < 25 else "Overweight" if bmi < 30 else "Obese"
        return f"Your BMI is {bmi:.1f} ({category})"
    except:
        return "Please provide valid weight (kg) and height (cm) values"

def calculate_body_fat(weight, height, age, gender):
    try:
        weight = float(weight)
        height = float(height) / 100
        age = int(age)
        bmi = weight / (height * height)
        body_fat = (1.20 * bmi) + (0.23 * age) - (16.2 if gender.lower() == "male" else 5.4)
        category = "Essential Fat" if body_fat < 10 else "Athletic" if body_fat < 20 else "Average" if body_fat < 25 else "Overweight" if body_fat < 30 else "Obese"
        return f"Your Body Fat Percentage is {body_fat:.1f}% ({category})"
    except:
        return "Please provide valid weight (kg), height (cm), age, and gender"

def calculate_ideal_weight(height, gender):
    try:
        height = float(height)
        ideal_weight = (50 if gender.lower() == "male" else 45.5) + 2.3 * ((height / 2.54) - 60)
        return f"Your Ideal Weight is {ideal_weight:.1f} kg"
    except:
        return "Please provide valid height (cm) and gender"

# Modified check_symptoms to rely solely on Groq API, ignoring knowledge graph
def check_symptoms(symptoms):
    symptoms_list = [s.strip().lower() for s in symptoms.split(",") if s.strip()]
    if not symptoms_list:
        return "Please enter at least one symptom."

    # Groq API call for symptom analysis
    system_prompt = """
    You are an advanced medical AI assistant. Analyze the provided symptoms to:
    1. Predict possible conditions with detailed explanations
    2. Estimate severity (mild, moderate, severe) with confidence scores
    3. Suggest immediate actions or precautions
    4. Recommend diagnostic tests if applicable
    Provide a structured response with clear sections.
    """
    user_prompt = f"""
    Symptoms: {', '.join(symptoms_list)}
    Provide a detailed analysis including possible conditions, severity, confidence, actions, and tests.
    """
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    try:
        response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
        ai_response = response.choices[0].message.content
        return f"AI Analysis:\n{ai_response}"
    except Exception as e:
        print(f"Error in symptom checker: {e}")
        return f"AI Response: Error occurred. Please try again."

def generate_health_report(weight, height, age, gender, symptoms):
    try:
        bmi_result = calculate_bmi(weight, height)
        body_fat_result = calculate_body_fat(weight, height, age, gender)
        ideal_weight_result = calculate_ideal_weight(height, gender)
        symptom_result = check_symptoms(symptoms) if symptoms else "No symptoms provided."
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            doc = SimpleDocTemplate(tmp_file.name, pagesize=letter)
            styles = getSampleStyleSheet()
            story = [
                Paragraph("Hybrid Healthcare Assistant - Health Report", styles['Title']),
                Spacer(1, 12),
                Paragraph(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']),
                Spacer(1, 12),
                Paragraph("Health Metrics", styles['Heading2']),
                Paragraph(bmi_result, styles['Normal']),
                Paragraph(body_fat_result, styles['Normal']),
                Paragraph(ideal_weight_result, styles['Normal']),
                Spacer(1, 12),
                Paragraph("Symptom Analysis", styles['Heading2']),
                Paragraph(symptom_result, styles['Normal']),
                Spacer(1, 12),
                Paragraph("Recommendations", styles['Heading2']),
                Paragraph("Consult a healthcare professional for detailed diagnosis.", styles['Normal'])
            ]
            doc.build(story)
            return tmp_file.name
    except Exception as e:
        print(f"Error generating report: {e}")
        return None

def fetch_health_news(submit_news=None):
    try:
        url = "https://www.who.int/news"
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        news_items = soup.find_all('a', class_='list-item-link')[:2]
        news_list = [f"- [{item.text.strip()}](https://www.who.int{item['href']})" for item in news_items]
    except Exception as e:
        print(f"Error fetching news: {e}")
        news_list = DEFAULT_NEWS.copy()

    if submit_news:
        user_news.append(f"- {submit_news} (Submitted by User on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")

    combined_news = "**Latest Health News:**\n" + "\n".join(news_list) + "\n\n**User-Submitted News:**\n" + "\n".join(user_news if user_news else ["- No user news yet."])
    return combined_news

def get_youtube_videos(query):
    try:
        request = youtube.search().list(q=f"{query} healthcare explanation", part="id,snippet", maxResults=1, type="video")
        response = request.execute()
        if response["items"]:
            video_id = response["items"][0]["id"]["videoId"]
            title = response["items"][0]["snippet"]["title"]
            return f"https://www.youtube.com/embed/{video_id}", title
        return None, "No videos found"
    except Exception as e:
        print(f"Error fetching YouTube video: {e}")
        return None, "Error fetching video"

def process_medicine_list(medicine_file, medicine_text, location):
    medicines = []
    if medicine_file:
        with open(medicine_file.name, "r", encoding='utf-8') as f:
            medicines = [line.strip().lower() for line in f.readlines() if line.strip()]
    if medicine_text:
        medicines.extend([med.strip().lower() for med in medicine_text.split(",") if med.strip()])
    if not medicines:
        return "Please provide a list of medicines."
    if not location:
        return "Please enter your location."
    location_query = location.replace(" ", "+")
    pharmacy_search_url = f"https://www.google.com/maps/search/pharmacies+near+{location_query}"
    result = f"### Pharmacy Finder Result\n\n**Location:** {location.capitalize()}\n\n**Medicines:** {', '.join([med.capitalize() for med in medicines])}\n\n"
    for med in medicines:
        dosage = medicine_data.get(med, "Dosage not available.")
        result += f"#### {med.capitalize()}\n- **Dosage:** {dosage}\n- **Online Purchase Options:**\n"
        for name, base_url in ONLINE_PHARMACIES.items():
            result += f"  - [{name}]({base_url}{med})\n"
        result += "\n"
    result += f"**Find Nearby Pharmacies:** [Click here]({pharmacy_search_url})"
    return result

# Modified generate_response to block only blocked keywords
def generate_response(message, history):
    # Check for blocked keywords
    message_lower = message.lower()
    for blocked in BLOCKED_KEYWORDS:
        if blocked in message_lower:
            return "Warning: I can only provide information related to medical fields. Please ask about diseases, treatments, medicines, symptoms, diet, health, lifestyle, or skin care."

    bmi_pattern = r"calculate.*bmi.*weight\D*(\d+\.?\d*)\D*height\D*(\d+\.?\d*)"
    bmi_match = re.search(bmi_pattern, message.lower())
    if bmi_match:
        weight, height = bmi_match.groups()
        return calculate_bmi(weight, height)

    entities = extract_entities(message)
    if entities:
        entity = entities[0][0]
        initialize_graph(entity)
        kg_data = query_knowledge_graph(entity.lower())
        kg_response = "\n".join([f"{pred}: {info}" for pred, info in kg_data])

        system_prompt = "You are a hybrid healthcare assistant combining AI insights with knowledge graph data. Provide concise, accurate answers."
        messages = [{"role": "system", "content": system_prompt}]
        for user_msg, ai_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": ai_msg})
        user_prompt = f"User query: {message}\nKnowledge Graph data:\n{kg_response}\nBlend this data with your AI insights."
        messages.append({"role": "user", "content": user_prompt})

        try:
            response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in Groq API call: {e}")
            return f"Knowledge Graph Info:\n{kg_response}\n\nAI Response: Error occurred. Please try again."
    return "I'm sorry, I could not find any medical-related information in your input. Please ask about diseases, treatments, medicines, symptoms, diet, health, lifestyle, or skin care."

def visualize_knowledge_graph(query=None):
    initialize_graph(query)
    G = nx.DiGraph()
    node_color_map = {"Disease": "lightcoral", "Symptom": "lightgreen", "Treatment": "lightblue", "Cause": "lightyellow", "Info": "lavender"}
    edge_color_map = {"hasSymptom": "blue", "treated_by": "green", "causing_by": "red", "hasInfo": "purple"}

    # Use disease_data for visualization
    if query and query.lower() in disease_data:
        disease = query.lower()
        G.add_node(disease, type="Disease")
        # Add info
        G.add_node(disease_data[disease]["hasInfo"], type="Info")
        G.add_edge(disease, disease_data[disease]["hasInfo"], relation="hasInfo", color=edge_color_map["hasInfo"])
        # Add symptoms
        for symptom in disease_data[disease]["hasSymptom"]:
            G.add_node(symptom, type="Symptom")
            G.add_edge(disease, symptom, relation="hasSymptom", color=edge_color_map["hasSymptom"])
        # Add treatments
        for treatment in disease_data[disease]["treated_by"]:
            G.add_node(treatment, type="Treatment")
            G.add_edge(disease, treatment, relation="treated_by", color=edge_color_map["treated_by"])
        # Add causes
        for cause in disease_data[disease]["causing_by"]:
            G.add_node(cause, type="Cause")
            G.add_edge(cause, disease, relation="causing_by", color=edge_color_map["causing_by"])
    else:
        for s, p, o in g:
            if p in [EX["hasSymptom"], EX["treated_by"], EX["hasInfo"], EX["causing_by"]]:
                subject = str(s).split('#')[-1]
                obj = str(o)  # Full text from the Literal
                relation = str(p).split('#')[-1]
                G.add_node(subject, type="Disease")
                G.add_node(obj, type="Symptom" if relation == "hasSymptom" else "Treatment" if relation == "treated_by" else "Cause" if relation == "causing_by" else "Info")
                G.add_edge(subject, obj, relation=relation, color=edge_color_map[relation])

    if not G.nodes():
        plt.text(0.5, 0.5, "No data to visualize", ha='center', va='center', fontsize=14)
        plt.axis('off')
    else:
        pos = nx.spring_layout(G)
        node_colors = [node_color_map.get(G.nodes[node]["type"], "lightgray") for node in G.nodes()]
        edge_colors = [G[u][v]["color"] for u, v in G.edges()]
        nx.draw(G, pos, node_size=1500, node_color=node_colors, edge_color=edge_colors, labels={node: node for node in G.nodes()}, font_size=8, with_labels=True)
        edge_labels = nx.get_edge_attributes(G, 'relation')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6)
        plt.title(f"Knowledge Graph: {query.capitalize() if query else 'Healthcare Conditions'}")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    img = Image.open(buf)
    plt.close()
    return img

# Flask Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html', about_section=about_section, college_info=college_info)

@app.route('/team')
def team():
    return render_template('team.html', team_members=team_members, college_info=college_info)

# Updated chat route to correctly handle blocked keywords warning
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        message = request.form['message']
        history = eval(request.form.get('history', '[]'))
        response = generate_response(message, history)
        out_of_scope = response.startswith("Warning: I can only provide information") or response.startswith("I'm sorry, I could not find any medical-related information")
        if out_of_scope:
            return jsonify({'response': response, 'out_of_scope': True, 'history': history})
        else:
            new_history = history + [(message, response)]  # Append new message and response
            return jsonify({'response': response, 'out_of_scope': False, 'history': new_history})
    return render_template('chat.html')

@app.route('/visualize', methods=['GET', 'POST'])
def visualize():
    if request.method == 'POST':
        query = request.form['query']
        img = visualize_knowledge_graph(query)
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')
    return render_template('visualize.html')

@app.route('/videos', methods=['GET', 'POST'])
def videos():
    if request.method == 'POST':
        query = request.form['query']
        video_url, title = get_youtube_videos(query)
        return jsonify({'video_url': video_url, 'title': title})
    return render_template('videos.html')

@app.route('/medicine', methods=['GET', 'POST'])
def medicine():
    if request.method == 'POST':
        medicine_text = request.form['medicine_text']
        location = request.form['location']
        result = process_medicine_list(None, medicine_text, location)
        return jsonify({'result': result})
    return render_template('medicine.html')
@app.route('/calculators', methods=['GET', 'POST'])
def calculators():
    if request.method == 'POST':
        action = request.form['action']
        if action == 'bmi':
            weight = request.form['weight']
            height = request.form['height']
            result = calculate_bmi(weight, height)
        elif action == 'body_fat':
            weight = request.form['weight']
            height = request.form['height']
            age = request.form['age']
            gender = request.form['gender']
            result = calculate_body_fat(weight, height, age, gender)
        elif action == 'ideal_weight':
            height = request.form['height']
            gender = request.form['gender']
            result = calculate_ideal_weight(height, gender)
        return jsonify({'result': result})
    return render_template('calculators.html')

@app.route('/symptoms', methods=['GET', 'POST'])
def symptoms():
    if request.method == 'POST':
        symptoms = request.form['symptoms']
        result = check_symptoms(symptoms)
        return jsonify({'result': result})
    return render_template('symptoms.html')

# Modified report route with Groq API integration
@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        user_input = request.form.get('input', '')
        age = request.form.get('age', '')
        body_weight = request.form.get('body_weight', '')
        height = request.form.get('height', '')
        gender = request.form.get('gender', '')
        family_health_details = request.form.get('family_health_details', '')
        symptoms = request.form.get('symptoms', '')
        lifestyle = request.form.get('lifestyle', '')
        medical_history = request.form.get('medical_history', '')
        allergies = request.form.get('allergies', '')

        try:
            bmi = float(body_weight) / ((float(height) / 100) ** 2) if body_weight and height else 'N/A'
            bmi_category = 'Normal' if 18.5 <= bmi <= 24.9 else 'Underweight' if bmi < 18.5 else 'Overweight' if bmi > 24.9 else 'N/A'
            ideal_weight_min = 18.5 * ((float(height) / 100) ** 2)
            ideal_weight_max = 24.9 * ((float(height) / 100) ** 2)
        except (ValueError, ZeroDivisionError):
            bmi = 'N/A'
            bmi_category = 'N/A'
            ideal_weight_min = 'N/A'
            ideal_weight_max = 'N/A'

        # Groq API call for detailed health report analysis
        system_prompt = """
        You are an advanced medical AI assistant. Analyze the provided health data to generate a comprehensive health report including:
        1. Detailed health analysis based on BMI, symptoms, lifestyle, and medical history
        2. Potential health risks and predictions
        3. Personalized recommendations for diet, lifestyle, and medical follow-up
        4. Explanation of findings in simple language
        Provide a structured response with clear sections.
        """
        user_prompt = f"""
        Health Data:
        - Age: {age}
        - Weight: {body_weight} kg
        - Height: {height} cm
        - Gender: {gender}
        - BMI: {bmi:.1f} ({bmi_category})
        - Ideal Weight Range: {ideal_weight_min:.1f} - {ideal_weight_max:.1f} kg
        - Family Health Details: {family_health_details}
        - Symptoms: {symptoms}
        - Lifestyle: {lifestyle}
        - Medical History: {medical_history}
        - Allergies: {allergies}
        Generate a detailed health report with analysis, risks, and recommendations.
        """
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        try:
            response = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
            groq_analysis = response.choices[0].message.content
        except Exception as e:
            print(f"Error in Groq API call for report: {e}")
            groq_analysis = "Error: Unable to generate AI analysis. Please try again."

        report_file = os.path.join(app.root_path, 'static', 'health_report.pdf')
        os.makedirs(os.path.dirname(report_file), exist_ok=True)

        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        c = canvas.Canvas(report_file, pagesize=letter)
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.green)
        c.drawString(100, 750, "Healthcare Hub - Health Report")
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawString(100, 730, f"Generated on: {datetime.datetime.now()}")
        c.rect(90, 700, 400, 1, fill=1, stroke=0)

        c.drawString(100, 680, "Patient Information")
        c.rect(90, 650, 400, 1, fill=1, stroke=0)
        y = 630
        c.drawString(100, y, f"User Input: {user_input}")
        y -= 20
        c.drawString(100, y, f"Age: {age}")
        y -= 20
        c.drawString(100, y, f"Body Weight: {body_weight} kg")
        y -= 20
        c.drawString(100, y, f"Height: {height} cm")
        y -= 20
        c.drawString(100, y, f"Gender: {gender}")
        y -= 20
        c.drawString(100, y, f"Family Health Details: {family_health_details}")
        y -= 20
        c.drawString(100, y, f"Symptoms: {symptoms}")
        y -= 20
        c.drawString(100, y, f"Lifestyle: {lifestyle}")
        y -= 20
        c.drawString(100, y, f"Medical History: {medical_history}")
        y -= 20
        c.drawString(100, y, f"Allergies: {allergies}")

        c.drawString(100, y - 30, "AI-Generated Health Analysis")
        c.rect(90, y - 50, 400, 1, fill=1, stroke=0)
        y -= 70
        # Split Groq analysis into lines and handle page breaks
        for line in groq_analysis.split('\n'):
            while len(line) > 80:  # Break long lines
                c.drawString(100, y, line[:80])
                line = line[80:]
                y -= 20
                if y < 100:
                    c.showPage()
                    y = 750
            c.drawString(100, y, line)
            y -= 20
            if y < 100:
                c.showPage()
                y = 750

        c.showPage()
        c.save()

        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                return send_file(
                    report_file,
                    as_attachment=True,
                    download_name='health_report.pdf',
                    mimetype='application/pdf'
                )
            except PermissionError:
                if attempt < max_attempts - 1:
                    time.sleep(0.1)
                    continue
                else:
                    raise
            finally:
                if os.path.exists(report_file):
                    for _ in range(max_attempts):
                        try:
                            os.remove(report_file)
                            break
                        except PermissionError:
                            time.sleep(0.1)
                            continue

    return render_template('report.html')

@app.route('/news', methods=['GET', 'POST'])
def news():
    if request.method == 'POST':
        submit_news = request.form.get('submit_news')
        news = fetch_health_news(submit_news)
        return jsonify({'news': news})
    news = fetch_health_news()
    return render_template('news.html', news=news)
@app.route("/appointments", methods=["POST"])
def create_appointment():
    try:
        data = request.get_json()

        customer_name = data.get("customer_name")
        phone_number = data.get("phone_number")
        appointment_time = data.get("appointment_time")

        # Basic validation
        if not all([customer_name, phone_number, appointment_time]):
            return jsonify({
                "success": False,
                "message": "All fields are required."
            }), 400

        # Convert string to datetime object
        appointment_datetime = datetime.strptime(
            appointment_time,
            "%Y-%m-%d %H:%M"
        )

        # Create appointment
        appointment = Appointment(
            customer_name=customer_name,
            phone_number=phone_number,
            appointment_time=appointment_datetime
        )

        # Save to database
        db.session.add(appointment)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Appointment created successfully.",
            "appointment": appointment.to_dict()
        }), 201

    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid date format. Use YYYY-MM-DD HH:MM"
        }), 400

    except Exception as e:
        db.session.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)