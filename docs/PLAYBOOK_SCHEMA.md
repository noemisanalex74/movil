# Esquema de Playbooks de Automatización (v1.0)

Este documento define la estructura y sintaxis de los archivos de Playbook utilizados por el sistema de automatización de AGP. Los playbooks se escriben en formato **YAML** por su legibilidad.

---

## Estructura General de un Playbook

Un playbook es un archivo YAML que contiene metadatos y una lista de tareas a ejecutar en uno o más agentes remotos.

**Ejemplo de Playbook:**
```yaml
# playbook_ejemplo.yml
name: "Mantenimiento Básico del Servidor"
description: "Este playbook actualiza los paquetes del sistema y limpia archivos temporales."
version: "1.0"

# Define el agente o grupo de agentes de destino
target: "agent-web-prod-01"

# Define variables que pueden ser usadas en las tareas
vars:
  temp_directory: "/tmp"
  package_manager: "apt-get"

# Lista de tareas a ejecutar secuencialmente
tasks:
  - name: "Actualizar lista de paquetes"
    module: command
    args: "{{ package_manager }} update -y"
    register: update_result

  - name: "Instalar actualizaciones de seguridad"
    module: command
    args: "{{ package_manager }} upgrade -y"
    when: "update_result.rc == 0" # Solo se ejecuta si el comando anterior fue exitoso

  - name: "Listar contenido del directorio temporal"
    module: command
    args: "ls -la {{ temp_directory }}"
    register: temp_files

  - name: "Mostrar archivos temporales (solo para debug)"
    module: debug
    args: "Contenido de {{ temp_directory }}:\n{{ temp_files.stdout }}"

  - name: "Limpiar archivos temporales antiguos (más de 7 días)"
    module: command
    args: "find {{ temp_directory }} -type f -mtime +7 -delete"
    when: "update_result.rc == 0"
```

---

## Componentes del Playbook

### 1. Metadatos (Nivel Raíz)

- `name` (string, **obligatorio**): Un nombre descriptivo y único para el playbook.
- `description` (string, opcional): Una explicación más detallada de lo que hace el playbook.
- `version` (string, **obligatorio**): La versión del esquema del playbook que se está utilizando (ej. "1.0").

### 2. `target` (string, **obligatorio**)

Define en qué agente se ejecutarán las tareas.
- **Actualmente:** Acepta el ID de un único agente (ej. `"agent-web-prod-01"`).
- **Futuro:** Podría expandirse para aceptar listas de agentes (`["agent-01", "agent-02"]`) o nombres de grupos (ej. `"grupo:webservers"`).

### 3. `vars` (diccionario, opcional)

Un diccionario de clave-valor que define variables. Estas variables pueden ser referenciadas en las tareas usando la sintaxis de plantillas Jinja2: `{{ nombre_de_la_variable }}`.

### 4. `tasks` (lista, **obligatorio**)

Una lista de diccionarios, donde cada diccionario representa una tarea a ejecutar. Las tareas se ejecutan en el orden en que aparecen en la lista.

#### Atributos de una Tarea

- `name` (string, **obligatorio**): Descripción de lo que hace la tarea. Se usa para los logs y la visualización en el dashboard.
- `module` (string, **obligatorio**): El módulo a ejecutar. Define el tipo de acción a realizar.
    - `command`: Ejecuta un comando de shell en el agente. Los comandos deben estar en la lista blanca del agente.
    - `debug`: Imprime un mensaje en los logs de ejecución del playbook. Es útil para depurar el valor de las variables.
    - *(Futuro: se pueden añadir módulos como `file`, `service`, `template`, `copy` etc.)*
- `args` (string, **obligatorio**): Los argumentos para el módulo.
    - Para `command`: Es el comando completo a ejecutar (ej. `"ls -l /home/user"`).
    - Para `debug`: Es el mensaje a mostrar (ej. `"La variable es {{ mi_variable }}"`).
- `register` (string, opcional): Si se especifica, el resultado completo de la tarea se guardará en una variable con este nombre. El resultado es un diccionario que contiene `stdout` (salida estándar), `stderr` (salida de error), y `rc` (código de retorno).
- `when` (string, opcional): Una expresión condicional. La tarea solo se ejecutará si la expresión se evalúa como verdadera. Se pueden usar las variables registradas en tareas anteriores (ej. `when: "update_result.rc == 0"`).
`)