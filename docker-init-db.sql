CREATE USER {{ project_name|lower }};
CREATE DATABASE {{ project_name|lower }};
GRANT ALL PRIVILEGES ON DATABASE {{ project_name|lower }} TO {{ project_name|lower }};

