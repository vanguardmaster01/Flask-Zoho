from flask import Flask, request, jsonify
import Constants
import json
import requests
import base64
import datetime

app = Flask(__name__)

refreshToken = None
accessToken = None

@app.route('/')
def hello():
    return '<h1>Welcome to Flask</h1>'


@app.route('/send_master_contract', methods=['POST'])
def send_master_contract():
    global accessToken
    content = None
    resData = {}
    try:
        content = request.json

        # if refreshtoken, get access token and refresh token
        genAccessAndRefreshToken()
        
        print('accesstoken------', accessToken)

        fileList=[["BUSINESS LOAN AGREEMENT.docx","./BUSINESS LOAN AGREEMENT.docx","application/docx"]]
        respjson= createDocument(fileList, accessToken, content)

        respjson=respjson['requests']
        request_id=respjson['request_id']

        result=submitDocument(request_id,respjson,accessToken, content)

        print('submitrespjson---------', (submitrespjson))
        print('Successfully send the document out for signature.')
        
        if result:
            resData['contract_id'] = request_id
            resData['result'] = 'success'
        else:
            resData['contract_id'] = -1
            resData['result'] = 'failure'


        # # send the POST request
        # response = requests.post(Constants.createContractEndpoint, headers=headers, data=json.dumps(payload))

        # if response.status_code == 200:
        #     contractData = response.json()
        #     contractId = contractData.get('request_id')
        #     print(f"Contract created successfully. Contract ID: {contractId}")
        # else:
        #     error_message = response.json().get("message")
        #     print(f"Contract creation failed. Error message: {error_message}")

    except Exception as e:
        print(e)
        resData['contract_id'] = -1
        resData['result'] = 'exception'

    # if content:
    #     # return jsonify(responseData.contractID)
    #     return jsonify(responseData.apiName)
    # else:
    return jsonify(resData) 
    

@app.route('/zoho_callback', methods=['POST'])
def zoho_callback():
    resData = request.json
    requestsData = resData['requests']

    print(f'requests payload: {requestsData}')
    print(f'request id: {requestsData["request_id"]}')
    
    return '<h2>Contract id: {} is signed</h2>'.format(5)


# get contract with apiName using zoho sign not using contract id
@app.route('/zoho_status', methods=['GET'])
def get_status():
    global accessToken
    param = request.json
    contractId = param['contract_id']
    
    contractData = getDocumentDetailsById(contractId, accessToken)
    
    print(f'contractData: {contractData}')

    return contractData


def genAccessAndRefreshToken():
    global refreshToken
    global accessToken
    
    try:
        if not refreshToken:
            payloads = {
                'client_id': Constants.clientId,
                'client_secret': Constants.clientSecret,
                'code': Constants.code,
                'grant_type': 'authorization_code'
            }

            response = requests.post(Constants.genAccessAndRefreshTokenEndpoint, 
                                    data=payloads)

            if response.status_code == 200:
                accessToken = response.json().get('access_token')
                refreshToken = response.json().get('refresh_token')
                # getAccessFromRefreshToken()
        else:
            getAccessFromRefreshToken()
    except Exception as e:
        print('genAccessAndRefreshToken error')
        print(e)


def getAccessFromRefreshToken():
    global refreshToken
    global accessToken
    payloads = {
        'refresh_token': refreshToken,
        'client_id': Constants.clientId,
        'client_secret': Constants.clientSecret,
        'grant_type': 'refresh_token'
    }

    response = requests.post(Constants.genAccessAndRefreshTokenEndpoint, 
                             data=payloads)
    if response.status_code == 200:
        accessToken = response.json().get('accesst_token')

    return 1


def createDocument(fileList, Oauthtoken, content):
    headers = {'Authorization':'Zoho-oauthtoken '+Oauthtoken}
    files = []
    for i in fileList:
	    files.append(('file', (i[0],open(i[1],'rb'),i[2])))
    req_data = {}
    req_data['request_name']="Zoho Contract"
    req_data["expiration_days"]= 10
    req_data["is_sequential"]=True
    req_data["email_reminders"]=True
    req_data["reminder_period"]= 5
    # field_list={}
    # field_list['field_text_data'] = "1"
    # req_data['field_data'] = field_list
    actions_list=[]
    actions_list.append({
        "recipient_name": content[Constants.lender_contact_name],
        "recipient_email": content[Constants.lender_email],
        "verify_recipient": False,
        "action_type":"SIGN",
        "private_notes":"Please get back to us for further queries",
        "signing_order":0})
    
    actions_list.append({
        "recipient_name": content[Constants.first_name],
        "recipient_email": content[Constants.email],
        "verify_recipient": False,
        "action_type":"SIGN",
        "private_notes":"Please get back to us for further queries",
        "signing_order":0})

    req_data['actions']=actions_list
    data={}
    data['requests']=req_data
    data_json={}
    data_json['data'] = json.dumps(data)
    
    res = requests.post(Constants.signEndpoint, files=files, data=data_json,headers=headers)
    return res.json()


