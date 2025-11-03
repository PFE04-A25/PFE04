# Backend Database Architecture

## From Frontend to Backend: Database Implementation Migration

This document outlines the architectural changes made to move database operations from the frontend to the backend, implementing a clean separation of concerns using the Repository Design Pattern.

## Overview

Previously, our application directly connected to MongoDB from the frontend using TypeScript. This approach presented several challenges including:

- Limited separation of concerns
- Difficulty implementing complex validation
- Cross-platform compatibility issues

## Architecture Components

### Repository Design Pattern

We've implemented the **Repository Design Pattern**, which provides:

- A clean separation between data access logic and business logic
- Abstraction of the underlying database technology
- Improved testability through dependency injection
- Standardized CRUD operations across entities

### Component Structure

All Database classes extends the BaseModel or the  BaseRepository<T> 

```raw

db/
├── models/          # Data models representing database entities
├── repositories/    # Data access layer for CRUD operations
└── services/        # Business logic layer using repositories

```

```mermaid

classDiagram
    %% Base Classes
    class BaseModel {
        +str collection_name
        +ObjectId id
        +datetime created_at
        +datetime updated_at
        +__init__(**kwargs)
        +to_dict() Dict
    }

    class BaseRepository~T~ {
        +Type[T] model_class
        +MongoClient client
        +Database db
        +Collection collection
        +__init__(model_class, mongo_uri)
        +create(model: T) T
        +find_by_id(id: str) Optional[T]
        +find_all(filter_dict: Dict) List[T]
        +update(id: str, update_dict: Dict) Optional[T]
        +delete(id: str) bool
    }

    %% TestCase Classes
    class Example {
        +str collection_name = "Exemple"
        +__init__(**kwargs)
    }

    class ExampleRepository {
        +__init__(mongo_uri: str)
        +find_by_id(example_id) uuid
    }

    class ExampleService {
        +ExampleRepository repository
        +__init__()
        +create_example(test_type, source_code, test_case) TestCase
        +get_example(filter_dict) List[TestCase]
        +get_example(id) Optional[TestCase]
        +update_example(id, update_data) Optional[TestCase]
        +delete_example(id) bool
    }

    %% External Interfaces
    class FlaskAPI {
        +create_test_case() Response
        +get_test_cases() Response
        +update_test_case(id) Response
        +delete_test_case(id) Response
    }

    class MongoDB {
    }

    %% Relationships
    FlaskAPI ..> ExampleService : uses
    BaseModel <|-- Example : inherits
    BaseRepository <|-- ExampleRepository : inherits
    
    ExampleRepository --> Example : uses
    ExampleRepository ..> MongoDB : interacts
    
    ExampleService --> ExampleRepository : contains
    
    
    %% Generic Type Binding
    BaseRepository ..> BaseModel : T extends

```

#### Current Architecture

```mermaid
classDiagram

    %% Models Used by Services
    class Pipeline {
        +str collection_name = "pipelines"
        +str name
        +str version
        +str description
        +str language
        +bool active
        +List[Dict] prompts
    }

    class PromptTemplate {
        +str collection_name = "prompt_templates"
        +str name
        +str template
        +List[str] variables
        +str category
    }

    class CodeSnippet {
        +str collection_name = "code_snippets"
        +str code
        +str language
        +str description
    }

    class ModelInfo {
        +str collection_name = "model_info"
        +str model_name
        +str model_version
        +Dict parameters
        +str provider
    }

    class TestGeneration {
        +str collection_name = "test_generations"
        +str source_code_id
        +str model_id
        +List[str] generated_tests
        +datetime generated_at
    }

    class TestExecution {
        +str collection_name = "test_executions"
        +str test_generation_id
        +str status
        +str output
        +datetime executed_at
    }

    %% Model Relationships
    Pipeline --> PromptTemplate : uses
    Pipeline--> TestGeneration: uses
    CodeSnippet --> TestGeneration: references (source_code_id)
    ModelInfo --> TestGeneration : references (model_id)
    TestExecution --> TestGeneration : references (test_case_id)
```

#### Model Layer

Models represent the database entities and their properties.
The ``BaseModel`` provides common functionality like ID generation and timestamp management.

#### Repositories Layer

Repositories handle direct interaction with the database, providing CRUD operations:
The ``BaseRepository`` implements generic CRUD operations like ``create``, ``find_by_id``, ``find_all``, ``update`` and ``delete``.

#### Services Layer

Services encapsulate business logic, using repositories for data access.

#### API Layer

Flask routes expose the database operations through RESTful endpoints:

```python

@app.route("/db/testcases", methods=["POST"])
@app.route("/db/testcases", methods=["GET"])
@app.route("/db/testcases/<id>", methods=["DELETE"])
@app.route("/db/testcases/<id>", methods=["PUT"])

```

### Benefits of the New Architecture

1. Better Separation of Concerns: Each layer has a single responsibility
2. Enhanced Maintainability: Changes to the database don't require frontend changes
3. Consistent API: Standardized endpoints for all database operations
4. Improved Testability: Each layer can be tested independently
5. Scalability: Backend can be scaled separately from frontend

#### Testing

The architecture supports comprehensive testing:

- Unit tests for models and services
- Integration tests for DB
- API tests for endpoints

## Conclusion

Moving the database operations from the frontend to a backend API following the Repository Design Pattern has significantly improved our application's architecture. The separation of concerns, improved testing and enhanced maintainability make the application more robust and easier to extend.
