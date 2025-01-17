import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from dbops import get_app_count_data, get_doc_id, get_clinic_names, get_slots, get_appointments, get_appointment_details, update_appointment_status

def display_charts():
    result = get_app_count_data(st.session_state.temp['doc_id'],st.session_state.temp['dashboard_datetime'])
    if result['status_code'] == 400:
        st.error('No Appointments Found')
    else:
        df = pd.DataFrame(result['data'])

        chart_clinic = st.selectbox('Select Clinic', options=df['Clinic'].unique())

        cd_df = df[df['Date']==st.session_state.temp['dashboard_datetime']]

        if len(cd_df[cd_df['Clinic']==chart_clinic]) >0:
            st.subheader('Appointments Distribution')
            fig = px.pie(cd_df[cd_df['Clinic']==chart_clinic], values='Appointments', names='Slot',height=300, width=200)
            fig.update_layout(margin=dict(l=20, r=20, t=30, b=0),)
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader('Appointments History')
        st.bar_chart(df[df['Clinic']==chart_clinic],y="Appointments",x='Date',color='Slot',stack=False)        
        
        if len(cd_df['Clinic']) > 0:
            st.subheader('Interclinic Appointments Comparision')
            st.bar_chart(cd_df,y="Appointments",x='Clinic',color='Slot',stack=False)

        with st.expander("Want to check appointments data"):
            st.table(result['data'])


def display_appointments():
    if 'clinic' in st.session_state.temp and 'slot' in st.session_state.temp:
        clinic = st.session_state.temp['clinic']
        slot = st.session_state.temp['slot']
        
        result = get_appointments(clinic,slot,st.session_state.temp['dashboard_datetime'])
        if result['status_code']==400:
            st.warning("No Appointments Found")
        else:
            appointments = pd.DataFrame(result['data'])
            if not appointments.empty:
                st.table(appointments)
            
                selected_patient = st.selectbox("Select Patient", options=appointments['patient_name'].tolist(), index=None)
                if selected_patient:
                    selected_visit = appointments[appointments['patient_name']==selected_patient]['visit_id'].item()
                    if selected_visit != None:
                        st.session_state.temp['visit'] = selected_visit
                
                        display_visit()
    
def display_visit():
    if 'clinic' in st.session_state.temp and 'slot' in st.session_state.temp and 'visit' in st.session_state.temp:
        result = get_appointment_details(st.session_state.temp['visit'])
        if result['status_code'] == 400:
            st.warning("Appointment Details Not Found")
        else:
            with st.container(border=True):
                v1,v2= st.columns(2)
                with v1:
                    st.header("Patient Details",divider="blue")
                    st.write(f"_Name_ : {result['data']['name'].title()}")
                    st.write(f"_Gender_ : {result['data']['gender']}")
                    st.write(f"_Age_ : {int((datetime.datetime.now() - datetime.datetime.strptime(result['data']['dob'],'%d/%m/%Y')).days/365)}")
                    st.write(f"_Contact_ : {result['data']['contact']}")
                    st.write(f"_Appointment_ : {'Follow Up' if result['data']['status']==2 else 'New Patient'}")
                with v2:
                    if 'history' in result['data'].keys():
                        st.header("Medical Condition",divider="red")
                        if 'detected_symptoms' in result['data']['history'].keys():
                            st.write(f"_AI Detected Symptoms_ : {', '.join(result['data']['history']['detected_symptoms'])}")
                        # if 'symptoms' in result['data']['history'].keys():
                        #     if result['data']['history']['symptoms']:
                        #       st.write(f"_Symptoms_ : {result['data']['history']['symptoms']}")
                        if 'illness_duration' in result['data']['history'].keys():
                            if result['data']['history']['illness_duration']:
                                st.write(f"_Illness Duration_ : {result['data']['history']['illness_duration']}")
                        if 'ncd' in result['data']['history'].keys():
                            if result['data']['history']['ncd']:
                                st.write(f"_Pre Medical Condition_ : {result['data']['history']['ncd']}")
                        if 'detected_medications' in result['data']['history'].keys():
                            st.write(f"_AI Detected Medications_ : {', '.join(result['data']['history']['detected_medications'])}")
                        # if 'medications' in result['data']['history'].keys():
                        #     if result['data']['history']['medications']:
                        #         st.write(f"_Medications_ : {result['data']['history']['medications']}")

                appointment_option = st.radio("Select Operation for Appointment",options=["Completed", "Cancel", "Not Available"], index= None)
                if appointment_option != None:
                    status_map = {"Completed":3, "Cancel":0, "Not Available":4}
                    result = update_appointment_status(st.session_state.temp['visit'],status_map[appointment_option],datetime.datetime.now())
                    if result['status_code']==400:
                        st.warning("Sorry! Unable To Update Appointment Status")
                    else:
                        st.success(f"Appointment update to - {appointment_option}")

#Main App
st. set_page_config(layout="wide") 
st.title("Doctor's Appointment Dashboard")
if 'temp' not in st.session_state:
    st.session_state['temp'] = {}

dashboard_date = st.date_input('Select Date')
doc_contact = st.text_input('Enter Doctor Contact')
st.session_state.temp['doc_contact'] = doc_contact
st.session_state.temp['dashboard_datetime'] = datetime.datetime(year=dashboard_date.year,month=dashboard_date.month,day=dashboard_date.day,hour=0,minute=0,second=0,microsecond=0)

if doc_contact:
    result = get_doc_id(st.session_state.temp['doc_contact'])
    if result['status_code'] == 400:
        st.error('Invalid Contact Number')
    else:
        st.session_state.temp['doc_id'] = result['data']
    
        col1, col2 = st.columns(2)
        with col2:
            st.header("Clinic Management Insights")
            display_charts()

        with col1:
            st.header("Appointment Management")
            result = get_clinic_names(st.session_state.temp['doc_id'])
            if result['status_code']==400:
                st.error("No Clinic Found")
            else:
                if len(result['data']) ==1:
                    st.session_state.temp['clinic'] = result['data'][0]
                else:
                    selected_clinic = st.selectbox("Select Clinic", options=result['data'], index=None)
                    if selected_clinic != None:
                        st.session_state.temp['clinic'] = selected_clinic

                if 'clinic' in st.session_state.temp:
                    result = get_slots(st.session_state.temp['clinic'])
                    if result['status_code']==400:
                        st.error("No Slots Found")
                    else:
                        selected_slot = st.selectbox("Select Slot", options=result['data'], index=None)
                        if selected_slot != None:
                            st.session_state.temp['slot'] = selected_slot

                            display_appointments()
    
    


