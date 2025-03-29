# 🚀 Backend API - Sistema RAG Multi-tenant

<div align="center">

[![Python](https://img.shields.io/badge/python-3.10-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.103.1-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Pytest](https://img.shields.io/badge/pytest-8.0.0-red.svg?style=flat-square&logo=pytest&logoColor=white)](https://docs.pytest.org)


</div>

## 📋 Contenido
- [Descripción](#-descripción)
- [Características](#-características)
- [Tecnologías](#-tecnologías)
- [Estructura](#-estructura-del-proyecto)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Tests](#-tests)
- [Documentación](#-documentación)

## 📝 Descripción

Backend desarrollado con FastAPI para un sistema de gestión documental inteligente con arquitectura RAG (Retrieval Augmented Generation) y soporte multi-tenant.

## ✨ Características

### 🏢 Arquitectura Multi-tenant
- Aislamiento seguro de datos por empresa
- Autenticación basada en JWT
- Control de acceso basado en roles

### 📄 Gestión Documental
- Subida y gestión de metadatos
- Pipeline automático de procesamiento
- Extracción de texto y chunking
- Seguimiento de estado de documentos

### 🤖 Implementación RAG
- Consultas documentales usando Google Gemini
- Respuestas contextuales inteligentes
- Registro y seguimiento de consultas

## 🛠️ Tecnologías

- **Framework**: FastAPI
- **Base de Datos**: Supabase (PostgreSQL)
- **Autenticación**: JWT con Supabase Auth
- **Almacenamiento**: Supabase Storage
- **Modelo LLM**: Google Gemini
- **Testing**: pytest

## 📂 Estructura del Proyecto

```
app/
├── auth/           # Middleware de autenticación y JWT
├── config/         # Configuración de BD y variables
├── core/           # Funcionalidades centrales
├── llm/           # Integración con Gemini
├── models/        # Modelos Pydantic
├── routers/       # Endpoints API
├── tests/         # Suite de pruebas
└── utils/         # Funciones auxiliares
```

## 🚀 Instalación

1. Clonar el repositorio:
```bash
git clone <url-repositorio>
cd Backend-FastAPI
```

2. Crear y activar entorno virtual:
```bash
python -m venv venv
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales:
# SUPABASE_URL=tu_url_supabase
# SUPABASE_KEY=tu_key_supabase
# GEMINI_API_KEY=tu_key_gemini
```

## 🔧 Uso

### Iniciar servidor de desarrollo:
```bash
uvicorn app.main:app --reload
```

### Endpoints Principales:

#### 🔐 Autenticación
- `POST /auth/login`: Login de usuario
- `POST /auth/register`: Registro de usuario
- `GET /auth/me`: Perfil del usuario actual

#### 🏢 Empresas
- `GET /companies`: Listar empresas
- `POST /companies`: Crear empresa
- `GET /companies/{id}`: Detalles de empresa

#### 📄 Documentos
- `POST /documents`: Subir documento
- `GET /documents`: Listar documentos
- `GET /documents/{id}`: Ver documento
- `POST /documents/{id}/process`: Procesar documento

#### 🤖 Consultas RAG
- `POST /rag/query`: Realizar consulta RAG

## 🧪 Tests

Ejecutar suite completa:
```bash
pytest
```

Ejecutar módulos específicos:
```bash
pytest app/tests/test_documents.py -v
pytest app/tests/test_rag_query.py -v
```

## 📖 Documentación

- Documentación API: `http://localhost:8000/docs`
- Documentación ReDoc: `http://localhost:8000/redoc`

## 📝 Notas de Desarrollo

- Implementación MVP enfocada en funcionalidad core
- Optimización de búsqueda vectorial planificada para futuras iteraciones
- Logging y monitoreo básico implementado
- Despliegue futuro planificado en GKE

## 📄 Licencia

MIT License

Copyright (c) 2024 [Tu Nombre o Nombre de tu Organización]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
