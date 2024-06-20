# TypeLink

## Overview

TypeLink is a tool designed to generate TypeScript types and route constants from a Django backend to ensure consistency between the frontend and backend. It leverages `Django Spectacular` for generating OpenAPI schemas and `openapi-typescript` for converting these schemas to TypeScript types. This ensures that the types and URL routes are always in sync between both the frontend and backend.

## Features

- **Automatic Type Generation**: Generates TypeScript types from your Django backend.
- **Route Constants**: Extracts and generates route constants for use in your frontend.
- **Consistency**: Ensures that the types and routes remain consistent across your application.

## Project Structure

The project consists of a Django application for the backend and a React TypeScript application for the frontend, created using Vite.

- **Server Folder**: Contains the Django backend with a virtual environment.
- **Client Folder**: Contains the React application.

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- Python (v3.11 or higher)
- Django (with Django Rest Framework, Django Spectacular)

### Setup

1. **Backend Setup (Django)**:
    - Navigate to the `server` folder.
    - Activate the virtual environment:
      ```bash
      source venv/bin/activate
      ```
    - Install the required Python packages:
      ```bash
      pip install -r requirements.txt
      ```
    - Apply migrations:
      ```bash
      python manage.py migrate
      ```
    - Start the Django development server:
      ```bash
      python manage.py runserver
      ```

2. **Frontend Setup (React)**:
    - Navigate to the `client` folder.
    - Install the required Node.js packages:
      ```bash
      npm install
      ```
    - Start the Vite development server:
      ```bash
      npm run dev
      ```

### Usage

1. **Generating TypeScript Types**:
    - cd into the `client` folder.
    - Run the command
      ```bash
      node src/tools/generate-types.js  
      ```


2. **Generating TypeScript Routes**:
    - cd into the `client` folder.
      ```bash
      node src/tools/generate-routes.js  
      ```

By running the above commands you will see some new files generated in your `client/src/` folder.
```bash
src/
├── api-types/
│   ├── components/
│   │   └── schemas.d.ts
│   ├── routeTypes.d.ts
│   └── routePaths.ts
```



#### Sample Generated Schema:

```typescript
export interface Error {
    message: string;
    /** @description Short code describing the error */
    code: string;
}

export interface Item {
    id: number;
    name: string;
    description: string;
    /** Format: decimal */
    price?: string;
    /** Format: int64 */
    stock?: number;
}

export interface NotFound {
    detail: string;
}

export interface PatchedItem {
    id?: number;
    name?: string;
    description?: string;
    /** Format: decimal */
    price?: string;
    /** Format: int64 */
    stock?: number;
}
```

### Sample Generated Routes:

```typescript
export const Paths = {
  ITEM_SET_2: '/api/v1/items/',
  ITEM_SET_4_DETAIL: '/api/v1/items/{id}/',
} as const;

```



This will generate TypeScript types based on the OpenAPI schema and save them to the specified file.

### Additional Notes

- Make sure to update the OpenAPI schema and regenerate the TypeScript types whenever you make changes to your Django models or API endpoints to ensure consistency.
- For more information on using Django Spectacular and openapi-typescript, refer to their respective documentation.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
