"""MiniLMS Production WSGI Server Runner
Runs the application using Waitress (high-performance pure-Python WSGI server for Windows/cross-platform)
with configured thread pool, keep-alive, and connection limits.

Linux / Production Container Note:
In Linux or containerized environments, invoke Gunicorn directly:
    gunicorn --workers=4 --threads=2 --bind=0.0.0.0:5000 --access-logfile=- --error-logfile=- wsgi:application
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
load_dotenv()

from wsgi import application

def configure_production_logging():
    """Sets up formatted stdout/file logging for production observability."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] [PID %(process)d] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger('minilms.production')

def run_server(host='0.0.0.0', port=5000, threads=8):
    """Starts the Waitress WSGI server with production settings."""
    logger = configure_production_logging()
    
    logger.info("=========================================================")
    logger.info(" MiniLMS Production WSGI Server (Waitress Engine)")
    logger.info("=========================================================")
    logger.info(f" Host Binding:      http://{host}:{port}")
    logger.info(f" Worker Threads:    {threads}")
    logger.info(f" Target Database:   {os.getenv('DB_NAME', 'minilms_db')}")
    logger.info(f" Process ID:        {os.getpid()}")
    logger.info(f" Environment:       PRODUCTION (DEBUG=False)")
    logger.info(" Health Endpoint:   http://%s:%s/health", '127.0.0.1' if host == '0.0.0.0' else host, port)
    logger.info("=========================================================")

    try:
        from waitress import serve
        serve(
            application,
            host=host,
            port=port,
            threads=threads,
            connection_limit=100,
            channel_timeout=30,
            ident="MiniLMS-Waitress/3.0"
        )
    except ImportError:
        logger.error("Waitress is not installed. Please run: pip install waitress")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\nGracefully shutting down MiniLMS WSGI server.")
        sys.exit(0)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    threads = int(os.getenv('WSGI_THREADS', 8))
    run_server(host=host, port=port, threads=threads)
