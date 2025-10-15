-- Main NVIDIA model table
CREATE TABLE nvidia_models (
    id SERIAL PRIMARY KEY,
    nvidia_url TEXT UNIQUE NOT NULL,
    organization TEXT,
    scraped_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Junction table for many-to-many relationship between models and tags
CREATE TABLE model_tags (
    model_id INT REFERENCES nvidia_models(id) ON DELETE CASCADE,
    tag_id INT REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (model_id, tag_id)
);
