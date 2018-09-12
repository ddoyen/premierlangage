import requests
from lti.models import LTIGradeHomework, LTIGrade, LTIGradeActivity
import xml.etree.ElementTree as ET

def replace_grade(request,grade):
    if request.method == 'POST':
        with open("ressources/result.xml", "r") as f:
            return f.read() % (LTIGrade.sourcedid, grade)

def replace_read_result(request):
    if request.method == 'POST':
        with open("ressources/readResult.xml", "r") as f:
            return f.read() % LTIGrade.sourcedid
        
def replace_delete(request):
    if request.method == 'POST':
        with open("ressources/delete.xml", "r") as f:
            return f.read() % LTIGrade.sourcedid
    
def send_grade(request, user, activity, grade):
     LTIGrade
     result_xml = replace_grade(request,grade)
     response = requests.post(LTIGrade.outcome_url, data=result_xml)
     tree = ET.parse(response)
     root = tree.getroot()
     if 200 <= response.status_code < 300 and root[0][0][2][0].text == "succes":
          return True
     raise ValueError(root[0][0][2][2].text)

def send_read_result(request):
     result_xml = replace_read_result(request)
     response = request.post(LTIGrade.outcome_url, data=result_xml)
     tree = ET.parse(response)
     root = tree.getroot()
     if 200 <= response.status_code < 300 and root[0][0][2][0].text == "succes":
          return True
     raise ValueError("Read result response have failed")

     
        
