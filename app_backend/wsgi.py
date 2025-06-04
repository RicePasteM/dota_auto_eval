from waitress import serve
from app import create_app

if __name__ == '__main__':
    # Create app with the same configuration
    app = create_app(host='0.0.0.0', port=5000)
    print("Starting Waitress server...")
    print("The application will be available at:")
    print("- Frontend: http://localhost:5000")
    print("- API: http://localhost:5000/api")
    
    serve(
        app, 
        host='0.0.0.0', 
        port=5000,
        threads=4,              # Number of threads for handling requests
        connection_limit=100,   # Maximum number of concurrent connections
        cleanup_interval=30,    # Clean up unused connections every 30 seconds
        channel_timeout=30      # Connection timeout in seconds
    )