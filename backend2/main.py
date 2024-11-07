import blnstats


# blnstats.set_up_database()
# blnstats.testFunctionality()

# app = blnstats.create_app()
# app.run(host='0.0.0.0', port=8000)




if __name__ == "__main__":
    # Working modules:


    # General Statistics
    blnstats.generateGeneralStatisticsCharts()

    # Coefficients
    # blnstats.generateCoefficientCharts() # Veikia 2024-11-04
    # blnstats.generateCoefficientsOnSingleChart() # Veikia 2024-11-04
    # blnstats.generateOverlappingCoefficientCharts() # Veikia 2024-11-04

    # CSV
    # blnstats.generateCSV_EntityMetrics() # Veikia 2024-11-04
    
    # Lorenz
    # blnstats.generateLorenzCharts() # Veikia 2024-11-04
    # blnstats.generateExampleLorenzCharts() # Veikia 2024-11-04
    


    # Testing:
    # blnstats.generateRainbowChart() # Neveikia - daryta per Tableau





# if __name__ == "__main__":
#     blnstats.test_entity_functionality()
#     pass