from pprint import pprint

from flask import Flask, jsonify, render_template, request

from services import *
from state_replies import replies

welcome_message = replies['0']
app = Flask(__name__)
SESSIONS = {}

ENTITIES = {}


class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'


class Session(object):
    def __init__(self, sess_id, replies):
        self.sess_id = sess_id
        self.state = '0'
        self.replies = replies
        
    def get_response(self, text):
        if self.state in ('0','f0_0'):
            chat_intent = get_chat_intent(text)
            if chat_intent == 'file_claim':
                self.state = '1'
                ENTITIES['Intent'] = "Claim Filing"
            elif chat_intent == 'check_status':
                self.state == '2'
            elif chat_intent == 'file_claim_policy_number':
                ENTITIES['Intent'] = "Claim Filing"
                ENTITIES["Policy Number"] = "".join(re.findall(r'\d', text))
                self.state = '3'
            else:
                self.state = 'f0_0'
        
        elif self.state in ('1', 'f1_0', 'f1_1', 'f1_2', 'f1_3'):
            response = verify_policy_number(text)['response']
            if response == 'ok':
                self.state = '3'
                ENTITIES['Policy Number'] = "".join(re.findall(r'\d', text))
            elif response == 'not_found':
                self.state = 'f1_0'
            elif response == 'non_numeric':
                self.state = 'f1_1'
            elif response == 'digits_unmatched':
                self.state = 'f1_2'
            elif response == 'already_filed':
                self.state = 'f1_3'

        elif self.state in ('3', 'f3_0'):
            response = get_name(text)
            if not response is None:
                self.state = '4a'
                ENTITIES["Name"] = response
            else:
                self.state = 'f3_0'

        elif self.state in ('4a', 'f4a_0'):
            response = get_location(text)
            if not response is None:
                self.state = '4'
                ENTITIES["Address"] = response
            else:
                self.state = 'f4a_0' 
        
        elif self.state in ('4', 'f4_1'):
            response = verify_phone_number(text)['response']
            if response == 'valid':
                self.state = '5'
                ENTITIES["Phone Number"] = verify_phone_number(text)['value']
            elif response == 'area_code_missing':
                self.state = '4_0'
            elif response == 'not_valid':
                self.state = 'f4_1'

        elif self.state in ('4_0', '4_0_0'):
            number = "".join(re.findall(r'\d', text))
            if len(number) == 3:
                self.state = '5'
                ENTITIES['Area Code'] = number
            else:
                self.state = 'f4_0_0'
            
        elif self.state in ('5', 'f5_0'):
            response = verify_email_address(text)
            if response == 'valid':
                self.state = '6a'
                ENTITIES["Email Address"] = text
            else:
                self.state = 'f5_0'

        elif self.state in ('6a', 'f6a_0'):
            response = get_loss_date(text)
            if not response == 'not_found':
                self.state = '6'
                ENTITIES["Date of Loss"] = response
            else:
                self.state = 'f6a_0'
                

        elif self.state in ('6', 'f6_0'):
            response = get_loss(text)
            if 'exterior' in response and 'interior' in response:
                self.state = '10'
                ENTITIES["Exterior Damage"] = response['exterior']
                ENTITIES["Interior Damage"] = response['interior']
            elif 'exterior' in response:
                self.state = '8'
                ENTITIES["Exterior Damage"] = response['exterior']
            elif 'interior' in response:
                self.state = '9'
                ENTITIES["Interior Damage"] = response['interior']
            elif 'loss' in 'response':
                self.state = '7'
                ENTITIES["Damage"] = response['loss']
            else:
                self.state = 'f6_0'
        
        elif self.state in ('7', 'f7_0'):
            response = get_loss(text)
            ENTITIES['Additional Damage'] = response
            ####??
            self.state = '8'

        elif self.state in ('8', 'f8_0'):
            response = get_loss(text)
            ENTITIES['Additional Damage'] = response
            ####??
            self.state = '10'

        elif self.state in ('9', 'f9_0'):
            response = get_loss(text)
            ENTITIES['Additional Damage'] = response
            ####??
            self.state = '10'

        elif self.state in ('10', 'f10_0'):
            response = get_power_loss(text)
            if response == 'yes':
                self.state = '11a'
                ENTITIES["Power Loss Occurred"] = "Yes"
            elif response == 'no':
                self.state = '13'
                ENTITIES["Power Loss Occurred"] = "No"
            else:
                self.state = 'f10_0'

        elif self.state in ('11a', 'f11a_0'):
            response = get_power_loss_duration(text)
            if not response == 'not_found':
                self.state = '11'
                ENTITIES["Power Loss Duration"] = response
            else:
                self.state = 'f11a_0'


        elif self.state in ('11', 'f11_0'):
            response = get_food_spoilage(text)
            if response == 'yes':
                self.state = '12'
                ENTITIES["Food Spoilage"] = "Yes"
            elif response == 'no':
                self.state = '13'
                ENTITIES["Food Spoilage"] = "No"
            else:
                self.state = 'f11_0'

        elif self.state in ('12', 'f12_0'):
            response = get_food_spoilage_estimate(text)
            if not response == 'not_found':
                self.state = '13'
                ENTITIES["Food Spoilage Estimate"] = response
            else:
                self.state = 'f12_0'

        elif self.state in ('13', 'f13_0'):
            response = get_home_livable(text)
            if response == 'yes':
                self.state = '14'
                ENTITIES["Home Livable"] = "Yes"
            elif response == 'no':
                self.state = '14'
                ENTITIES["Home Livable"] = "No"
            else:
                self.state = 'f13_0' 

        return self.replies[self.state][0], self.state, self.state == '14'



@app.route('/get_intent', methods=['POST'])
def get_intent():
    data = request.get_json(silent=True)
    sess_id = data['session'] 

    if sess_id in SESSIONS:
        sess = SESSIONS[sess_id]
    else:
        sess = Session(sess_id=sess_id, replies=replies)
        SESSIONS[sess_id] = sess

    text = data['queryResult']['queryText']
    print('#'*50)
    print("Session:    " + sess_id)
    print("Customer:  "+text)
    response, state, end = sess.get_response(text)
    print("Operator:  "+response)
    print("Conversation End:   "+str(end)+"\n\n")
    reply = {
        
                "fulfillmentText": response,
                "payload": {
                    "google": {
                         "expectUserResponse": True,
                        "richResponse": {
                            "items": [
                                {
                                    "simpleResponse": {
                                        "textToSpeech": response
                                    }
                                
                                }
                            ],
                            "suggestions": [
                                {"title": "hello"}
                            ]
                        }
                    }
                }
            }

    return jsonify(reply)

def converse():
    sess = Session('001', replies)
    print(color.BOLD+color.RED+"Sally: "+color.END+color.END+welcome_message[0])
    print("")
    while(1):
        text = raw_input(color.BOLD+color.BLUE+"User: "+color.END+color.END)
        response, state, _ = sess.get_response(text)
        print(color.BOLD+color.RED+"Sally: "+color.END+color.END+response)
        print("")
        if state == '14':
            break
    pprint('-'*50)
    pprint(ENTITIES)


    

if __name__ =="__main__":
    # app.run(debug=True,port=8080,threaded=True)
    converse()
