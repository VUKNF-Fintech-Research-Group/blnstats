from prefect import flow, task, serve
import blnstats


# Lightning Network Statistics Tasks
@task
def transform_node_metrics():
    """Transform node metrics."""
    print("Transforming node metrics...")
    blnstats.transformNodeMetrics()
    print("Node metrics transformation completed.")
    return "Node metrics transformed"


@task
def generate_general_statistics_charts():
    """Generate general statistics charts."""
    print("Generating general statistics charts...")
    blnstats.generateGeneralStatisticsCharts()
    print("General statistics charts generated.")
    return "General statistics charts generated"


@task
def compare_data_sources():
    """Compare data sources."""
    print("Comparing data sources...")
    blnstats.compare_data_sources()
    print("Data sources comparison completed.")
    return "Data sources compared"


@task
def generate_coefficient_charts(subjects_of_analysis):
    """Generate coefficient charts for specified subjects."""
    print(f"Generating coefficient charts for: {subjects_of_analysis}")
    blnstats.generateCoefficientCharts(subjectsOfAnalysis=subjects_of_analysis)
    print(f"Coefficient charts for {subjects_of_analysis} generated.")
    return f"Coefficient charts generated for {subjects_of_analysis}"


@task
def generate_coefficients_on_single_chart():
    """Generate coefficients on single chart."""
    print("Generating coefficients on single chart...")
    blnstats.generateCoefficientsOnSingleChart()
    print("Single chart coefficients generated.")
    return "Single chart coefficients generated"


@task
def generate_overlapping_coefficient_charts():
    """Generate overlapping coefficient charts."""
    print("Generating overlapping coefficient charts...")
    blnstats.generateOverlappingCoefficientCharts()
    print("Overlapping coefficient charts generated.")
    return "Overlapping coefficient charts generated"


@task
def generate_csv_entity_metrics(date_masks):
    """Generate CSV entity metrics."""
    print(f"Generating CSV entity metrics for date masks: {date_masks}")
    blnstats.generateCSV_EntityMetrics(dateMasks=date_masks)
    print("CSV entity metrics generated.")
    return f"CSV entity metrics generated for {date_masks}"


@task
def generate_lorenz_charts():
    """Generate Lorenz charts."""
    print("Generating Lorenz charts...")
    blnstats.generateLorenzCharts()
    print("Lorenz charts generated.")
    return "Lorenz charts generated"


@task
def generate_example_lorenz_charts():
    """Generate example Lorenz charts."""
    print("Generating example Lorenz charts...")
    blnstats.generateExampleLorenzCharts()
    print("Example Lorenz charts generated.")
    return "Example Lorenz charts generated"


# Blockchain Tasks
@task
def synchronize_blockchain():
    """Synchronize the blockchain."""
    print("Synchronizing blockchain...")
    blnstats.synchronizeBlockchain()
    print("Blockchain synchronization completed.")
    return "Blockchain synchronized"


# Data Import Tasks
@task
def import_lnd_dbreader_data(file_path):
    """Import LND DBReader data."""
    print(f"Importing LND DBReader data from: {file_path}")
    blnstats.importLNDDBReader(file_path)
    print("LND DBReader data import completed.")
    return f"LND DBReader data imported from {file_path}"


@task
def import_ln_research_data():
    """Import LNResearch data."""
    print("Importing LNResearch data...")
    blnstats.importLNResearchData()
    print("LNResearch data import completed.")
    return "LNResearch data imported"








############################################################################
################################## WORKFLOWS ###############################
############################################################################






########################## DATA IMPORT WORKFLOWS ###########################
@flow
def lnd_dbreader_import_flow(file_path: str):
    """Flow to import LND DBReader data."""
    return import_lnd_dbreader_data(file_path)


@flow
def ln_research_import_flow():
    """Flow to import LNResearch data."""
    return import_ln_research_data()
############################################################################







########################## BLN ANALYSIS WORKFLOW ###########################
@flow
def lightning_network_statistics_flow():
    """Complete Lightning Network statistics calculation flow."""

    # Sync blockchain
    sync_result = synchronize_blockchain()

    # Transform node metrics
    node_metrics_result = transform_node_metrics()
    
    # Generate general statistics
    general_stats_result = generate_general_statistics_charts()
    data_sources_result = compare_data_sources()
    
    # Generate coefficient charts
    nodes_coefficients = generate_coefficient_charts(["Nodes"])
    entities_coefficients = generate_coefficient_charts(["Entities"])
    single_chart_coefficients = generate_coefficients_on_single_chart()
    overlapping_coefficients = generate_overlapping_coefficient_charts()
    
    # Generate CSV files
    csv_result = generate_csv_entity_metrics(['2025-03-01', '20XX-XX-01'])
    
    # Generate Lorenz charts
    lorenz_result = generate_lorenz_charts()
    example_lorenz_result = generate_example_lorenz_charts()
    
    return {
        "sync_blockchain": sync_result,
        "node_metrics": node_metrics_result,
        "general_stats": general_stats_result,
        "data_sources": data_sources_result,
        "nodes_coefficients": nodes_coefficients,
        "entities_coefficients": entities_coefficients,
        "single_chart_coefficients": single_chart_coefficients,
        "overlapping_coefficients": overlapping_coefficients,
        "csv_export": csv_result,
        "lorenz_charts": lorenz_result,
        "example_lorenz": example_lorenz_result
    }
############################################################################






######################### FULL INITIALIZATION FLOW #########################
@flow
def full_initialization_flow():
    """Complete data pipeline: import -> calculate -> sync."""

    # Import LNResearch data
    ln_research_import_result = import_ln_research_data()

    # Import LND DBReader from Vilnius university Kaunas faculty data
    lnd_dbreader_import_result = import_lnd_dbreader_data("https://blnstats.knf.vu.lt/rawdata/INPUT/lnd-dbreader-A336EEAB--latest.json.gz")

    # Run LN statistics calculations
    stats_results = lightning_network_statistics_flow()
    
    return {
        "ln_research_import": ln_research_import_result,
        "lnd_dbreader_import": lnd_dbreader_import_result,
        "statistics": stats_results
    }
############################################################################




if __name__ == "__main__":
    # Create deployments for all flows
    ln_stats_deployment = lightning_network_statistics_flow.to_deployment(name="BLN Analysis Flow")
    lnd_import_deployment = lnd_dbreader_import_flow.to_deployment(name="LND DBReader Import Flow")
    full_pipeline_deployment = full_initialization_flow.to_deployment(name="Full Initialization Flow")

    # Serve all deployments
    serve(
        ln_stats_deployment,
        lnd_import_deployment,
        full_pipeline_deployment
    )

