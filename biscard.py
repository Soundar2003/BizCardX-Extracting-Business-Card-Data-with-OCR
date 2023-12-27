import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
import pymysql
import os
import re



mydb = pymysql.connect(host="localhost",user="root",passwd="Soundar@2003",database="bizcardx_db")
mycursor = mydb.cursor()

mycursor = mydb.cursor()
mycursor.execute("CREATE DATABASE IF NOT EXISTS bizcardx_db")
mycursor.execute("USE bizcardx_db")

mycursor.execute('''CREATE TABLE IF NOT EXISTS card_data
                   (id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    company_name TEXT,
                    card_holder TEXT,
                    designation TEXT,
                    mobile_number VARCHAR(50),
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code VARCHAR(10)
                    )''')


reader = easyocr.Reader(['en'])


def save_card(file):

    try:
        if not os.path.exists("uploaded_cards"):
            os.makedirs("uploaded_cards")

        file_path = os.path.join("uploaded_cards", file.name)

        with open(file_path, "wb") as f:
            f.write(file.getbuffer())

    except:
        pass

    else:
        print(f"Card saved successfully: {file.name}")

def dis_image(file):
        st.markdown("### You have uploaded the card")
        st.image(file, width = 550)

data = {"company_name" : [],
    "card_holder" : [],
    "designation" : [],
    "mobile_number" :[],
    "email" : [],
    "website" : [],
    "area" : [],
    "city" : [],
    "state" : [],
    "pin_code" : [],
    }

def get_data(res):
    for ind,i in enumerate(res):
        # To get website url
        if "www " in i.lower() or "www." in i.lower():
            data["website"].append(i)
        elif "WWW" in i:
            data["website"] = res[4] +"." + res[5]
        # To get email ID
        elif "@" in i:
            data["email"].append(i)
        # To get mobile number
        elif "-" in i:
            data["mobile_number"].append(i)
            if len(data["mobile_number"]) ==2:
                data["mobile_number"] = " & ".join(data["mobile_number"])
        # To get company name  
        elif ind == len(res)-1:
            data["company_name"].append(i)
        # To get card holder name
        elif ind == 0:
            data["card_holder"].append(i)
        # To get designation
        elif ind == 1:
            data["designation"].append(i)
        # To get area
        if re.findall('^[0-9].+, [a-zA-Z]+',i):
            data["area"].append(i.split(',')[0])
        elif re.findall('[0-9] [a-zA-Z]+',i):
            data["area"].append(i)
        # To get city name
        match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
        match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
        match3 = re.findall('^[E].*',i)
        if match1:
            data["city"].append(match1[0])
        elif match2:
            data["city"].append(match2[0])
        elif match3:
            data["city"].append(match3[0])
        # To get state
        state_match = re.findall('[a-zA-Z]{9} +[0-9]',i)
        if state_match:
                data["state"].append(i[:9])
        elif re.findall('^[0-9].+, ([a-zA-Z]+);',i):
            data["state"].append(i.split()[-1])
        if len(data["state"])== 2:
            data["state"].pop(0)
        # To get pincode        
        if len(i)>=6 and i.isdigit():
            data["pin_code"].append(i)
        elif re.findall('[a-zA-Z]{9} +[0-9]',i):
            data["pin_code"].append(i[10:])





st.set_page_config(layout="wide")

selected = option_menu(
    menu_title = "BizCardX: Extracting Business Card Data with OCR",
    options = ["Home", "Upload and Extract", "Modify"],
    orientation = "horizontal")


if selected == "Home":
    
    col1,col2 = st.columns(2)
    with col1:
        st.image("home.png", width = 550)
  
    with col2:
        st.markdown('''#### :green[**Overview :**]''')
        st.markdown('''In this streamlit web app you can upload an image of a business card 
                    and extract relevant information from it using easyOCR. You can view, modify or delete the extracted data 
                    in this app. This app would also allow users to save the extracted information into a database along with 
                    the uploaded business card image. The database would be able to store multiple entries, each with its own 
                    business card image and extracted information.''')
        

if selected == "Upload and Extract":

    st.markdown("### Upload a Business Card")
    uploaded_card = st.file_uploader(" ",type=["png","jpeg","jpg"])

    if uploaded_card is not None:

        save_card(uploaded_card)

        dis_image(uploaded_card)

        #easy OCR
        saved_img = os.getcwd()+ "\\" + "uploaded_cards"+ "\\"+ uploaded_card.name
        result = reader.readtext(saved_img,detail = 0,paragraph=False)

        get_data(result)
        
        st.success("### Data Extracted!")
        df=pd.DataFrame(data)
        st.write(df)
        
        if st.button("Upload to Database"):
            for i,row in df.iterrows():

                sql = """INSERT INTO card_data(company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code)
                         VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                
                mycursor.execute(sql, tuple(row))
                mydb.commit()

            st.success("#### Uploaded to database successfully!")


# Modify menu    
if selected == "Modify":
    col1,col2,col3 = st.columns([3,3,2])
    col2.markdown("## Alter or Delete the data here")
    column1,column2 = st.columns(2,gap="large")
    try:
        with column1:
            mycursor.execute("SELECT card_holder FROM card_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to update", list(business_cards.keys()))
            st.markdown("#### Update or modify any data below")
            mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data WHERE card_holder=%s",
                            (selected_card,))
            result = mycursor.fetchone()


            company_name = st.text_input("Company_Name", result[0])
            card_holder = st.text_input("Card_Holder", result[1])
            designation = st.text_input("Designation", result[2])
            mobile_number = st.text_input("Mobile_Number", result[3])
            email = st.text_input("Email", result[4])
            website = st.text_input("Website", result[5])
            area = st.text_input("Area", result[6])
            city = st.text_input("City", result[7])
            state = st.text_input("State", result[8])
            pin_code = st.text_input("Pin_Code", result[9])
            if st.button("Commit changes to DB"):

                mycursor.execute("""UPDATE card_data SET company_name=%s,card_holder=%s,designation=%s,mobile_number=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                    WHERE card_holder=%s""", (company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,selected_card))
                mydb.commit()
                st.success("Information updated in database successfully.")
        with column2:
            mycursor.execute("SELECT card_holder FROM card_data")
            result = mycursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to Delete", list(business_cards.keys()))
            st.write(f"### You have selected :green[**{selected_card}'s**] card to delete")
            st.write("#### Proceed to delete this card?")
            if st.button("Yes Delete Business Card"):
                mycursor.execute(f"DELETE FROM card_data WHERE card_holder='{selected_card}'")
                mydb.commit()
                st.success("Business card information deleted from database.")
    except:
        st.warning("There is no data available in the database")
    
    if st.button("View updated data"):
        mycursor.execute("select company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code from card_data")
        updated_df = pd.DataFrame(mycursor.fetchall(),columns=["Company_Name","Card_Holder","Designation","Mobile_Number","Email","Website","Area","City","State","Pin_Code"])
        st.write(updated_df)            