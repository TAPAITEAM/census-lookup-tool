#!/bin/bash
# Mac/Linux shell script to start the Census Demographics Lookup tool

echo "================================================"
echo "Census Demographics Lookup Tool"
echo "================================================"
echo ""

# Change to the script's directory
cd "$(dirname "$0")"

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Error: streamlit is not installed"
    echo ""
    echo "Installing required packages..."
    echo ""
    
    # Try to install requirements
    if [ -f "census_requirements.txt" ]; then
        pip install -r census_requirements.txt
        if [ $? -ne 0 ]; then
            echo ""
            echo "❌ Installation failed. Please run manually:"
            echo "   pip install -r census_requirements.txt"
            echo ""
            read -p "Press Enter to exit..."
            exit 1
        fi
    else
        pip install streamlit
        if [ $? -ne 0 ]; then
            echo ""
            echo "❌ Installation failed. Please run manually:"
            echo "   pip install streamlit"
            echo ""
            read -p "Press Enter to exit..."
            exit 1
        fi
    fi
    echo ""
    echo "✅ Installation complete!"
    echo ""
fi

echo "Starting the application..."
echo "The app will open in your web browser automatically."
echo ""
echo "To stop the application, press Ctrl+C in this window."
echo "================================================"
echo ""

streamlit run main_app.py
