# TypeLink

## Overview

TypeLink is a tool designed to generate TypeScript types and route constants from a Django backend to ensure consistency between the frontend and backend. It leverages `Django Spectacular `for generating OpenAPI schemas and `openapi-typescript` for converting these schemas to TypeScript types. This ensures that the types and URL routes are always in sync between both the frontend and backend.

## Features

- **Automatic Type Generation**: Generates TypeScript types from your Django backend.
- **Route Constants**: Extracts and generates route constants for use in your frontend.
- **Consistency**: Ensures that the types and routes remain consistent across your application.

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- Python (v3.11 or higher)
- Django (with Django Rest Framework, Django Spectacular)

### Backend Setup

1. **Install Django Spectacular**:

    ```bash
    pip install drf-spectacular
    ```

2. **Configure Django Spectacular**:

    Add the following to your `settings.py`:

    ```python
    INSTALLED_APPS = [
        ...
        'drf_spectacular',
        ...
    ]

    REST_FRAMEWORK = {
        ...
        'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
        ...
    }

    SPECTACULAR_SETTINGS = {
        'TITLE': 'Your Project API',
        'DESCRIPTION': 'API documentation',
        'VERSION': '1.0.0',
        ...
    }
    ```

3. **Add Schema and URL Views**:

    Create a file `openapi/urls.py`:

    ```python
    from django.urls import path
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    app_name = 'openapi'
    urlpatterns = [
        path('swagger/', SpectacularSwaggerView.as_view(url_name='openapi:schema')),
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    ]
    ```

    Include these URLs in your `urls.py`:

    ```python
    urlpatterns = [
        ...
        path('openapi/', include('openapi.urls')),
        ...
    ]
    ```

### Frontend Setup

1. **Install Dependencies**:

    ```bash
    npm install openapi-typescript ts-morph
    ```

2. **Setup Project Structure**:

    Ensure the following structure in your frontend project:

    ```
    src/
    ├── api-types/
    │   ├── components/
    │   │   └── schemas.d.ts
    │   ├── routeTypes.d.ts
    │   └── routePaths.ts
    └── tools/
        └── generate-types.js
        └── generate-routes.js
    ```

