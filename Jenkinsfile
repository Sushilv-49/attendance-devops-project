pipeline {
    agent any

    stages {

        stage('Clone Repository') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                bat 'python -m pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                bat 'python -m pytest'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat 'docker build -t attendance-app .'
            }
        }

        stage('Deploy Container') {
            steps {
                bat 'docker rm -f attendance-container || exit /b 0'
                bat 'docker run -d -p 5000:5000 -v attendance-data:/data --name attendance-container attendance-app'
            }
        }
    }
}