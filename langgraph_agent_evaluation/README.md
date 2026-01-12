# Evaluación del RAG Pipeline con RAGAS y MLflow

Vamos a demostrar cómo evaluar el pipeline de un RAG usando **RAGAS** para la evaluación y **MLflow** para el tracking

## 1. Multiple Model Setup

Se inicializan tres modelos:
- `llm`: un modelo de OpenAI usado para generar respuestas.
- `llm_judge`: un modelo más poderoso para evaluar respuestas generadas.
- `embedding`

## 2. MLflow Experiment Configuration
- Se crea un MLflow experiment y se empieza a runnear con un nombre personalizado.
- También hay metadatos:
```python
mlflow.set_experiment("udacity")
with mlflow.start_run(run_name="L4_exercise_02") as run:
  mlflow_run_id = run.info.run_id
  mlflow.log_params({
      "llm_model": llm.model_name,
      "llm_judge_model": llm_judge.model_name,
      "embedding_model": embedding.model
  })
```

## 3. Proceso de los documentos

- Se reusa el PDF para volver a cargarlo
-