3. **Generate Types and Routes**:

    Create the `generate-types.js`:

    ```javascript
    import fs from 'node:fs';
    import openapiTS from 'openapi-typescript';
    import { Project, ts } from 'ts-morph';

    // Constants
    const OAPI_SCHEMA_URL = 'http://localhost:8000/api/schema';
    const ROUTE_TYPES_FILE = './src/api-types/routeTypes.d.ts';
    const SCHEMA_TYPES_FILE = './src/api-types/components/schemas.d.ts';
    const builtinNames = ['Object'];

    // Ensure directories
    if (!fs.existsSync('./src/api-types')) {
        fs.mkdirSync('./src/api-types');
    }

    if (!fs.existsSync('./src/api-types/components')) {
        fs.mkdirSync('./src/api-types/components');
    }

    // Fetch schema
    console.log('Fetching schema...');
    const commonRouteTypes = await openapiTS(OAPI_SCHEMA_URL);
    fs.writeFileSync(ROUTE_TYPES_FILE, commonRouteTypes);

    // Transform schema
    const project = new Project();
    const routeTypesFile = project.addSourceFileAtPath(ROUTE_TYPES_FILE);
    const schemasFile = project.createSourceFile(SCHEMA_TYPES_FILE, '', {
        overwrite: true,
    });

    const componentsInterface = routeTypesFile.getInterface('components').getProperty('schemas');
    const SchemasProperties = componentsInterface.getTypeNode().getProperties();

    for (const property of SchemasProperties) {
        const structure = property.getStructure();
        const name = builtinNames.includes(structure.name) ? structure.name + '_' : structure.name;

        if (property.getTypeNode().isKind(ts.SyntaxKind.TypeLiteral)) {
            const _interface = schemasFile.addInterface({
                name: name,
                docs: structure.docs,
                isExported: true,
            });

            for (const prop of property.getTypeNode().getProperties()) {
                _interface.addMember(
                    prop.getFullText().trim().replaceAll(/components\["schemas"]\["(\w+)"]/g, (_, name) => {
                        return builtinNames.includes(name) ? name + '_' : name;
                    })
                );
            }
        } else {
            schemasFile.addTypeAlias({
                name: name,
                isExported: true,
                type: structure.type.replaceAll(/components\["schemas"]\["(\w+)"]/g, (_, name) => {
                    return builtinNames.includes(name) ? name + '_' : name;
                }),
            });
        }

        property.set({
            type: (w) => w.write(`import("./components/schemas.d.ts").${name}`),
        });
    }

    schemasFile.formatText({});
    schemasFile.save().then();
    routeTypesFile.save().then();
    ```

    Create the `generate-routes.js`:

    ```javascript
    import fs from 'node:fs';
    import ts from 'typescript';

    function extractPaths(filePath) {
        const program = ts.createProgram([filePath], {});
        const checker = program.getTypeChecker();
        const source = program.getSourceFile(filePath);
        const paths = new Map();

        ts.forEachChild(source, (rootNodes) => {
            if (!ts.isInterfaceDeclaration(rootNodes)) return;

            const symbol = checker.getSymbolAtLocation(rootNodes.name);
            if (symbol.name !== 'paths') return;

            ts.forEachChild(rootNodes, (pathInterfaceNodes) => {
                if (!ts.isPropertySignature(pathInterfaceNodes)) return;

                const path = checker.getSymbolAtLocation(pathInterfaceNodes.name).name;
                const operationNames = [];

                ts.forEachChild(pathInterfaceNodes.type, (operationsNode) => {
                    if (!ts.isPropertySignature(operationsNode)) return;

                    operationNames.push(operationsNode.type.indexType.literal.text);
                });

                let routeName = '';
                const routeOperations = new Set();
                const regex = '^(list|create|partialUpdate|update|retrieve|destroy)';

                for (const operationName of operationNames) {
                    const m = operationName.match(new RegExp(regex, 'i'));
                    if (m) {
                        routeOperations.add(m[1].toLowerCase());
                    }
                    const newRouteName = operationName.replaceAll(new RegExp(regex, 'gi'), '');
                    if (newRouteName.length > routeName.length) {
                        routeName = newRouteName;
                    }
                }

                if (routeOperations.has('list')) {
                    routeName = `${routeName}_list`;
                }

                if (
                    path.replace(/\/$/, '').split('/').at(-1).includes('{') &&
                    ['partialupdate', 'update', 'retrieve', 'destroy'].some((e) => routeOperations.has(e))
                ) {
                    routeName = `${routeName}_detail`;
                }

                routeName = routeName.replace(/(([a-z])(?=[A-Z][a-zA-Z])|([A-Z])(?=[A-Z][a-z]))/g, '$1_').toUpperCase();

                paths.set(routeName, path);
            });
        });

        return new Map([...paths.entries()].sort());
    }

    function buildPathsRecord(paths, recordName) {
        const output = [`export const ${recordName} = {`];
        for (const [key, val] of paths.entries()) {
            output.push(`  ${key.replaceAll('-', '_')}: '${val}',`);
        }
        output.push('} as const;');
        return output.join('\n');
    }

    const routePaths = [['./src/api-types/routeTypes.d.ts', 'Paths']]
        .map(([filePath, recordName]) => buildPathsRecord(extractPaths(filePath), recordName))
        .join('\n\n');

    fs.writeFileSync('./src/api-types/routePaths.ts', routePaths + '\n');
    ```

4. **Run the Generators**:

    ```bash
    node src/tools/generate-types.js
    node src/tools/generate-routes.js
    ```

## Usage

Once the types and routes are generated, you can import and use them in your frontend application as follows:

```typescript
import { Paths } from './api-types/routePaths';
import { components } from './api-types/routeTypes';

// Example usage
const item: components['schemas']['Item'] = {
    name: 'Sample Item',
    description: 'This is a sample item',
    price: 100.00,
    stock: 10,
};

const itemListPath = Paths.ITEM_LIST;
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

This project is licensed under the MIT License.

## Contact

If you have any questions, feel free to reach out to the project maintainers.

---

By using TypeLink, you can ensure that your frontend and backend are always in sync, reducing the risk of errors and making your development process more efficient. Happy coding!