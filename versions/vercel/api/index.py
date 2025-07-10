"""
Vercel serverless function entry point for the Purchase Order Consolidator
"""
import sys
import os

# Add the parent directory to the Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel expects a function named 'handler' or the app itself
def handler(request):
    return app(request.environ, lambda *args: None)

# For Vercel, we can also export the app directly
# Vercel will handle the WSGI interface
if __name__ == "__main__":
    app.run(debug=False)