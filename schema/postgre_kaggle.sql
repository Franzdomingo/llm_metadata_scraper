-- Table to store main Kaggle model info
CREATE TABLE kaggle_models (
    id SERIAL PRIMARY KEY,
    kaggle_model_url TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    author TEXT,
    created_on DATE,
    downloads INT,
    usability TEXT,
    short_description TEXT,
    model_card TEXT -- store README or markdown content
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
CREATE TABLE model_metadata (
    model_id INT REFERENCES kaggle_models(id) ON DELETE CASCADE PRIMARY KEY,
    collaborators TEXT[], -- array of collaborator names
    authors TEXT[],       -- array of metadata authors
    provenance TEXT       -- provenance info
);

-- Table for transformer-specific info (optional, for models that are transformers)
CREATE TABLE transformers_variation__info (
    model_id INT REFERENCES kaggle_models(id) ON DELETE CASCADE PRIMARY KEY,
    transformers_variation TEXT,
    transformers_variation_version TEXT,
    transformers_variation_license TEXT,
    transformers_variation_downloads INT,
    transformers_model_card TEXT, -- store README or markdown content
    transformers_description TEXT
);
