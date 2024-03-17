# Libraries used
import streamlit as st
import numpy as np
import PIL
from PIL import Image, ImageDraw
import cv2
import os
import pandas as pd
import streamlit as st
import cv2
import re
import easyocr
import pymysql
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

# Image to text:

# Create the reader object with desired languages
def DataConvertion(uploaded_image):
    reader = easyocr.Reader(['en'], gpu=False)
    if isinstance(uploaded_image, str):
        image = Image.open(uploaded_image)
    elif isinstance(uploaded_image, Image.Image):
        image = uploaded_image
    else:
        image = Image.open(uploaded_image)

    # Assuming 'image' is your image data or file path
    image_array = np.array(image)

    # Read text from the image
    text_read = reader.readtext(image_array)

    result = []
    for text in text_read:
        result.append(text[1])

    return result



def draw_boxes(uploaded_image,color='yellow', width=2):
        # Create the reader object with desired languages
    reader = easyocr.Reader(['en'], gpu=False)
    if isinstance(uploaded_image, str):
        image = Image.open(uploaded_image)
    elif isinstance(uploaded_image, Image.Image):
        image = uploaded_image
    else:
        image = Image.open(uploaded_image)

    # Assuming 'image' is your image data or file path
    image_array = np.array(image)

    # Read text from the image
    text_read = reader.readtext(image_array)


    # Create a new image with bounding boxes
    image_with_boxes = image.copy()
    draw = ImageDraw.Draw(image_with_boxes)
    
    # draw boundaries
    for bound in text_read:
        p0, p1, p2, p3 = bound[0]
        draw.line([*p0, *p1, *p2, *p3, *p0], fill=color, width=width) 

    st.image(image_with_boxes, width=400)  # Display the image


# data Extraction:
import re

def finding(res):
    data = {
        "Company_name": [],
        "Card_holder": [],
        "Designation": [],
        "Mobile_number": [],
        "Email": [],
        "Website": [],
        "Area": [],
        "City": [],
        "State": [],
        "Pin_code": [],
    }

    result = res[:]  # Create a copy of the original result list to avoid modifying it
    
    if result:
        name = result[0]
        data["Card_holder"].append(name)
        result.remove(name)

    if result:
        designation = result[0]
        data["Designation"].append(designation)
        result.remove(designation)

    if result:
        for item in result[:]:  # Iterate over a copy of the result list
            if "@" in item:
                email = item
                data["Email"].append(email)
                result.remove(email)  # Remove email from result list
        
    if result:
        for item in result[:]:  # Iterate over a copy of the result list
            if ".com" in item:
                web = item
                data["Website"].append(web)
                result.remove(item)

    if "Website" in data and not data["Website"]:
        for item in result:
            if item.startswith("www") or item.startswith("WWW"):
                web = item
                data["Website"].append(web)
                result.remove(web)
    
    if "WWW" in result:
        result.remove("WWW")        
    
    if result:
        mobile_numbers = [item for item in result if "-" in item]
        if len(mobile_numbers) >= 2:
            combined_mobile = " & ".join(mobile_numbers)
            data["Mobile_number"].append(combined_mobile)
            for mobile in mobile_numbers:
                result.remove(mobile)
        else:
            for item in result[:]:
                if "-" in item:
                    data["Mobile_number"].append(item)
                    result.remove(item)

    if result:
        street_name_pattern = r'\b\d+\s+[A-Za-z\s,]+\b'

        # Create a list to store the parts of the address
        address_parts = []

        # Iterate through the result list
        for item in result:
            # Use re.search() to search for the pattern in the item
            match = re.search(street_name_pattern, item)
            if match:
                # If the pattern is found, split the item by comma and add to the parts list
                matched_address = match.group()
                # Replace consecutive commas with a single comma before splitting
                matched_address = re.sub(r',{2,}', ',', matched_address)
                parts = [part.strip() for part in matched_address.split(',')]
                address_parts.extend(parts)

                # Assign values based on the length of the address parts list
                if len(address_parts) >= 1:
                    data["Area"].append(address_parts[0])
                if len(address_parts) >= 2:
                    data["City"].append(address_parts[1])
                if len(address_parts) >= 3:
                    data["State"].append(address_parts[2])

                # Remove the processed item from the result list
                result.remove(item)
    if "St ," in result:
        result.remove("St ,")
              

    if "City" in data and not data["City"]:
        city_pattern = r'\b(?:[A-Za-z]+(?:\s[A-Za-z]+)*)[,\s]*$'

        for item in result:
            # Use re.search() to search for the pattern in the item
            match = re.search(city_pattern, item)
            if match:
                city = match.group().strip()
                # Check if the city is not all uppercase
                if not city.isupper():
                    data["City"].append(city)
                    result.remove(city)  # Remove the matched city from the result list


    if result:
        state_pattern = r'([A-Za-z]+)\s+(\d{6})'
        for item in result:
            match = re.search(state_pattern, item)
            if match:
                state = match.group(1)  # Extract the state from the first captured group
                pin_code = match.group(2)
                data["State"].append(state)
                data["Pin_code"].append(pin_code)
                result.remove(item)

    if "Pin_code" in data and not data["Pin_code"]:
        for item in result:
            if len(item) >= 6 and item.isdigit():
                data["Pin_code"].append(item)
                result.remove(item)
            
                
    if result:
        # The remaining items in the result list are considered as the company name
        company_name = ' '.join(result)
        data["Company_name"].append(company_name)
    
    return data    


