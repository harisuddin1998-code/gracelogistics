import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///vehicle_management.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'xlsx', 'xls'}
    
    # App settings
    APP_NAME = "IntelliFleet"
    APP_NAME_SHORT = "IFL"
    COMPANY_SLOGAN = ""
    PORT = int(os.environ.get('FLASK_PORT', 5001))
    
    # Theme colors
    THEME_PRIMARY = "#6C8196"
    THEME_SECONDARY = "#5C5C5C"
    THEME_DARK = "#21201B"
    THEME_LIGHT = "#FDFDE4"
    
    # Alert thresholds
    FUEL_EFFICIENCY_THRESHOLD = 8
    STOCK_REORDER_DAYS = 7
    PERMIT_RENEWAL_DAYS = 15
    MAINTENANCE_DUE_DAYS = 7
    
    # Pagination
    ITEMS_PER_PAGE = 10