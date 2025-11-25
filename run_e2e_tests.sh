#!/bin/bash

# E2E Test Runner Script
# This script provides convenient commands for running E2E tests

echo "Library Management System - E2E Test Runner"
echo ""

show_menu() {
    echo "Select a test mode:"
    echo "1) Run all E2E tests (headless)"
    echo "2) Run all E2E tests (visible browser)"
    echo "3) Run all E2E tests in slow motion"
    echo "4) Exit"
    echo ""
}

while true; do
    show_menu
    read -p "Enter your choice [1-4]: " choice
    echo ""
    
    case $choice in
        1)
            echo "Running E2E tests in headless mode..."
            pytest tests/test_e2e.py -v
            ;;
        2)
            echo "Running E2E tests with visible browser..."
            pytest tests/test_e2e.py -v --headed
            ;;
        3)
            echo "Running E2E tests in slow motion (1 second delay)..."
            pytest tests/test_e2e.py -v --headed --slowmo 1000
            ;;
        4)
            exit 0
            ;;
        *)
            echo "Invalid choice. Please select 1-4."
            ;;
    esac
    
    echo ""
done