# Establish database connection and create table
myconnection = pymysql.connect(host='127.0.0.1', user='root', passwd='gowri@2903')
mycursor = myconnection.cursor()

try:
    mycursor.execute("CREATE DATABASE IF NOT EXISTS Bizcard")
    mycursor.execute("USE Bizcard")
    mycursor.execute("CREATE TABLE IF NOT EXISTS card_data (Company_name VARCHAR(255), Card_holder VARCHAR(255), Designation VARCHAR(255), Mobile_number VARCHAR(255), Email VARCHAR(255), Website VARCHAR(255), Area VARCHAR(255), City VARCHAR(255), State VARCHAR(255), Pin_code VARCHAR(255))")
except Exception as e:
    st.error(f"Error creating database and table: {e}")

# Function to update database with DataFrame
def connection_sql(data):
    st.table(data)
    try:
        for index, row in data.iterrows():
            company_name = row['Company_name']
            card_holder = row['Card_holder']
            designation = row['Designation']
            mobile_number = row['Mobile_number']
            email = row['Email']
            website = row['Website']
            area = row['Area']
            city = row['City']
            state = row['State']
            pin_code = row['Pin_code']
            mycursor.execute("""INSERT INTO card_data (Company_name, Card_holder, Designation, Mobile_number, Email, Website, Area, City, State, Pin_code)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE
                                Company_name = VALUES(Company_name),
                                Card_holder = VALUES(Card_holder),
                                Designation = VALUES(Designation),
                                Mobile_number = VALUES(Mobile_number),
                                Email = VALUES(Email),
                                Website = VALUES(Website),
                                Area = VALUES(Area),
                                City = VALUES(City),
                                State = VALUES(State),
                                Pin_code = VALUES(Pin_code)""",
                              (company_name, card_holder, designation, mobile_number, email, website, area, city, state, pin_code))
            myconnection.commit()
        st.success("Database updated successfully.")
    except:
        pass

# Sreamlit Part

st.header('BizCardX: Extracting Business Card Data with OCR', divider='rainbow')

import streamlit as st

col1, col2 = st.columns(2)

with col1:
    st.header(":open_file_folder: Image Upload")
    uploaded_images = st.file_uploader("Drag and drop JPG/PNG files here", accept_multiple_files=True, type=["jpg", "png"])
    st.image(uploaded_images)    

with col2:
   st.header(":magnet: Data Extraction")
   col1, col2 = st.columns(2)
   with col1:
      st.write("Data Cleansing")
      for uploaded_image in uploaded_images:
        result = DataConvertion(uploaded_image)
        value = finding(result)
        df = pd.DataFrame.from_dict(value)  # Convert to DataFrame
        df = df.transpose()  # Transpose the DataFrame to store data column-wise
        edited_df = st.data_editor(df, key="table_editor")  # Display DataFrame in Streamlit's data editor
        if st.button("Data Updated or No Change"):
            st.table(edited_df.transpose())  # Display the edited DataFrame as a table in the original orientation
        if st.button("Upload Data"):
            edited_df = edited_df.transpose()  # Convert back to DataFrame
            connection_sql(edited_df)  # Pass the DataFrame to the connection_sql() function

   with col2:
      st.write("Text Capture")
      result_image = draw_boxes(uploaded_image)

      myconnection = pymysql.connect(host='127.0.0.1', user='root', passwd='gowri@2903', database="Bizcard")
      mycursor = myconnection.cursor()
      mycursor.execute("SELECT card_holder FROM card_data")
      result = mycursor.fetchall()
      business_cards = {}
      for row in result:
         business_cards[row[0]] = row[0]
      selected_card = st.selectbox("Select a card holder name to Delete", list(business_cards.keys()))


      if st.button("Yes Delete Business Card"):
        mycursor.execute(f"DELETE FROM card_data WHERE card_holder='{selected_card}'")
        myconnection.commit()
        st.success("Business card information deleted from database.")

      

