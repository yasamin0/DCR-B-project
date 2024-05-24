import os
import mysql.connector
from mysql.connector import Error

def check_subtree_depth(root_dir, min_depth):
    for root, dirs, files in os.walk(root_dir):
        depth = root[len(root_dir):].count(os.sep)
        if depth >= min_depth:
            return True
    return False

def verify_dcrb_subtree(root_dir):
    for root, dirs, files in os.walk(root_dir):
        if "DCRB" in dirs:
            dcrb_path = os.path.join(root, "DCRB")
            if check_subtree_depth(dcrb_path, 4):
                return dcrb_path
    return None

def verify_dcrb_contents(dcrb_path):
    file_count = 0
    level_count = set()
    for root, dirs, files in os.walk(dcrb_path):
        depth = root[len(dcrb_path):].count(os.sep)
        level_count.add(depth)
        file_count += len(files)
       # print(f"Debug: {root} contains {len(files)} files at depth {depth}. Total files so far: {file_count}, Levels: {len(level_count)}")
        
        if file_count >= 50 and len(level_count) >= 4:
            return True
    return False


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
        ) AUTO_INCREMENT=1
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
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            file_id INT,
            path VARCHAR(255),
            type VARCHAR(50),
            occurrences INT,
            search_term VARCHAR(255),
            size_bytes BIGINT,
            UNIQUE KEY unique_result_id (id, search_term),
            FOREIGN KEY (file_id) REFERENCES all_files(id)
        ) AUTO_INCREMENT=1
    """)
    
    # Reset auto-increment value for search_results table before each search
    cursor.execute("ALTER TABLE search_results AUTO_INCREMENT = 1")
    
    cursor.close()
    print("Tables 'all_files' and 'search_results' created successfully")

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
    

def list_directory(root_dir):
    with open('DCRB_listing.txt', 'w', encoding='utf-8') as f:
        for root, dirs, files in os.walk(root_dir):
            level = root.replace(root_dir, '').count(os.sep)
            indent = ' ' * 4 * level
            f.write('{}{}/\n'.format(indent, os.path.basename(root)))
            subindent = ' ' * 4 * (level + 1)
            for file in files:
                f.write('{}{}\n'.format(subindent, file))

# Replace this path with the actual path to your DCRB directory
dcrb_path = r"C:\level1\level2\level3\DCRB"

list_directory(dcrb_path)


def search_files(connection, start_path, search_term):
    cursor = connection.cursor()
    
    # Clear previous search results
    cursor.execute("DELETE FROM search_results")
    
    cursor.execute("SELECT id, file_name, full_path, file_type, file_size FROM all_files")
    files = cursor.fetchall()
    
    directory_occurrences = {}  # Dictionary to store occurrences per directory
    result_id = 1  # Initialize result_id for this search
    
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
            
            # Insert search result with result_id incremented for each result
            cursor.execute("""
                INSERT INTO search_results (id, file_id, path, type, occurrences, search_term, size_bytes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (result_id, file_id, full_path, file_type, occurrences, search_term, file_size))
            result_id += 1  # Increment result_id for the next result
    
    # Insert directory occurrences into search_results table
    for directory, occurrences in directory_occurrences.items():
        cursor.execute("""
            INSERT INTO search_results (id, file_id, path, type, occurrences, search_term, size_bytes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (result_id, None, directory, 'directory', occurrences, search_term, 0))  # Set size_bytes to 0 for directories
        result_id += 1  # Increment result_id for the next result
        
    connection.commit()
    cursor.close()

def main():
    connection = connect_to_database()
    if connection:
        create_files_table(connection)
        directory = r"C:\level1"  
        insert_files_into_table(directory, connection)

        # Check subtree depth
        if not check_subtree_depth(directory, 6):
            print("Directory tree does not have the required depth of 6.")
            return
        
        dcrb_path = verify_dcrb_subtree(directory)
        if not dcrb_path:
            print("DCRB subtree with required depth is not present.")
            return

        if not verify_dcrb_contents(dcrb_path):
            print("DCRB subtree does not meet the content requirements.")
            return
        
        search_term = input("What are you searching for? ").lower()
        search_files(connection, directory, search_term)
        connection.close()
        print("Search completed.")

if __name__ == "__main__":
    main()
