-- Table to store main Kaggle model info
CREATE TABLE kaggle_models (
    id SERIAL PRIMARY KEY,
    kaggle_url TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    scraped_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    downloads INT,
    usability TEXT,
    short_description TEXT,
    model_card TEXT -- store README or markdown content
    example_usage TEXT -- store example usage code snippets
);

-- Table to store tags (many-to-many relationship with models)
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE model_tags (
    model_id INT REFERENCES kaggle_models(id) ON DELETE CASCADE,
    tag_id INT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (model_id, tag_id)
);

-- Table for metadata fields
CREATE TABLE 
 (
    model_id INT REFERENCES kaggle_models(id) ON DELETE CASCADE PRIMARY KEY,
    collaborators TEXT[], -- array of collaborator names
    authors TEXT[],       -- array of metadata authors
    provenance TEXT       -- provenance info
);

CREATE TABLE variation_info (
    model_id INT REFERENCES kaggle_models(id) ON DELETE CASCADE PRIMARY KEY,
    variation TEXT,
    variation_version TEXT,
    variation_license TEXT,
    variation_downloads INT,
    model_card TEXT, -- store README or markdown content
    is_finetunable BOOLEAN,
    example_usage TEXT -- store example usage code snippets
);
