CREATE TABLE IF NOT EXISTS search_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    path VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    occurrences INT,
    search_term VARCHAR(255) NOT NULL
);
