import pickle

from flask import Flask, request, render_template, jsonify

app = Flask(__name__)




cities_list = ['Ahmedabad', 'Bengaluru', 'Chandigarh', 'Chennai', 'Coimbatore',
    'Delhi', 'Faridabad', 'Gurugram', 'Hyderabad', 'Jaipur', 'Kochi',
    'Kolkata', 'Lucknow', 'Madurai', 'Mohali', 'Mumbai', 'Noida',
    'Pune', 'Surat', 'Vadodara', 'other'
]
    # Define experience ranges with their corresponding labels
departments_data =  {'Administration & Facilities': ['Administration', 'Facility Management'],
 'BFSI, Investments & Trading':['General Insurance',
   'Banking Operations',
   'Others',
   'Lending',
   'Life Insurance'],
'Consulting':['IT Consulting',
   'Other Consulting',
   'Management Consulting'],
'Content, Editorial & Journalism':['Content Management (Print / Online / Electronic)',
   'Content, Editorial & Journalism - Others'],
 'Customer Success, Service & Operations'
 :['Customer Success',
   'Operations Support',
   'Others',
   'Operations',
   'Service Delivery',
   'After Sales Service & Repair',
   'Customer Success, Service & Operations - Other',
   'Voice / Blended',
   'Back Office'],
 'Data Science & Analytics' :['Business Intelligence & Analytics',
   'Data Science & Analytics - Other',
   'Data Science & Machine Learning'],
 'Engineering - Software & QA':['Others',
   'Quality Assurance and Testing',
   'DBA / Data warehousing',
   'DevOps',
   'Software Development'],
'Environment Health & Safety': ['Others',
   'Environment Health and Safety - Other',
   'Occupational Health & Safety'],
 'Finance & Accounting' : ['Finance & Accounting - Others',
   'Finance & Accounting - Other',
   'Finance',
   'Treasury',
   'Accounting & Taxation',
   'Audit & Control'],
 'Food, Beverage & Hospitality':['F&B Service',
   'Kitchen / F&B Production',
   'Food, Beverage & Hospitality - Others',
   'Front Office & Guest Services'],
 'Healthcare & Life Sciences': ['Doctor',
   'Imaging & Diagnostics',
   'Health Informatics',
   'Healthcare & Life Sciences - Other',
   'Nursing',
   'Other Hospital Staff'],
 'Human Resources': ['HR Operations',
   'Others',
   'Employee Relations',
   'Recruitment & Talent Acquisition',
   'Compensation & Benefits',
   'Human Resources - Other'],
 'Legal & Regulatory': ['Legal Operations',
   'Others',
   'Legal & Regulatory - Other',
   'Corporate Affairs'],
 'Marketing & Communication':['Digital Marketing',
   'Marketing',
   'Corporate Communication',
   'Marketing & Communication - Others',
   'Advertising & Creative'],
 'Merchandising, Retail & eCommerce': ['Retail Store Operations',
   'Merchandising, Retail & eCommerce - Others'],
 'Others':['Others - Others'],
 'Product Management': ['Product Management - Other',
   'Product Management - Technology'],
 'Production, Manufacturing & Engineering': ['Management',
   'Operations, Maintenance & Support',
   'Production & Manufacturing - Other',
   'Engineering'],
 'Project & Program Management':['Other Program / Project Management',
   'Technology / IT',
   'Finance',
   'Construction / Manufacturing'],
'Research & Development':['Others',
   'Research & Development - Other',
   'Pharmaceutical & Biotechnology',
   'Engineering & Manufacturing'],
 'Risk Management & Compliance': ['Risk Management & Compliance - Others',
   'Finance',
   'Risk Management & Compliance - Other'],
 'Sales & Business Development': ['Sales Support & Operations',
   'Others',
   'BD / Pre Sales',
   'Enterprise & B2B Sales'],
 'Sports, Fitness & Personal Care':['Others', 'Health & Fitness', 'Beauty & Personal Care'],
'Strategic & Top Management': ['Strategic & Top Management - Others',
   'Top Management']
}