def submitDocument(request_id,respjson,Oauthtoken, content):
    print('Oauthtoken----------', Oauthtoken)
    print('request_id----------', request_id)
    headers = {'Authorization':'Zoho-oauthtoken '+Oauthtoken}
    req_data={}
    resData = {}
    try:
        req_data['request_name']=respjson['request_name']
        docIdsJsonArray = respjson['document_ids']
        actionsJsonArray = respjson['actions']
        for i in docIdsJsonArray:
            docId=i["document_id"]		
            for j in actionsJsonArray:
                fields=[]
                current_date = datetime.date.today().strftime("%Y-%m-%d")
                dateField = {}
                dateField["field_type_name"] = "Textfield"
                dateField["text_property"]={}
                dateField["text_property"]["is_read_only"]= True
                dateField["is_mandatory"]= True
                dateField['default_value'] = current_date
                dateField["page_no"]= 0
                dateField["document_id"]= docId
                dateField["field_name"]= 'Text field'
                dateField["y_coord"]= 125
                dateField["abs_width"]= 100
                dateField["x_coord"]=100
                dateField["abs_height"]= 13
                fields.append(dateField)
                
                borrowEmailField = {}
                borrowEmailField["field_type_name"] = "Textfield"
                borrowEmailField["text_property"]={}
                borrowEmailField["text_property"]["is_read_only"]= True
                borrowEmailField["is_mandatory"]= True
                borrowEmailField['default_value'] = content[Constants.email]
                borrowEmailField["page_no"]= 0
                borrowEmailField["document_id"]= docId
                borrowEmailField["field_name"]= 'Text field'
                borrowEmailField["y_coord"]= 168
                borrowEmailField["abs_width"]= 120
                borrowEmailField["description_tooltip"]= ""
                borrowEmailField["x_coord"]=125
                borrowEmailField["abs_height"]= 13
                fields.append(borrowEmailField)

                name1 = {}
                name1["field_type_name"] = "Textfield"
                name1["text_property"]={}
                name1["text_property"]["is_read_only"]= True
                name1["is_mandatory"]= True
                name1['default_value'] = content[Constants.first_name] + ' ' + content[Constants.last_name]
                name1["page_no"]= 0
                name1["document_id"]= docId
                name1["field_name"]= 'Text field'
                name1["y_coord"]= 197
                name1["abs_width"]= 120
                name1["description_tooltip"]= ""
                name1["x_coord"]=110
                name1["abs_height"]= 13
                fields.append(name1)

                sigField1={}
                sigField1["field_type_name"]= "Signature"
                sigField1["is_mandatory"]= True
                sigField1["field_name"]= "Signature"
                sigField1["page_no"]= 0
                sigField1["y_coord"]= 212
                sigField1["abs_width"]= 120
                sigField1["description_tooltip"]= ""
                sigField1["x_coord"]= 125
                sigField1["abs_height"]= 15
                sigField1["document_id"]= docId
                fields.append(sigField1)

                emailField = {}
                emailField["field_type_name"] = "Textfield"
                emailField["text_property"]={}
                emailField["text_property"]["is_read_only"]= True
                emailField["is_mandatory"]= True
                emailField["page_no"]= 0
                emailField["document_id"]= docId
                emailField["y_coord"]= 266
                emailField["abs_width"]= 120
                emailField["description_tooltip"]= ""
                emailField['default_value'] = content[Constants.lender_email]
                emailField["field_name"]= 'Text field'
                emailField["x_coord"]=115
                emailField["abs_height"]= 13
                fields.append(emailField)

                name2 = {}
                name2["field_type_name"] = "Textfield"
                name2["text_property"]={}
                name2["text_property"]["is_read_only"]= True
                name2["is_mandatory"]= True
                name2["page_no"]= 0
                name2["document_id"]= docId
                name2["y_coord"]= 281
                name2["abs_width"]= 120
                name2["description_tooltip"]= ""
                name2['default_value'] = content[Constants.lender_contact_name]
                name2["field_name"]= 'Text field'
                name2["x_coord"]=110
                name2["abs_height"]= 13
                fields.append(name2)

                sigField2={}
                sigField2["field_type_name"]= "Signature"
                sigField2["is_mandatory"]= True
                sigField2["field_name"]= "Signature"
                sigField2["page_no"]= 0
                sigField2["y_coord"]= 298
                sigField2["abs_width"]= 120
                sigField2["description_tooltip"]= ""
                sigField2["x_coord"]= 125
                sigField2["abs_height"]= 15
                sigField2["document_id"]= docId
                fields.append(sigField2)

                if 'fields' in j:
                    j['fields']=j['fields']+fields
                else:
                    j["fields"]=fields
                j.pop('is_bulk',None)
                j.pop('allow_signing',None)
                j.pop('action_status',None)
        
        req_data['actions']=actionsJsonArray
        data={}
        data['requests']=req_data
        data_json={}
        data_json['data'] = json.dumps(data)

        url = Constants.signEndpoint + '/' + request_id + '/submit'
        r = requests.post(url, files=[],data=data_json, headers=headers)
        if r.status_code == 200:
            return True
        else:
            return False
    
    except Exception as e:
        print("SubmitError------", e)
        
    return False


def getDocumentDetailsById(request_id,Oauthtoken):
	headers = {'Authorization':'Zoho-oauthtoken '+Oauthtoken}
	r = requests.get('https://sign.zoho.com/api/v1/requests/'+request_id,headers=headers)
	return r.json()


def getDownloadPDF(request_id,Oauthtoken):
	headers = {'Authorization':'Zoho-oauthtoken '+Oauthtoken}
	r = requests.get(Constants.signEndpoint+request_id+"/pdf",headers=headers)
	open('temp.pdf', 'wb').write(r.content)


if __name__ == '__main__':
    app.run()