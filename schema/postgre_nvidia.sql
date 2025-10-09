-- Main NVIDIA model table
CREATE TABLE nvidia_models (
    id SERIAL PRIMARY KEY,
    nvidia_model_url TEXT UNIQUE NOT NULL,
    model_card TEXT
);
