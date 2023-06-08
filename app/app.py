import os
import tempfile
from flask import Flask, request, jsonify
import csv
import sqlite3
from flask_cors import CORS
from uuid import uuid4

app = Flask(__name__)
CORS(app, support_credentials=True)

# SQLite database configuration
DB_NAME = 'database.db'
TABLES = {
    'departments': ['id', 'department'],
    'jobs': ['id', 'job'],
    'hired_employees': ['id', 'name', 'datetime', 'department_id', 'job_id']
}

def create_database():
    """
    Crea la base de datos SQLite y las tablas necesarias si no existen.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for table_name, columns in TABLES.items():
        columns_str = ', '.join([f'{col} TEXT' for col in columns])
        query = f'CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})'
        cursor.execute(query)

    conn.commit()
    conn.close()

def get_existing_ids(table_name):
    """
    Obtiene los IDs existentes en la tabla especificada.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = f'SELECT id FROM {table_name}'
    cursor.execute(query)
    existing_ids = [row[0] for row in cursor.fetchall()]

    conn.close()

    return existing_ids

@app.route('/upload', methods=['POST'])
def upload_csv():
    """
    Endpoint para recibir datos históricos en formato CSV y cargarlos en la base de datos.
    """
    file = request.files['file']
    table_name = request.form.get('table')

    if file and table_name:
        try:
            # Guardar el archivo CSV en una ubicación temporal
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, file.filename)
            file.save(temp_path)

            print('Temp Path:',temp_path)

            with open(temp_path, 'r') as csv_file:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()

                csv_reader = csv.reader(csv_file)
                columns = TABLES[table_name]
                query = f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES ({", ".join(["?"] * len(columns))})'

                existing_ids = get_existing_ids(table_name)
                print(existing_ids)
                rows = []
                for row in csv_reader:
                    print(row)
                    row_id = row[0]
                    print(row_id)
                    if row_id not in existing_ids:
                        rows.append(tuple(row))
                        existing_ids.append(row_id)

                    if len(rows) >= 1000:
                        cursor.executemany(query, rows)
                        rows = []

                if rows:
                    cursor.executemany(query, rows)

                conn.commit()
                conn.close()
            # Eliminar el archivo temporal después de procesarlo
            os.remove(temp_path)

            return 'Data uploaded successfully'

        except Exception as e:
            return f'Error: {str(e)}', 500

    return 'Invalid request', 400

@app.route('/query', methods=['GET'])
def query_data():
    table_name = request.args.get('table')

    if table_name:
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            query = f'SELECT * FROM {table_name}'
            cursor.execute(query)
            rows = cursor.fetchall()

            conn.close()

            columns = TABLES[table_name]
            results = []
            for row in rows:
                result = {}
                for i, col in enumerate(columns):
                    result[col] = row[i]
                results.append(result)

            return jsonify(results)

        except Exception as e:
            return f'Error: {str(e)}', 500

    return 'Invalid request', 400

@app.route('/delete', methods=['POST'])
def delete_data():
    table_name = request.form.get('table')
    filter_column = request.form.get('filter_column')
    filter_value = request.form.get('filter_value')

    if table_name and filter_column and filter_value:
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            query = f'DELETE FROM {table_name} WHERE {filter_column} = ?'
            cursor.execute(query, (filter_value,))
            conn.commit()
            conn.close()

            return 'Data deleted successfully'

        except Exception as e:
            return f'Error: {str(e)}', 500

    return 'Invalid request', 400

@app.route('/truncate/<table_name>', methods=['POST'])
def truncate_table(table_name):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        query = f'DELETE FROM {table_name}'
        print('Query:', query)
        cursor.execute(query)
        conn.commit()
        conn.close()

        return 'Table truncated successfully'

    except Exception as e:
        print('Error:', str(e))
        return f'Error: {str(e)}', 500

@app.route('/metrics/employees-by-job-department', methods=['GET'])
def get_employees_by_job_department():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        query = '''
        SELECT 
            departments.department AS department,
            jobs.job AS job,
            SUM(CASE WHEN strftime('%Y', datetime) = '2021' AND strftime('%m', datetime) BETWEEN '01' AND '03' THEN 1 ELSE 0 END) AS Q1,
            SUM(CASE WHEN strftime('%Y', datetime) = '2021' AND strftime('%m', datetime) BETWEEN '04' AND '06' THEN 1 ELSE 0 END) AS Q2,
            SUM(CASE WHEN strftime('%Y', datetime) = '2021' AND strftime('%m', datetime) BETWEEN '07' AND '09' THEN 1 ELSE 0 END) AS Q3,
            SUM(CASE WHEN strftime('%Y', datetime) = '2021' AND strftime('%m', datetime) BETWEEN '10' AND '12' THEN 1 ELSE 0 END) AS Q4
        FROM hired_employees
        INNER JOIN departments ON hired_employees.department_id = departments.id
        INNER JOIN jobs ON hired_employees.job_id = jobs.id
        GROUP BY department, job
        ORDER BY department ASC, job ASC
        '''

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        columns = ['department', 'job', 'Q1', 'Q2', 'Q3', 'Q4']
        results = [{col: row[i] for i, col in enumerate(columns)} for row in rows]

        return jsonify(results)

    except Exception as e:
        return f'Error: {str(e)}', 500
    
@app.route('/metrics/departments-with-highest-hiring', methods=['GET'])
def get_departments_with_highest_hiring():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        query = '''
        SELECT
            departments.id AS id,
            departments.department AS department,
            COUNT(hired_employees.id) AS hired
        FROM departments
        INNER JOIN hired_employees ON departments.id = hired_employees.department_id
        WHERE strftime('%Y', hired_employees.datetime) = '2021'
        GROUP BY departments.id
        HAVING hired > (SELECT AVG(department_hiring_count) FROM (SELECT COUNT(id) AS department_hiring_count FROM hired_employees WHERE strftime('%Y', datetime) = '2021' GROUP BY department_id))
        ORDER BY hired DESC
        '''

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        columns = ['id', 'department', 'hired']
        results = [{col: row[i] for i, col in enumerate(columns)} for row in rows]

        return jsonify(results)

    except Exception as e:
        return f'Error: {str(e)}', 500

if __name__ == '__main__':
    create_database()
    app.run(debug=True)