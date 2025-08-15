# Cash Flow Analytics SaaS

Una aplicación completa de análisis de flujo de caja para PYMEs, construida con Streamlit como MVP pero con arquitectura lista para SaaS.

## 🚀 Características

### Funcionalidades Principales
- **📥 Importación de Datos**: Carga masiva desde CSV/Excel y entrada manual de transacciones
- **📈 Proyecciones**: Flujo de caja mensual por método directo hasta 24 meses
- **🧪 Escenarios**: Modelado de casos Base/Optimista/Pesimista con comparación
- **📊 KPIs**: Saldo mínimo, meses de runway, burn rate, DSCR, caja final
- **📋 Reportes**: Exportación a Excel y PDF con gráficos y análisis

### Arquitectura Técnica
- **Backend**: Python 3.11+ con SQLModel y SQLite (ready for PostgreSQL)
- **Frontend**: Streamlit con componentes modulares
- **Autenticación**: streamlit-authenticator (ready for OAuth/SAML)
- **Multimoneda**: Soporte completo con tipos de cambio
- **Multi-tenant**: Arquitectura preparada para múltiples empresas

## 📦 Instalación

### Requisitos Previos
- Python 3.11 o superior
- pip (gestor de paquetes de Python)

### Configuración del Entorno

1. **Clonar el repositorio** (si aplica):
```bash
git clone <repository-url>
cd cashflow-saas
```

2. **Crear entorno virtual**:
```bash
python -m venv venv

# En Windows:
venv\Scripts\activate

# En Linux/Mac:
source venv/bin/activate
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

### Inicialización de la Base de Datos

4. **Crear estructura de base de datos**:
```bash
python -m src.core.db --init
```

5. **Cargar datos de ejemplo**:
```bash
python -m src.core.db --seed
```

## 🏃‍♂️ Ejecución

### Localmente:
```bash
streamlit run app.py
```

La aplicación estará disponible en: http://localhost:8501

### 🚀 Streamlit Cloud (Recomendado):

1. **Fork este repositorio** en tu cuenta de GitHub
2. **Visita**: https://share.streamlit.io/
3. **Conecta tu GitHub** y selecciona este repositorio
4. **Main file path**: `app.py`
5. **Deploy!** 

La aplicación se auto-inicializará con datos de ejemplo en el primer acceso.

### Usuarios Demo

La aplicación viene con usuarios de demostración configurados:

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| admin | admin123 | Admin |
| analyst | analyst123 | Analyst |

## 📂 Estructura del Proyecto

```
cashflow-saas/
├── app.py                      # Aplicación principal de Streamlit
├── requirements.txt            # Dependencias Python
├── README.md                   # Este archivo
├── .streamlit/
│   └── config.toml            # Configuración de Streamlit
├── src/
│   ├── auth/                  # Sistema de autenticación
│   │   ├── auth.py           # Lógica de autenticación
│   │   └── users.yaml        # Usuarios y roles (hashed)
│   ├── core/                 # Lógica de negocio central
│   │   ├── models.py         # Modelos SQLModel
│   │   ├── schemas.py        # DTOs Pydantic
│   │   ├── db.py            # Sesión DB, init, seed
│   │   ├── logic.py         # Proyecciones y KPIs
│   │   ├── fx.py            # Soporte multimoneda
│   │   ├── exporters.py     # Excel y PDF export
│   │   └── utils.py         # Utilidades
│   └── ui/
│       ├── components.py     # Componentes UI reutilizables
│       └── pages/           # Páginas de la aplicación
│           ├── 1_🏠_Dashboard.py
│           ├── 2_📥_Transacciones.py
│           ├── 3_⚙️_Supuestos_y_Drivers.py
│           ├── 4_📈_Proyecciones.py
│           ├── 5_🧪_Escenarios.py
│           ├── 6_📊_Reportes.py
│           └── 7_🛠️_Admin.py
├── data/                     # Datos de ejemplo
│   ├── sample_tx.csv        # Transacciones de ejemplo
│   └── fx_rates_sample.csv  # Tipos de cambio
└── tests/                   # Tests automatizados
    ├── test_logic.py        # Tests de lógica de negocio
    └── test_imports.py      # Tests de importación
```

## 🔧 Uso de la Aplicación

### Flujo de Trabajo Típico

1. **Login**: Usar credenciales demo (admin/admin123 o analyst/analyst123)

2. **Importar Datos**:
   - Ir a "📥 Transacciones"
   - Subir archivo CSV/Excel o ingresar manualmente
   - Mapear categorías a cuentas contables

3. **Configurar Supuestos**:
   - Ir a "⚙️ Supuestos y Drivers"
   - Ajustar tasas de crecimiento, DSO, DPO, etc.

4. **Ver Proyecciones**:
   - Ir a "📈 Proyecciones"
   - Revisar flujo de caja proyectado a 24 meses
   - Analizar KPIs clave

5. **Crear Escenarios**:
   - Ir a "🧪 Escenarios"
   - Crear casos optimista/pesimista
   - Comparar resultados

6. **Generar Reportes**:
   - Ir a "📊 Reportes"
   - Exportar a Excel/PDF
   - Compartir con stakeholders

### Estructura de Datos

#### Formato CSV de Transacciones
```csv
date,category,description,amount,currency,account,paid
2024-01-15,Sales,Product Revenue,50000.00,USD,Revenue,true
2024-01-30,Payroll,January Salaries,-28000.00,USD,Salaries,true
```

#### Supuestos Clave
- **Sales Growth**: Crecimiento mensual de ventas
- **DSO**: Días promedio de cobro
- **DPO**: Días promedio de pago a proveedores
- **Tax Rate**: Tasa de impuestos corporativos
- **CapEx**: Inversión mensual en capital

## 🧪 Tests

Ejecutar tests automatizados:

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_logic.py
pytest tests/test_imports.py

# Con coverage
pytest --cov=src
```

