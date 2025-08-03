import blnstats
import sys



if __name__ == "__main__":

    if(len(sys.argv) == 1):
        print("Usage: python main.py <command>")
        print("")
        print("Commands:")
        print("  --init-db                      Initialize the database")
        print("  --calculate-ln-stats           Calculate Lightning Network statistics")
        print("  --synchronize-blockchain       Synchronize the blockchain")
        print("  --serve-api                    Serve the backend API")
        print("")
        print("Example: python main.py --init-db")
        print("")
        print("")




    elif(sys.argv[1] == "--init-db"):
        blnstats.set_up_database()




    elif(sys.argv[1] == "--calculate-ln-stats"):

        # CalculateNode Metrics
        blnstats.transformNodeMetrics()

        # General Statistics
        blnstats.generateGeneralStatisticsCharts()
        blnstats.compare_data_sources()

        # Coefficients
        blnstats.generateCoefficientCharts(subjectsOfAnalysis=["Nodes"])
        blnstats.generateCoefficientCharts(subjectsOfAnalysis=["Entities"])
        blnstats.generateCoefficientsOnSingleChart()
        blnstats.generateOverlappingCoefficientCharts()

        # CSV
        blnstats.generateCSV_EntityMetrics(dateMasks=['2025-03-01', '20XX-XX-01'])
        
        # Lorenz
        blnstats.generateLorenzCharts()
        blnstats.generateExampleLorenzCharts()

        



    elif(sys.argv[1] == "--sync-blockchain"):
        blnstats.synchronizeBlockchain()




    elif(sys.argv[1] == "--import-lnd-dbreader-data"):
        if(len(sys.argv) == 3):
            blnstats.importLNDDBReader(sys.argv[2])
        else:
            print("Error: Invalid number of arguments")
            print()
            print("Usage: python3 main.py --import-lnd-dbreader-data <file_path>")
            print()
            print("Examples:")
            print("    python3 main.py --import-lnd-dbreader-data http://192.168.1.2/rawdata/lnd-dbreader.json.gz")
            print("    python3 main.py --import-lnd-dbreader-data /DATA/INPUT/lnd-dbreader-20250101-123456.json.gz")
            print("")


    elif(sys.argv[1] == "--serve-api"):
        app = blnstats.create_app()
        app.run(host='0.0.0.0', port=8000, debug=True)


    elif(sys.argv[1] == "--import-ln-research-data"):
        from blnstats.data_import.ln_research import LNResearchData
        LNResearchData()