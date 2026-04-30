from flask import Flask, render_template, request, jsonify, session, send_file
import numpy as np
import pandas as pd
import pickle
import os
from export_utils import create_excel_export, create_pdf_export, generate_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Load trained model
with open("model.pkl", "rb") as f:
    model = pickle.load(f)
print("Model loaded: model.pkl")

HISTORY_FILE = "history.csv"


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get form data matching dataset columns
        student_name = request.form['student_name']

        # Validate student name - only letters and spaces allowed
        if not student_name.replace(' ', '').isalpha():
            return jsonify({'error': 'Student name must contain only letters and spaces'})

        attendance = float(request.form['attendance'])
        assignment_score = float(request.form['assignment_score'])
        internal_marks = float(request.form['internal_marks'])

        # Validate input
        if not (0 <= attendance <= 100):
            return jsonify({'error': 'Attendance must be between 0 and 100'})

        if not (0 <= assignment_score <= 20):
            return jsonify({'error': 'Assignment score must be between 0 and 20'})

        if not (0 <= internal_marks <= 30):
            return jsonify({'error': 'Internal marks must be between 0 and 30'})

        # Make prediction
        features = np.array([[attendance, assignment_score, internal_marks]])
        predicted_marks = model.predict(features)[0]
        predicted_marks = max(0, min(100, predicted_marks))
        rounded_pred = round(predicted_marks, 2)

        # Determine grade
        if predicted_marks >= 90:
            grade = 'A+'
        elif predicted_marks >= 80:
            grade = 'A'
        elif predicted_marks >= 70:
            grade = 'B'
        elif predicted_marks >= 60:
            grade = 'C'
        elif predicted_marks >= 50:
            grade = 'D'
        else:
            grade = 'F'

        # Determine performance category
        if predicted_marks >= 80:
            performance = 'Excellent'
        elif predicted_marks >= 60:
            performance = 'Good'
        elif predicted_marks >= 40:
            performance = 'Average'
        else:
            performance = 'Needs Improvement'

        # Save to history.csv
        row = pd.DataFrame([{
            "student_name": student_name,
            "attendance": attendance,
            "assignment_score": assignment_score,
            "internal_marks": internal_marks,
            "prediction": rounded_pred,
            "grade": grade
        }])

        if os.path.exists(HISTORY_FILE):
            row.to_csv(HISTORY_FILE, mode="a", header=False, index=False)
        else:
            row.to_csv(HISTORY_FILE, index=False)

        return jsonify({
            'student_name': student_name,
            'predicted_marks': rounded_pred,
            'grade': grade,
            'performance': performance,
            'success': True
        })

    except ValueError as e:
        return jsonify({'error': 'Please enter valid numeric values'})
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})


@app.route('/history')
def history():
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        data = df.to_dict(orient="records")
    else:
        data = []

    return render_template('history.html', history=data)


@app.route('/clear-history', methods=['POST'])
def clear_history():
    try:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
            return {"success": True, "message": "History cleared successfully"}
        else:
            return {"success": True, "message": "No history to clear"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@app.route('/export/excel')
def export_excel():
    try:
        if os.path.exists(HISTORY_FILE):
            df = pd.read_csv(HISTORY_FILE)
            history_data = df.to_dict(orient="records")
        else:
            history_data = []

        if not history_data:
            return {"success": False, "message": "No data to export"}

        excel_file = create_excel_export(history_data)
        filename = generate_filename("xlsx")

        return send_file(
            excel_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return {"success": False, "message": f"Excel export failed: {str(e)}"}


@app.route('/export/pdf')
def export_pdf():
    try:
        if os.path.exists(HISTORY_FILE):
            df = pd.read_csv(HISTORY_FILE)
            history_data = df.to_dict(orient="records")
        else:
            history_data = []

        if not history_data:
            return {"success": False, "message": "No data to export"}

        pdf_file = create_pdf_export(history_data)
        filename = generate_filename("pdf")

        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        return {"success": False, "message": f"PDF export failed: {str(e)}"}


@app.route('/api/model-info')
def model_info():
    if hasattr(model, 'coef_'):
        coefficients = model.coef_.tolist()
        intercept = model.intercept_
        feature_names = ['Attendance (%)', 'Assignment Score', 'Internal Marks']

        feature_importance = list(zip(feature_names, coefficients))
        feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)

        return jsonify({
            'feature_importance': feature_importance,
            'intercept': intercept,
            'model_type': 'Linear Regression'
        })
    else:
        return jsonify({'error': 'Model not available'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
