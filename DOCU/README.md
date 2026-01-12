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

## 3. **RAG** Generación Aumentada por recuperación agéntica

Siguen un patrón simple: reciben una consulta, recuperan algunos documentos y generan una respuesta.

Esto funciona para preguntas sencillas, pero resulta insuficiente en escenarios más complejos. El RAG agéntico mejora esto al dotar a los agentes con la capacidad de reflexionar, reintentar y refinar, transformando la recuperación de una herramienta estática en una parte activa del ciclo de razonamiento del agente.

#### **Recuperación**

El Rag de tooooda la via recupera y sigue con su vida, el agéntico en cambio valora la calidad de lo que recupera:

 - El agente evalúa si los documentos son relevantes.
 - Identifica información faltante
 - Reformula las consultas si es necesario
 - Repite la recuperación y ajusta las estrategias antes de responder

#### **Estudio de Caso: Fallo de ZIllow Offers**

Un RAG simple podría resumir que el algoritmo de vivienda de *Zillow* falló debido a mercados impredecibles. Sin embargo, un RAG agéntico:

- Detectaría vacíos en la recuperación inicial
- Reflexionaría sobre lo que falta (por ejemplo, supuestos algoritmos, bucles de retroalimentación)
- Reformularía la consulta para enfocarse en fallas técnicas y estrategia de negocio 
- Recuperaría mejores datos y produciría una explicación en capas

#### **Planificación y Flujos de Trabajo Flexibles**

Los agentes RAG agénticos planifican:
- Cuándo recuperar
- Qué recuperar (definiciones, contexto, evidencias)
- Cómo integrar el contexto recuperado a través de múltiples pasos

Los agentes también deben ser capaces de inspeccionar sus resultados:
- ¿Coinciden con las palabras clave de la consulta?
- ¿Responden directamente al "qué" o "por qué"¿
- ¿Puede cada afirmación respaldarse con una fuente específica?

Los frmaworks pueden incluir métricas como **fidelidad** y **relevancia**. De hecho el que hice yo los tenía

## 4. Human-in-the-loop y Observabilidad

La **transparencia y el control** son esenciales . 
- La **observabilidad** ayuda a **monitorear**, **interpretar** y **optimizar**.
- El **Human in the loop (HTL)** asegura la **supervisión** y **corrección de errores** en escenarios críticos.

#### **Visibilidad inicial**

- **El debugging básico empieza printeando los outputs**, permitiendo:
  - Observar las respuestas del agente a diferentes outputs.
  - Identificar errores o inconsistencias.
  - Iterar y refinar la lógica.
  - Es útil para los **early-stage development**.

#### **Introduciendo el Human-in-the-loop**

Los mecanismos de HITL permiten a los humanos:
- **Interrumpir y aprobar una acción** antes de la ejecución.
- **Validar outputs** para prevenir errores.
- **Modificar el estado del agente** en tiempo real para corregir malinterpretaciones.

**Revisar los checkpoints**.

#### **Observabilidad avanzada para Producción de Sistemas**

Para deployments a larga escala, la **observabilidad refinada** asegura que los agentes resulten **eficientes y confiables**

La observabilidad se basa en tres técnicas:
 - 1 - **Métricas**: monitorear los **indicadores de performance** como tiempo de respuesta, precisión y uso de tokens.
 - 2 - **Logs**: capturar los **records detallados** de acciones del agente, errores e interacciones.
 - 3 - **Tracing**: trackea la **secuencia de acciones** tomadas por el agente.

 ## 5. Fiabilidad y Evaluación del Agente

Hacer agentes es fácil, el reto viene a la hora de hacerlos predecibles, consistentes y fiables.

#### **Definir el éxito con métricas**

Los agentes necesitan criterios de éxito medibles:
- **Accuracy**: son las respuestas **correctas y relevantes**? Cada cuánto ocurren errores?
- **Efficiency**: completa el agente tareas **rápidamente y con el mínimo uso de resource**?
- **Optimización de coste**: está la performance optimizada sin usar **excesivas llamadas a la API**, **tokens** o **coste computacional**?

#### **Evaluación vs Testing**
- El **Testing** identifica **defectos y errores funcionales**.
- La **Evaluation** se encarga del chequeo de la **calidad general**, determinando cómo de bien el agente actúa su tarea.

#### **Observabilidad: Monitorear Agentes en producción**

La fiabilidad requiere **ongoing monitoring** para detectar fallos y mejorar la performance.

Las técnicas clave de la observabilidad incluyen:

- **Tracking KPIs**: medir constantemente la **accuracy**, **efficiency** y **ratios de error**.
- **Logging y Tracing**: guardar **fallos y éxitos** para refinar los workflows.
- **Transparencia de decisión**: monitorear cómo el agente hace las elecciones y elige acciones.

