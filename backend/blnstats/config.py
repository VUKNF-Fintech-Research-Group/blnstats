import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""
    # Secret key for session management
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    
    # Bitcoin RPC settings
    BITCOIN_RPC_USER = os.getenv('BITCOIN_RPC_USER', '')
    BITCOIN_RPC_PASSWORD = os.getenv('BITCOIN_RPC_PASSWORD', '')
    BITCOIN_RPC_HOST = os.getenv('BITCOIN_RPC_HOST', '')
    BITCOIN_RPC_PORT = int(os.getenv('BITCOIN_RPC_PORT', 8332))

    # Electrum server settings
    ELECTRUM_SERVER_HOST = os.getenv('ELECTRUM_SERVER_HOST', '')
    ELECTRUM_SERVER_PORT = int(os.getenv('ELECTRUM_SERVER_PORT', 50001))

    # Lightning Network research settings
    LN_RESEARCH_TIMEFRAME = os.getenv('LN_RESEARCH_TIMEFRAME', '20230924')

    # Chart generation settings
    CHART_DPI = int(os.getenv('CHART_DPI', 1000))
    CHART_DATE_CUTOFF = os.getenv('CHART_DATE_CUTOFF', '2023-09-24')

    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')

    # Cache settings
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', 300))

    # Other settings
    TOP_ENTITIES_COUNT = int(os.getenv('TOP_ENTITIES_COUNT', 50))
    DAY_OF_YEAR_FOR_CHARTS = os.getenv('DAY_OF_YEAR_FOR_CHARTS', '-06-01')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    DATABASE_NAME = 'test_' + Config.DATABASE_NAME


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False

    # Override these settings in production
    SECRET_KEY = os.getenv('SECRET_KEY')  # Must be set in production
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'production_LnStats.db')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'ERROR')


# Dictionary to easily select the configuration
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    Retrieve the appropriate configuration based on the FLASK_ENV environment variable.
    """
    flask_env = os.getenv('FLASK_ENV', 'default')
    return config.get(flask_env, config['default'])



# Usage example:
# current_config = get_config()
# secret_key = current_config.SECRET_KEY