#create flask api
from flask import Flask, jsonify, request, after_this_request
import requests
import json
from bs4 import BeautifulSoup
from flask_cors import CORS, cross_origin
from utils import parse_RFP, cleanup
import os 
import atexit
#import flask after_this_request

#create instance of Flask class
app = Flask(__name__)
CORS(app)

ENTITY_SEARCH_URL = "https://api.sam.gov/entity-information/v2/entities"

SBA_SEARCH_URL = "https://web.sba.gov/pro-net/search/dsp_profile.cfm"

#welcome screen
@app.route('/')
def welcome():
    return 'Welcome to the Server!'

@app.route('/api/company_info',methods=["GET"])
def get_company_info():
    try:
        app.logger.info('Processing request...')

        responseobj={}
        if 'duns' in request.args:
            duns = request.args['duns']
        else:
            return "Error: No DUNS provided. Please specify DUNS."
        if 'api_key' in request.args:
            api_key = request.args['api_key']
        else:
            return "Error: No API Key provided. Please specify API Key."
        
        #call sam.gov entity search api
        SAM_response = requests.get(ENTITY_SEARCH_URL, params={'ueiDUNS': duns, 'api_key': api_key});
        if SAM_response is None:
            return jsonify(responseobj)
        SAM_response = json.loads(SAM_response.text)
        
        url = SAM_response['entityData'][0]['coreData']["entityInformation"]['entityURL']
        business_types = SAM_response['entityData'][0]['coreData']["businessTypes"]
        business_type_list = [x["businessTypeDesc"] for x in business_types["businessTypeList"]]
        sba_8a_entrance = ""
        sba_8a_exit = ""
        if "sbaBusinessTypeList" in business_types:
            for x in business_types["sbaBusinessTypeList"]:
                if x["sbaBusinessTypeDesc"] != None:
                    business_type_list.append(x["sbaBusinessTypeDesc"])
                    if "8(a)" in x["sbaBusinessTypeDesc"]:
                        sba_8a_entrance = x["certificationEntryDate"]
                        sba_8a_exit = x["certificationExitDate"]
        socio_economic_status = []
        SBA8aFlag = False
        for d in business_type_list:
            if not ("corporation" in d.lower() or "organization" in d.lower()):
                socio_economic_status.append(d)
        primary_NAICS = SAM_response['entityData'][0]['assertions']["goodsAndServices"]['primaryNaics']
        responseobj = {"url": url, "primary_NAICS": primary_NAICS, "socio_economic_status": socio_economic_status, 
        "sba_8a_entrance": sba_8a_entrance, "sba_8a_exit": sba_8a_exit}

        #call sba.gov search api
        SBA_response = requests.get(SBA_SEARCH_URL, params={'duns': duns})
        if not SBA_response.ok:
            return jsonify(responseobj)
        SBA_response = SBA_response.text

        soup = BeautifulSoup(SBA_response, "html.parser")
        #get all divs w/ class "profileline"
        profile_divs = soup.find_all("div", {"class":"profileline"})
        #iterate over profile divs
        for profile_div in profile_divs:
            k = profile_div.find("div", {"class":"profilehead"}).text
            if profile_div.find("div", {"class":"profileinfo"}) is not None:
                v = profile_div.find("div", {"class":"profileinfo"}).text
            responseobj[k]=v
        cap_narr = soup.find(string="Capabilities Narrative:")
        if cap_narr is not None:
            s = cap_narr.find_next('div').text
            cap_narrative = " ".join(s.split())
            responseobj['Capabilities Narrative'] = cap_narrative
        #get past performance
        all_references = soup.find_all("div",{"class":"referencebox"})
        reference_info = []
        for reference in all_references:
            contract_info = {}
            profile_divs = reference.find_all("div", {"class":"profileline"})
            for profile_div in profile_divs:
                k = profile_div.find("div", {"class":"profilehead"}).text
                if profile_div.find("div", {"class":"profileinfo"}) is not None:
                    v = profile_div.find("div", {"class":"profileinfo"}).text
                contract_info[k]=v
            reference_info.append(contract_info)
        responseobj['References'] = reference_info
        return jsonify(responseobj)
    except:
        return jsonify({})

#figure out how to delete file after it closes
@app.route('/api/parser', methods = ['POST'])
def upload_file():
    file = request.files['uploadedFile']
    file.save(file.filename)
    ordered_sentences = parse_RFP(file.filename)
    file.close()
    #os.remove(file.filename)

    return jsonify({'sentences': ordered_sentences[:10]})

atexit.register(cleanup)
app.run(debug=True) 


