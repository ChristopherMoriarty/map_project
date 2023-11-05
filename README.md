# map_project

## Docker way to start

Use a specific command for your OS:

1. Windows

    ```bash
    docker run -v %cd%/map:/map -v %cd%/tiles:/tiles -p 8080:8080 1oker/mapproject
    ```

2. MacOS or Linux
   
   ```bash
    docker run -v $PWD/map:/map -v $PWD/tiles:/tiles -p 8080:8080 1oker/mapproject
    ```

## Standart way to start

To install the project dependencies, follow these steps:

1. Use Python version 3.8.10 to create a virtual environment:

    ```bash
    python3.8.10 -m venv venv
    ```

2. Activate a virtual enviroment:
   
   ```bash
    venv\Scripts\activate
    ```

3. Install the dependencies from the `requirements.txt` file using pip:

    ```bash
    pip install -r requirements.txt
    ```
    
4. Run script:

    ```bash
    python main.py run
    ```