experience_dict = {
    "Entry-level": (0, 1),
    "Junior": (1, 3),
    "Mid-level": (3, 5),
    "Experienced": (5, 10),
    "Senior": (10, 15),
    "Expert": (15, float('inf'))  # Using infinity for experience above 15
}

sal_dict  = {
    0: (0, 350000),
    1: (1000000, 1500000),
    2: (350000, 600000),
    3: (600000, 1000000),
    4: (1500000, float('inf'))  # Use float('inf') for 'above 1500000'
}



with open("salary_model.pkl", "rb") as file:
    model = pickle.load(file)



with open("Department_encoder.pkl", "rb") as file:
    department_encoder = pickle.load(file)

with open("role_category_encoder.pkl", "rb") as file:
    role_category_encoder = pickle.load(file)



with open("experience_Category_encoder.pkl", "rb") as file:
    experience_Category_encoder = pickle.load(file)

with open("city_encoder.pkl", "rb") as file:
    city_encoder = pickle.load(file)

with open("salencoder.pkl", "rb") as file:
    salencoder = pickle.load(file)


@app.route('/', methods=["GET"])
def root():
    # Pass departments data keys to the template
    departments = list(departments_data.keys())
    return render_template('index.html', departments=departments, cities_list=cities_list)

@app.route('/get_roles', methods=["POST"])
def get_roles():
    department = request.json.get("department")
    # Return the role categories for the selected department
    role_categories = departments_data.get(department, [])
    return jsonify({"roles": role_categories})

@app.route('/predict', methods=["POST"])

def predict_churn_value():
    department = department_encoder.transform([request.form.get('department')])
    city = city_encoder.transform([request.form.get('city')])
    role_category = role_category_encoder.transform([request.form.get("role_category")])
    experience = int(request.form.get("experience"))

    # Find the corresponding experience level
    experience_level = next((level for level, (min_exp, max_exp) in experience_dict.items() if min_exp <= experience <= max_exp), "Unknown")
    experience = experience_Category_encoder.transform([experience_level])

    education_ug = int(request.form.get("education_ug"))
    education_pg = int(request.form.get("education_pg"))

    # Model input and prediction
    result = [experience[0], city[0], education_ug, education_pg, department[0], role_category[0]]
    predicted_code = model.predict([result])[0]

    # Find salary range
    salary_range = next(
        (f"{min_exp} to {max_exp}" for salcode, (min_exp, max_exp) in sal_dict.items() if salcode == predicted_code),
        None
    )

    # If no valid prediction is found
    if not salary_range:
        return render_template("error.html", message="Something went wrong during prediction.")

    # Render the result page
    return render_template("result.html", salary_range=salary_range)

# @app.route('/predict', methods=["POST"])
# def predict_churn_value():
#     # Print form values to the console
#     print("Department:", request.form.get("department"))
#     print("Role Category:", request.form.get("role_category"))
#     print("Experience:", request.form.get("experience"))
#     print("UG:", request.form.get("education_ug"))
#     print("PG:", request.form.get("education_pg"))
    
#     return "Form values printed to console."

app.run(host="0.0.0.0", port=8000, debug=True)


#
# ['Administration & Facilities', 'BFSI, Investments & Trading',
#        'Consulting', 'Content, Editorial & Journalism',
#        'Customer Success, Service & Operations',
#        'Data Science & Analytics', 'Engineering - Software & QA',
#        'Environment Health & Safety', 'Finance & Accounting',
#        'Food, Beverage & Hospitality', 'Healthcare & Life Sciences',
#        'Human Resources', 'Legal & Regulatory',
#        'Marketing & Communication', 'Merchandising, Retail & eCommerce',
#        'Others', 'Product Management',
#        'Production, Manufacturing & Engineering',
#        'Project & Program Management', 'Research & Development',
#        'Risk Management & Compliance', 'Sales & Business Development',
#        'Sports, Fitness & Personal Care', 'Strategic & Top Management']