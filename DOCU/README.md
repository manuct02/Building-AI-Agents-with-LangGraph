# Creando Agentes de IA con LangGraph

## 1. Herramientas y APIS Externas

La clave de los agentes reside en su capacidad de actuación interactuando con sistemas reales como servicios de reservas de vuelos, plataformas de mensajería o fuentes de datos financieros. El cambio de paradigma del mero razonamiento a la actuación ocurre a través del uso de **APIs externas**, que sirven de puente entre el razonamiento interno del agente y las acciones en el mundo real.

#### **¿Qué es realmente una API?**

Una API **(Interfaz de Programación de aplicaciones)** es una forma estrcuturada para que diferentes tipos de software se comuniquen e interactúen. Es como hacer un pedido en el restaurante: 

El agente formatea la solicitud (la comanda) $\longrightarrow$ la envía a la API (la cocina) $\longrightarrow$ recibe una respuesta (la comida). La mayoría de las APIs usan HTTP y REST, donde el agente envía una solicitud a una URL y recibe datos estructurados, comúnmente en JSON.

#### **Manejo de la autenticación**

Las APIs requieren credenciales. Para accesos más seguros o específicos de usuario se usa OAuth (dirige a los usuarios para autorizar el acceso, recibir un token y usarlo de forma segura)

### Protocolo de Contexto de Modelo (MCP)

MCP intenta hacer por el **uso de herramientas de IA** lo que hizo USB-C por las conexiones de dispositivos.

MCP proporciona un **conector universal**-un protocolo estándar que hace que el uso de herramientas sea más:
- **Consistente** entre modelos y proveedores
- **Componible** entre herramientas y agentes
- **Monitoreable** y **auditable** para seguridad y gobernanza

#### **Cómo funciona**

En esencia, MCP define una manera para que los modelos:
- 1 - **Expresen llamadas a herramientas** en un formato de mensaje estándar
- 2 - **Reciban resultados de herramientas** también de forma estándar
- 3 - **Transmitan interacciones** para que los agentes peudan manejar flujos de trabajo de múltiples pasos dinámicamente

Separa:

- El **razonamiento** y la **intención** del modelo (Quiero usar la herramienta "X" con los argumentos "Y" y "Z")
- De la **ejecución** real de las herramientas por el sistema (llamadas a AIs, manejo de autenticación, reintentos, registros, etc.,..)

#### **Transporte: SSE queda obsoleto, HTTP con transmisión continua en el futuro**

Las primeras versiones de MCP usaban **Eventos Enviados por el Servidor (SSE)** para las interacciones en streaming.

Por su parte, **HTTP con transmisión continua** es el transporte preferido:
- Más flexible
- Mejor para el contenido multimodal
- Más fácil de adoptar en arquitecturas modernas

MCP se está convirtiendo rápidamente en el estándar para la IA aumentada con herramientas. Donde se puede encontrar:
- **Agentes personalizados**
- **Agentes cross-model**
- **Orquestaión de herramientas empresariales**
- **Sistemas multiagente**

## 2. Interacción con bases de datos

Para acceder a datos internos y privados de cliente se reuiere una interacción precisa al margen de datos públicos o APIs.

#### **· Recuperación Estructurada en Acción**

Si se le pregunta a un agente: <<¿Cuál es el estado del ticket #3042?>> , no puede buscarlo con una búsqueda web. La respuesta se encontrará en una base de datos relacional privada o un CRM. De manera similar, si el agente completa una tarea buscamos que actualice el sistema correspondiente; no sólo confirmar el éxito de la operación, sino escribir una nueva entrada a la base de datos.

#### **· Comprendiendo las bases de datos**

- **Bases de datos relacionales** (PostgreSQL, MySQL) almacenan datos en tablas con esquemas definidos, ideales para interacciones de agentes que requieren consultas estructuradas.
- **Bases de datos NoSQL** (MongoDB) ofrecen flexibilidad, pero se usan menos comúnmente para integración directa con agentes.
- **Base de datos vectoriales** (Chroma, Pinecone) almacenan embeddings para búsqueda semántica, permitiendo la rcuperación basada en similitud, una parte clave de muchos flujos de trabajo de RAG (Generación aumentada por recuperación)

Por ahora, el enfoque está en bases de datos relacionales y SQL.

#### **· text2SQL: Traduciendo Lenguaje a Consultas**
Los agentes pueden traducir lenguaje natural a SQL, una práctica conocida como **text2SQL** . Por ejemplo:

**Entrada:** "¿Cuántos usuarios se registraron esta semana?"

**Salida:** ```SELECT COUNT(*) FROM users WHERE signup_date >= '2025-07-01'```

Esto requiere que el agente:
- Comprenda los esquemas de la base de datos
- Maneje filtros y rangos de fechas
- Evite consultas peligrosas (por ejemplo, un `DELETE` accidental)

Para prevenir errores críticos, los agentes en entornos reales deben estar protegidos con mecanismos de seguridad, incluyendo validación de consultas y aprobaciones humanas.

#### **· Uso de Bases de Datos Vectoriales (Búsqueda Semántica)**

Algunas preguntas no tienen rspuestas exactas en una base de datos. Las bases de datos vectoriales manejan esto comparando embeddings y devolviendo el contenido más relevante semánticamente, no solo coincidencias exactas.

Rag es un patrón, no una herramienta. La recuperación puede usar SQL, búsqueda por palabras clave o ombinaciones de todo. Los agentes (como el que hicimos de hospitality) combinan enfoques: usan SQL para filtrar y búsqueda vectorial para ordenar resultados semánticamente. Este modelo híbrido brinda a los agentes la capacidad de razonar tanto sobre la estructura como sobre el significado de los datos.




