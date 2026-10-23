# StockFlow · Gestión de inventario con pipeline CI optimizado

**StockFlow** es una aplicación web (Flask + SQLite) para gestionar el inventario de un negocio:

- Alta, edición, búsqueda y baja de **productos** (SKU, precio, stock mínimo, categoría).
- Registro de **movimientos** de entrada y salida, con validación de stock insuficiente.
- **Panel** con KPIs: productos, unidades, valor del inventario y alertas de **stock bajo**.
- **API REST** (`/api/productos`, `/api/movimientos`, `/api/resumen`, `/api/categorias`).

```bash
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements-dev.txt
python seed.py        # datos de ejemplo (opcional)
python run.py         # http://localhost:5000
```

## Estrategia de branching (GitFlow simplificado)

```
main        ●────────────────●───────────── producción (releases)
             \              /
develop       ●──●────●────●─────────────── integración
                  \  /
feature/*          ●●                       nuevas funcionalidades
```

| Rama | Propósito | Etapas que ejecuta Jenkins |
|------|-----------|----------------------------|
| `feature/*` | Desarrollo de una funcionalidad | Build · Calidad · Tests unitarios/API |
| `develop` | Integración de features | + Tests E2E (Selenium) · SonarQube |
| `release/*`, `hotfix/*` | Estabilización / correcciones urgentes | + Empaquetado |
| `main` | Producción | Todo: Build · Calidad · Tests · E2E · SonarQube · Empaquetado |

Flujo: `feature/x` → merge a `develop` → merge a `main`.

## Pipeline de Jenkins

```
Preparación ─► Build ─────────────► Calidad de código ─────► Tests ───────────────► SonarQube ─► Empaquetado
               ├ Backend (Python)   ├ flake8 (PEP 8)          ├ Unitarios + API        (develop,     (main,
               └ Frontend (JS)      ├ black (formato)         └ E2E Selenium           main)          release)
                                    ├ ESLint (JS)               (develop, main o
                                    └ bandit (seguridad)         cambios en la UI)
post: always (JUnit + informes) · success / failure / unstable (estado en GitHub + correo) · aborted · cleanup
```

### Optimizaciones aplicadas

| Estrategia | Implementación |
|------------|----------------|
| **Ejecución paralela** | `parallel` en Build (Python ∥ JS), Calidad (4 linters, `failFast`) y Tests (unitarios ∥ Selenium). |
| **Cache** | `cacheDependencias`: el venv y `node_modules` se guardan en `$CI_CACHE` con clave = hash SHA-256 de `requirements*.txt` / `package-lock.json`. Si no cambian, se reutilizan (de minutos a ~0 s). También cache de descargas de pip y npm. |
| **Ejecución selectiva** | Por **rama** (`ramaInfo`), por **ficheros cambiados** (`changeset 'app/templates/**'` activa Selenium en una feature que toca la UI) y por **parámetros** (`FORZAR_E2E`, `FORZAR_SONAR`). `disableConcurrentBuilds(abortPrevious: true)` cancela builds obsoletos de la misma rama. |
| **Modular y reutilizable** | Shared Library `stockflow-ci-lib` (`ci/jenkins-lib`): `ramaInfo`, `cacheDependencias`, `githubStatus`, `notificarCorreo`, `resumenTests` y una plantilla de correo. Cualquier otro proyecto puede usarla con `@Library('stockflow-ci-lib')`. |

### Notificaciones

- **GitHub**: el pipeline publica el estado del commit (`pending` → `success`/`failure`/`error`) con la API de *commit statuses*. Se ve como ✅/❌ junto al commit y en los Pull Requests.
- **Correo** (Gmail): resumen HTML con rama, commit, tests y etapas ejecutadas.

## Estructura

```
app/                    Aplicación Flask (models, services, routes, templates, static)
tests/unit|api|e2e      Pruebas: reglas de negocio, API REST y UI con Selenium
ci/jenkins-lib/         Shared Library de Jenkins (vars/ + resources/)
infra/jenkins/          Jenkins + SonarQube en Docker, configurados como código (JCasC)
Jenkinsfile             Pipeline declarativo multibranch
.flake8 · pyproject.toml · eslint.config.js · sonar-project.properties
```

## Infraestructura

```bash
cd infra/jenkins
cp .env.example .env    # rellenar tokens y contraseñas
docker compose up -d --build
```

- Jenkins: <http://localhost:8080> (job **stockflow**, multibranch, revisa el repo cada 2 min)
- SonarQube: <http://localhost:9000>
