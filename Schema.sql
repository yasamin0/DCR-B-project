CREATE TABLE IF NOT EXISTS all_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255),
    full_path VARCHAR(255),
    file_type VARCHAR(50),
    file_size BIGINT,
    contents LONGTEXT
);

CREATE INDEX idx_filename ON all_files(file_name);
CREATE INDEX idx_fullpath ON all_files(full_path);
CREATE INDEX idx_filetype ON all_files(file_type);

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
);

ALTER TABLE search_results AUTO_INCREMENT = 1;

INSERT INTO all_files (file_name, full_path, file_type, file_size, contents)
                    VALUES (%s, %s, %s, %s, %s);

DELETE FROM search_results;

SELECT id, file_name, full_path, file_type, file_size FROM all_files;

INSERT INTO search_results (id, file_id, path, type, occurrences, search_term, size_bytes)
                VALUES (%s, %s, %s, %s, %s, %s, %s);

INSERT INTO search_results (id, file_id, path, type, occurrences, search_term, size_bytes)
            VALUES (%s, %s, %s, %s, %s, %s, %s);