## 🚀 Migración a Producción SaaS

### Base de Datos

**PostgreSQL Migration:**
```python
# Cambiar en src/core/db.py
DATABASE_URL = "postgresql://user:password@host:port/database"
```

**Supabase (recomendado):**
```python
DATABASE_URL = "postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres"
```

### Autenticación

**OAuth/SAML Integration:**
- Reemplazar `streamlit-authenticator` con providers OAuth
- Implementar registro de usuarios
- Configurar multi-tenant security

### Infraestructura

**Deployment Options:**
- **Streamlit Cloud**: Deployment directo desde GitHub
- **Docker**: Containerización para cualquier cloud
- **AWS/GCP/Azure**: Deployment escalable

**Environment Variables:**
```bash
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
STRIPE_API_KEY=sk_live_...  # Para billing
```

### Funcionalidades SaaS

**Billing & Subscriptions:**
- Integrar Stripe para pagos
- Planes: Starter, Professional, Enterprise
- Límites por plan (transacciones, usuarios, etc.)

**Advanced Features:**
- API REST para integraciones
- Webhooks para notificaciones
- Advanced analytics con ML
- Multi-currency automated rates

## 📄 API Documentation

### Endpoints Futuros (Post-MVP)

```python
# Transacciones
GET    /api/v1/transactions
POST   /api/v1/transactions
PUT    /api/v1/transactions/{id}
DELETE /api/v1/transactions/{id}

# Proyecciones
GET    /api/v1/projections
POST   /api/v1/projections/calculate

# Escenarios
GET    /api/v1/scenarios
POST   /api/v1/scenarios
GET    /api/v1/scenarios/{id}/compare

# Reportes
GET    /api/v1/reports/excel
GET    /api/v1/reports/pdf
```

## 🔒 Seguridad

### Implementado
- Hash de contraseñas con bcrypt
- Session state management
- Role-based access control (admin/analyst)
- Multi-tenant data isolation

### Para Producción
- HTTPS obligatorio
- OAuth 2.0 / SAML
- Rate limiting
- Input validation
- SQL injection protection
- Audit logging

## 📈 KPIs y Métricas

### KPIs Calculados
- **Minimum Cash Position**: Posición mínima de efectivo proyectada
- **Months of Runway**: Meses de operación con burn rate actual
- **Average Burn Rate**: Tasa promedio de quema de efectivo
- **DSCR**: Debt Service Coverage Ratio
- **Final Cash Position**: Efectivo al final del período

### Fórmulas Clave
```python
# Months of Runway
runway = current_cash / average_monthly_burn_rate

# DSCR
dscr = operating_cash_flow / total_debt_service

# Working Capital
working_capital = (DSO * monthly_sales / 30) + inventory - (DPO * monthly_cogs / 30)
```

## 🎯 Roadmap

### Fase 1 - MVP ✅
- [x] Autenticación básica
- [x] Importación de transacciones
- [x] Proyecciones de flujo de caja
- [x] Escenarios básicos
- [x] Reportes Excel/PDF

### Fase 2 - SaaS Features 🚧
- [ ] Registro de usuarios
- [ ] Billing con Stripe
- [ ] API REST
- [ ] Multi-tenant completo
- [ ] Advanced analytics

### Fase 3 - Enterprise 📋
- [ ] SSO/SAML
- [ ] Advanced forecasting con ML
- [ ] Integraciones ERP
- [ ] White-label options

## 🤝 Contribución

### Setup Desarrollo
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run code formatting
black src/
flake8 src/

# Run tests
pytest --cov=src
```

### Guidelines
- Seguir PEP 8 para style
- Tests para nuevas funcionalidades
- Documentar funciones complejas
- Type hints obligatorios

## 📞 Soporte

### Issues Comunes

**Error de Base de Datos:**
```bash
# Reinicializar DB
python -m src.core.db --init --seed
```

**Error de Autenticación:**
- Verificar users.yaml existe
- Passwords hasheados correctamente

**Error de Dependencias:**
```bash
pip install --upgrade -r requirements.txt
```

### Contacto
- GitHub Issues para bugs
- Documentation en Wiki
- Email: support@cashflow-analytics.com

## 📜 Licencia

MIT License - ver LICENSE file para detalles.

---

**¡Listo para ejecutar!** 🚀

```bash
# Quick Start
python -m src.core.db --init --seed
streamlit run app.py
```

Abrir http://localhost:8501 y login con admin/admin123