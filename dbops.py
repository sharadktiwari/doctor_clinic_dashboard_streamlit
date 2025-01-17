from pymongo import MongoClient
import datetime
try:
    client = MongoClient("mongodb+srv://sharadkumartiwari1508:171489956@clustor0.kyc0e.mongodb.net/?retryWrites=true&w=majority&appName=clustor0")
    db = client["appointease"]
    doc_loc_details = db["doc_location_details"]
    doc_details = db["doc_details"]
    patient_details = db["patient_details"]
    appointment_details = db["appointment_details"]
    patient_history = db["patient_history"]
except Exception as e:
    print('Unable to establish connection with database')

def get_doc_id(dr_contact:str) -> dict:
    try:
        doc_id = doc_details.find_one({"contact":dr_contact},['doc_id'])
        if doc_id:
            return {'status_code':200,'data':doc_id['doc_id']}
        else:
            return {'status_code':400,'data':'Doctor is not registered'}
    except Exception as e:
        print(e)
        return {'status_code':400,'data':'Doctor not found'}
    
def get_clinic_names(doc_id:str):
    try:
        loc_addresses = doc_loc_details.find({"doc_id":doc_id},['loc_address'])
        if loc_addresses:
            return {'status_code':200,'data':[la['loc_address'] for la in loc_addresses]}
        else:
            return {'status_code':400,'data':'Location Data Not Found'}
    except Exception as e:
        print(e)
        return {'status_code':400,'data':'Location not found'}
    
def get_slots(clinic:str):
    try:
        loc_slots = doc_loc_details.find_one({"loc_address":clinic},['avail_time_slots'])
        if loc_slots:
            return {'status_code':200,'data':loc_slots['avail_time_slots']}
        else:
            return {'status_code':400,'data':'Slots Data Not Found'}
    except Exception as e:
        print(e)
        return {'status_code':400,'data':'Slots not found'}
    
def get_appointments(clinic,slot,dash_datetime):
    try:
        loc_id = doc_loc_details.find_one({"loc_address":clinic},['loc_id'])
        if loc_id:
            appointment_data = appointment_details.find({'loc_id':loc_id['loc_id'],'app_time_slot':slot,'status':{'$in':[1,2]},'app_date':dash_datetime},
                                                        ['visit_id','patient_id'])
            if appointment_data:
                data = []
                for ad in appointment_data:
                    patient_data = patient_details.find_one({'patient_id':ad['patient_id']},['name','contact'])
                    if patient_data:
                        data.append({'visit_id':ad['visit_id'],'patient_name':patient_data['name'],'patient_contact':patient_data['contact']})
                    continue
                if data:
                    return {'status_code':200,'data':data}
                else:
                    return {'status_code':400,'data':'Patient Data Not Found'}
            else:
                return {'status_code':400,'data':'Appointment Data Not Found'}
        else:
            return {'status_code':400,'data':'Location Data Not Found'}
    except Exception as e:
        print(e)
        return {'status_code':400,'data':'Data not found'}

def get_app_count_data(doc_id,dash_datetime):
    try:
        loc_info = list(doc_loc_details.find({"doc_id": doc_id},{"loc_id": 1, "loc_address": 1, "_id": 0}))
        loc_ids = [loc['loc_id'] for loc in loc_info]
        loc_addresses = {loc['loc_id']: loc['loc_address'] for loc in loc_info}
        if not loc_ids:
            return {'status_code':400,'data':'Location data not found'}
        else:
            pipeline = [{"$match": {"app_date": {"$lte": dash_datetime + datetime.timedelta(days=5),"$gte": dash_datetime - datetime.timedelta(days=5)},"loc_id": {"$in": loc_ids}}},
                        {"$group": {"_id": {"loc_id": "$loc_id","app_date": "$app_date","app_time_slot": "$app_time_slot"},"count": {"$sum": 1}}}]

            result = list(appointment_details.aggregate(pipeline))
            if result:
                data = []
                for item in result:
                    data.append({'Clinic':loc_addresses.get(item['_id']['loc_id'], "Address not found"), 'Date':item['_id']['app_date'],'Slot':item['_id']['app_time_slot'],'Appointments':item['count']})
                return {'status_code':200,'data':data}
            else:
                return {'status_code':400,'data':'No Appointments found'}
    except Exception as e:
        print(e)
        return {'status_code':400,'data':'Unable to fetch data at the moment'}
    
def get_appointment_details(visit_id:str):
    try:
        app_details = appointment_details.find_one({"visit_id":visit_id,'status': {"$in":[1,2]}},['patient_id','status'])
        if app_details:
            pat_details = patient_details.find_one({'patient_id':app_details['patient_id']},['name','gender','dob','contact'])
            pat_history = patient_history.find_one({'patient_id':app_details['patient_id'], "history.visit_id": visit_id},{'history.$':1})
            if pat_history:
                pat_details['history'] = pat_history['history'][-1]
            app_details.update(pat_details)
            return {'status_code':200,'data':app_details}
        else:
            return {'status_code':400,'data':'Appointment data not found'}
    except Exception as e:
        print(e)
        return {'status_code':400,'data':'Data Fetching Failed'}
    
def update_appointment_status(visit_id:str,status:int, insertion_time) -> dict:
        try:
            appointment_details.update_one({'visit_id':visit_id},{"$set":{'status':status, 'updated_at':insertion_time}})
            return {'status_code':200,'data':'Appointment Updated'}
        except Exception as e:
            print(e)
            return {'status_code':400,'data':'Data Updation Failed'}
