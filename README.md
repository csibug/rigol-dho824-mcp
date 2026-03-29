# Rigol DHO824 MCP Server v2

Custom Model Context Protocol (MCP) server for Rigol DHO800 series oscilloscopes.  
This project is a refined, modular evolution (v2) of the original MCP server, specifically optimized for **Sony TC-FX44** cassette deck restoration and precision audio signal analysis.

## Key Features (v2)

* **Modular Architecture:** Separated logic for triggers, acquisition, measurement, and waveform processing.
* **Audio Diagnostics Ready:** Built-in tools for Dolby level calibration (AC_RMS) and motor speed verification (7-digit counter).
* **Clean Data Management:** All generated assets (screenshots, CSVs, raw binaries) are routed to a central `data/` directory for easy cleanup.
* **Hardware Validated:** Includes a comprehensive 9-point integration test suite to ensure reliable communication.

## Hardware Support

* **Primary Device:** Rigol DHO824 (also supports DHO804/814).
* **Connectivity:** LAN (LXI/TCP-IP) via PyVISA.
* **Firmware:** Tested on version 00.01.04.

## Installation & Setup

1.  **Clone & Clean:** This version is designed for a clean local environment. Ensure you have Python 3.10+ and a virtual environment.
    ```bash
    pip install -e .
    ```

2.  **Environment Configuration:**
    Create a `.env` file in the root directory:
    ```env
    RIGOL_RESOURCE="TCPIP0::192.168.1.100::inst0::INSTR"
    VISA_TIMEOUT=30000
    ```

3.  **Directory Structure:**
    The server automatically manages the following:
    * `data/screenshots/`: Manual and automated screen captures.
    * `data/waveforms/`: Raw data transfers and metadata (JSON).

## Usage

### Starting the Server
Run the modular server directly:
```bash
python src/rigol_dho824_mcp/server2.py
```

## Integrated Tools
Once connected via an MCP client (like Claude or Cursor), you can use high-level commands:
* "Capture a screenshot of the current waveform"
* "Check the frequency on Channel 1 using the High-Res counter" (Ideal for 3000Hz speed test)
* "Measure AC RMS voltage on Channel 1" (Ideal for Dolby level adjustment)

## Development & Testing
Validate the hardware connection before starting critical measurements:
```Bash
pytest tests/
```

## Acknowledgments
This project is a modularized and enhanced version (v2) based on the original [rigol-dho824-mcp](https://github.com/aimoda/rigol-dho824-mcp) by **ai.moda**.