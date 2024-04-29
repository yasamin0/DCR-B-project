import os
import mysql.connector
from mysql.connector import Error

def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="@YasNaz7787#", 
            database="file_search"
        )
        print("Connection to database was successful.")
        return connection
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None

def create_files_table(connection):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS all_files (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_name VARCHAR(255),
            full_path VARCHAR(255),
            file_type VARCHAR(50),
            file_size BIGINT,
            contents LONGTEXT
        )
    """)
    
    # Adding indexes only if they don't exist
    try:
        cursor.execute("CREATE INDEX idx_filename ON all_files(file_name)")
    except mysql.connector.errors.ProgrammingError as e:
        if e.errno == 1061:  # Error number for duplicate key name
            print("Index 'idx_filename' already exists.")
        else:
            raise e
    
    try:
        cursor.execute("CREATE INDEX idx_fullpath ON all_files(full_path)")
    except mysql.connector.errors.ProgrammingError as e:
        if e.errno == 1061:
            print("Index 'idx_fullpath' already exists.")
        else:
            raise e
    
    try:
        cursor.execute("CREATE INDEX idx_filetype ON all_files(file_type)")
    except mysql.connector.errors.ProgrammingError as e:
        if e.errno == 1061:
            print("Index 'idx_filetype' already exists.")
        else:
            raise e
    
    cursor.close()
    print("Table 'all_files' created successfully")

def insert_files_into_table(directory, connection):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM all_files")
    if cursor.fetchone()[0] == 0:  # If the table is empty, then populate it
        print("Populating 'all_files' table...")
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_name, file_extension = os.path.splitext(file)
                file_size = os.path.getsize(file_path)
                
                # Read contents only for specific file types
                content = None
                if file_extension.lower() in ('.html', '.htm', '.txt', '.pdf', '.doc', '.docx'):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    except Exception as e:
                        print(f"Error reading file {file_path}: {e}")
                
                # Insert file details and contents into the database
                cursor.execute("""
                    INSERT INTO all_files (file_name, full_path, file_type, file_size, contents)
                    VALUES (%s, %s, %s, %s, %s)
                """, (file_name, file_path, file_extension, file_size, content))
                
        connection.commit()
        print("Files inserted into 'all_files' table successfully")
    else:
        print("The 'all_files' table is already populated; no new files will be added.")
    cursor.close()

def count_occurrences(file_path, search_term):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read().lower()
        return content.count(search_term.lower())
    except Exception as e:
        print(f"Could not process file {file_path}: {e}")
        return 0

def search_files(connection, start_path, search_term):
    cursor = connection.cursor()
    
    # Clear previous search results
    cursor.execute("DELETE FROM search_results")
    
    cursor.execute("SELECT id, file_name, full_path, file_type, file_size FROM all_files")
    files = cursor.fetchall()
    
    directory_occurrences = {}  # Dictionary to store occurrences per directory
    
    for file_id, file_name, full_path, file_type, file_size in files:
        occurrences = count_occurrences(full_path, search_term)
        if occurrences > 0:
            if os.path.isdir(full_path):
                # For directories, store them as path and type as 'directory'
                directory = full_path
                file_type = 'directory'
            else:
                directory = os.path.dirname(full_path)
            
            directory_occurrences[directory] = directory_occurrences.get(directory, 0) + occurrences
            
            print(f"File: {file_name}, Path: {full_path}, Occurrences: {occurrences}")
            
            cursor.execute("""
                INSERT INTO search_results (id, path, type, occurrences, search_term, size_bytes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (file_id, full_path, file_type, occurrences, search_term, file_size))
    
    # Insert directory occurrences into search_results table
    for directory, occurrences in directory_occurrences.items():
        cursor.execute("""
            INSERT INTO search_results (path, type, occurrences, search_term, size_bytes)
            VALUES (%s, %s, %s, %s, %s)
        """, (directory, 'directory', occurrences, search_term, 0))  # Set size_bytes to 0 for directories
        
    connection.commit()
    cursor.close()

def main():
    connection = connect_to_database()
    if connection:
        create_files_table(connection)
        directory = r"C:\level1"  # Adjust the path as needed
        insert_files_into_table(directory, connection)
        search_term = input("What are you searching for? ").lower()
        search_files(connection, directory, search_term)
        connection.close()
        print("Search completed.")

if __name__ == "__main__":
    main()
