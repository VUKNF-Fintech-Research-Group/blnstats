# Bitcoin LN Statistics

A comprehensive analytics platform for Bitcoin Lightning Network (BLN) statistics, providing detailed insights into network topology, node/entity centralization metrics and trends.

![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🎯 Overview

BLN Statistics is a multi-service application that collects, processes, and visualizes Bitcoin Lightning Network data. It provides advanced statistical analysis including centralization coefficients, Lorenz curves, network topology metrics, and comparative data source analysis.


<img width="1139" height="910" alt="Screenshot 2025-08-04 at 14 24 21" src="https://github.com/user-attachments/assets/fbac735e-cf40-4ab8-aafd-0385410df58b" />



### Key Features

- **Network Analysis**: Comprehensive Lightning Network topology analysis
- **Centralization Metrics**: Gini coefficients, HHI, Theil index, Shannon entropy, and Nakamoto coefficients
- **Lorenz Curves**: Wealth distribution analysis across nodes and entities
- **Multi-source Data**: Integration with LNResearch and LND DBReader data sources
- **Real-time Visualization**: Charts and dashboards
- **Workflow Orchestration**: Automated data processing with Prefect
- **Historical Analysis**: Time-series analysis of network evolution

## 🏗️ Architecture

### Services

The application consists of several Docker containers orchestrated via Docker Compose:

| Service | Technology | Purpose |
|---------|------------|---------|
| **NextJS** | Next.js + Material-UI | Web interface and data visualization |
| **Backend** | Python Flask | REST API and data processing |
| **Database** | MySQL | Lightning Network data storage |
| **Workflow Engine** | Prefect | Data pipeline orchestration |
| **Reverse Proxy** | Caddy | HTTP endpoint unification |
| **Database Browser** | DBGate | Database administration |
| **File Browser** | FileBrowser | Raw data file management |


## 🔧 Installation

### System Requirements
- **RAM**: 8GB+
- **Storage**: 40GB+
- **CPU**: 4+ cores



### Prerequisites
* Ubuntu 22.04+ OS version
* Ready to use Docker and docker-compose CLI tools


### Setup

Clone BLN Stats repository:
```bash
git clone https://github.com/VUKNF-Fintech-Research-Group/blnstats.git
cd blnstats
```

Run provided docker compose sample configuration file and start the system:
```bash
cp docker-compose.yml.sample docker-compose.yml
./runUpdateThisStack.sh
```

After docker finishes starting services open your server IP address using WEB browser:
```
http://<ubuntu-server-ip-address-here>:80
```

## 🔗 External Dependencies

- **LNResearch**: Lightning Network research data
- **Electrum Server**: Using electrum.blockstream.info server by default
- **LND DBReader**: Lightning Network daemon database reader (Optional)

## 🙏 Acknowledgments

- [Lightning Network Research Community](https://github.com/lnresearch) - For historical BLN data
- [Lightning Network Community](https://lightning.network/) - For the amazing Lightning Network ecosystem
